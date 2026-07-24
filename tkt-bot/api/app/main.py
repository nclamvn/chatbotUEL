import asyncio
import base64
import html
import json
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from pydantic import BaseModel

from . import log, telemetry
from .config import (APP_VERSION, ADMIN_PASS, ADMIN_USER, CORS_ORIGINS,
                     MAX_QUESTION_LEN, MODE, OPENAI_API_KEY,
                     ANTHROPIC_API_KEY)
from .db import connect
from .models import Answer, ChatRequest
from .pipeline import answer_pipeline
from .ratelimit import limiter

log.configure()

MSG_429 = "Bạn gửi hơi nhanh, chờ một chút rồi hỏi lại giúp mình nhé."
MSG_422 = (f"Câu hỏi hơi dài. Bạn rút gọn còn dưới {MAX_QUESTION_LEN} ký tự, "
           "hỏi thẳng vào một ý để mình trả lời chính xác hơn nhé.")

app = FastAPI(title="TKT-BOT API", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def client_ip(request: Request) -> str:
    """Sau Caddy, IP thật nằm ở X-Forwarded-For (hop đầu)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def guard(request: Request) -> str:
    """Cổng chung cho endpoint chat: sinh request_id, ghi log request, áp
    rate limit. Trả rid để endpoint set lại trong context của mình (dependency
    sync chạy ở threadpool context riêng, không tự propagate xuống pipeline)."""
    rid = request.headers.get("x-request-id") or log.new_request_id()
    log.set_request_id(rid)
    ip = client_ip(request)
    log.event("api", "request", path=request.url.path, ip=ip)
    if not limiter.check(ip):
        try:
            telemetry.incr_counter("rate_limited")
        except Exception:  # bộ đếm hỏng không được che mất phản hồi 429
            pass
        log.event("api", "rate_limited", ip=ip)
        raise HTTPException(status_code=429, detail=MSG_429)
    return rid


def enforce_length(message: str) -> None:
    if len(message) > MAX_QUESTION_LEN:
        raise HTTPException(status_code=422, detail=MSG_422)


@app.get("/health")
def health():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM claims")
        n = cur.fetchone()["n"]
        cur.execute("SELECT value FROM meta WHERE key = 'registry_version'")
        row = cur.fetchone()
    return {
        "status": "ok",
        "version": APP_VERSION,
        "mode": MODE,  # TIP-13: template = fallback, không phải LLM
        "providers": {
            "primary": "openai" if OPENAI_API_KEY and MODE != "template" else None,
            "fallback": "anthropic" if ANTHROPIC_API_KEY and MODE != "template" else None,
        },
        "claims_loaded": n,
        "registry_version": row["value"] if row else None,
    }


@app.post("/chat")
def chat(req: ChatRequest, rid: str = Depends(guard)) -> Answer:
    log.set_request_id(rid)  # context của endpoint sync, để pipeline log cùng rid
    enforce_length(req.message)
    answer, _meta = answer_pipeline(req.message, use_llm=req.response_mode == "api")
    telemetry.log_event(req.session_id, req.message, answer["status"],
                        answer["citations"])
    return Answer(**answer)


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    question: str
    thumbs: str  # "up" | "down"
    comment: str | None = None  # TIP-13: ô góp ý một dòng tùy chọn


@app.post("/telemetry")
def feedback(req: FeedbackRequest):
    comment = (req.comment or "").strip()[:500] or None
    telemetry.log_event(req.session_id, req.question, "feedback", [],
                        req.thumbs, comment=comment)
    return {"ok": True}


@app.get("/telemetry/nulls")
def telemetry_nulls():
    return {"backlog": telemetry.null_backlog()}


@app.get("/telemetry/stats")
def telemetry_stats():
    return {"composer_calls": telemetry.get_counter("composer_calls"),
            "cache_hits": telemetry.get_counter("cache_hits"),
            "rate_limited": telemetry.get_counter("rate_limited"),
            "llm_calls_composer": telemetry.get_counter("llm_calls_composer"),
            "llm_calls_composer_openai": telemetry.get_counter("llm_calls_composer_openai"),
            "llm_calls_composer_anthropic": telemetry.get_counter("llm_calls_composer_anthropic"),
            "llm_fallback_openai_to_anthropic":
                telemetry.get_counter("llm_fallback_openai_to_anthropic"),
            "llm_tokens_in_composer": telemetry.get_counter("llm_tokens_in_composer"),
            "llm_tokens_out_composer": telemetry.get_counter("llm_tokens_out_composer"),
            "llm_calls_router": telemetry.get_counter("llm_calls_router"),
            "llm_tokens_in_router": telemetry.get_counter("llm_tokens_in_router"),
            "llm_tokens_out_router": telemetry.get_counter("llm_tokens_out_router")}


def _check_admin(authorization: str | None) -> bool:
    if not ADMIN_USER or not ADMIN_PASS:
        return False  # chưa cấu hình admin thì khóa mặc định
    if not authorization or not authorization.startswith("Basic "):
        return False
    try:
        user, _, pw = base64.b64decode(authorization[6:]).decode().partition(":")
    except Exception:
        return False
    return (secrets.compare_digest(user, ADMIN_USER)
            and secrets.compare_digest(pw, ADMIN_PASS))


@app.get("/admin", response_class=HTMLResponse)
def admin(authorization: str | None = Header(default=None)):
    """Trang admin tối giản (TIP-13): null backlog + counters, basic auth riêng."""
    if not _check_admin(authorization):
        return Response(status_code=401,
                        headers={"WWW-Authenticate": 'Basic realm="tkt-admin"'})
    nulls = telemetry.null_backlog(limit=30)
    counters = {k: telemetry.get_counter(k) for k in
                ("composer_calls", "cache_hits", "rate_limited",
                 "llm_calls_composer", "llm_calls_router")}
    stat_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in counters.items())
    null_rows = "".join(
        f"<tr><td>{n['count']}</td><td>{n['sessions']}</td>"
        f"<td>{html.escape(n['sample_question'] or '')}</td></tr>" for n in nulls)
    return HTMLResponse(f"""<!doctype html><meta name="robots" content="noindex">
<title>TKT admin</title><style>body{{font-family:system-ui;margin:24px;color:#14202a}}
table{{border-collapse:collapse;margin:10px 0;font-size:14px}}
td,th{{border:1px solid #cdd8e1;padding:6px 10px;text-align:left}}h2{{font-size:15px}}</style>
<h1>TKT-BOT admin · mode={MODE}</h1>
<h2>Counters</h2><table><tr><th>key</th><th>value</th></tr>{stat_rows}</table>
<h2>Null backlog (câu chưa trả được)</h2>
<table><tr><th>count</th><th>sessions</th><th>câu hỏi</th></tr>{null_rows}</table>""")


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, rid: str = Depends(guard)):
    """SSE. Verifier duyệt xong toàn bộ câu trả lời rồi mới stream (REQ-06:
    style gate chạy trước khi render), nên stream ở đây là nhịp hiển thị."""
    log.set_request_id(rid)  # asyncio.to_thread copy context này xuống pipeline
    enforce_length(req.message)
    answer, meta = await asyncio.to_thread(
        answer_pipeline, req.message, req.response_mode == "api")
    await asyncio.to_thread(telemetry.log_event, req.session_id, req.message,
                            answer["status"], answer["citations"])

    async def gen():
        yield f"event: meta\ndata: {json.dumps({'intent': meta['intent'], 'provider': meta['provider'], 'response_mode': meta['response_mode']})}\n\n"
        words = answer["answer_markdown"].split(" ")
        step = max(1, len(words) // 40)
        for i in range(0, len(words), step):
            part = " ".join(words[: i + step])
            yield f"event: partial\ndata: {json.dumps({'text': part})}\n\n"
            await asyncio.sleep(0.03)
        yield f"event: answer\ndata: {json.dumps(answer, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
