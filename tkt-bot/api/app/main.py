import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from . import telemetry
from .config import APP_VERSION
from .db import connect
from .models import Answer, ChatRequest
from .pipeline import answer_pipeline

app = FastAPI(title="TKT-BOT API", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "claims_loaded": n,
        "registry_version": row["value"] if row else None,
    }


@app.post("/chat")
def chat(req: ChatRequest) -> Answer:
    answer, _meta = answer_pipeline(req.message)
    telemetry.log_event(req.session_id, req.message, answer["status"],
                        answer["citations"])
    return Answer(**answer)


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    question: str
    thumbs: str  # "up" | "down"


@app.post("/telemetry")
def feedback(req: FeedbackRequest):
    telemetry.log_event(req.session_id, req.question, "feedback", [], req.thumbs)
    return {"ok": True}


@app.get("/telemetry/nulls")
def telemetry_nulls():
    return {"backlog": telemetry.null_backlog()}


@app.get("/telemetry/stats")
def telemetry_stats():
    return {"composer_calls": telemetry.get_counter("composer_calls"),
            "cache_hits": telemetry.get_counter("cache_hits"),
            "llm_calls_composer": telemetry.get_counter("llm_calls_composer"),
            "llm_tokens_in_composer": telemetry.get_counter("llm_tokens_in_composer"),
            "llm_tokens_out_composer": telemetry.get_counter("llm_tokens_out_composer"),
            "llm_calls_router": telemetry.get_counter("llm_calls_router"),
            "llm_tokens_in_router": telemetry.get_counter("llm_tokens_in_router"),
            "llm_tokens_out_router": telemetry.get_counter("llm_tokens_out_router")}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE. Verifier duyệt xong toàn bộ câu trả lời rồi mới stream (REQ-06:
    style gate chạy trước khi render), nên stream ở đây là nhịp hiển thị."""
    answer, meta = await asyncio.to_thread(answer_pipeline, req.message)
    await asyncio.to_thread(telemetry.log_event, req.session_id, req.message,
                            answer["status"], answer["citations"])

    async def gen():
        yield f"event: meta\ndata: {json.dumps({'intent': meta['intent']})}\n\n"
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
