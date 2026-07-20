# COMPLETION REPORT — TKT-BOT · TIP-11 (Hardening trước khi phơi công khai)
Thợ (Claude Code) · 20/07/2026 · Vibecode Kit v6.1
Khế ước: TIP-PACK-2-TKT-BOT.md · nền X-RAY-REPORT.md

## STATUS

DONE 6/6 đầu việc. Không cần API key, chạy song song hàng chờ TIP-08. Verify
thật trên stack db+api dựng bằng `docker compose up -d --build` (đường LLM tắt,
fallback deterministic như hiện trạng), pytest 41/41 trong container python:3.12.

## FILES CHANGED

Mới:
```
tkt-bot/api/app/ratelimit.py          RateLimiter cửa sổ trượt theo IP, thuần, test được
tkt-bot/api/app/log.py                JSON logging + request_id contextvar
tkt-bot/api/tests/test_ratelimit.py   4 test thuần, không DB
tkt-bot/api/tests/test_bm25_cache.py  1 test hồi quy cache BM25 (cần DB)
tkt-bot/web/components/ErrorBoundary.tsx(+.module.css)  boundary bọc ChatSurface
```
Sửa:
```
api/app/main.py        guard() gộp request_id + rate limit; CORS đóng; 422 length cap;
                       /telemetry/stats thêm rate_limited
api/app/config.py      MAX_QUESTION_LEN, SITE_ADDRESS, CORS_ORIGINS (suy từ SITE_ADDRESS)
api/app/retrieval.py   _chunks_version() làm khóa cache _bm25_index(version)
api/app/pipeline.py    log 4 tầng router/retrieval/composer/verifier, bỏ print
api/app/router.py      thay print bằng log.event (đường LLM)
api/app/composer.py    thay print bằng log.event (đường LLM)
web/app/page.tsx       bọc ChatSurface trong ErrorBoundary
docker-compose.yml     DB_HOST_PORT tham số hóa; api nhận SITE_ADDRESS/CORS_ORIGINS/MAX_QUESTION_LEN
.env.example           tài liệu CORS_ORIGINS, MAX_QUESTION_LEN, DB_HOST_PORT
.gitignore             thêm tkt_pgdata/, *.tsbuildinfo
```

## TEST RESULTS

| Hạng mục (AC) | Kết quả | Bằng chứng |
|---|---|---|
| Rate limit 11 req/phút (AC1) | PASS | req 1..10 → 200, req 11 → 429, thân JSON thông điệp tử tế |
| Telemetry đếm 429 (AC1) | PASS | `meta.counter:rate_limited`=1 sau đúng một lần 429; `/telemetry/stats.rate_limited` phơi ra |
| Cap 500 ký tự | PASS | 601 ký tự → 422 "Câu hỏi hơi dài…"; đúng 500 ký tự → 200 (biên) |
| CORS origin lạ bị chặn (AC2) | PASS | preflight Origin `evil.example` → không có Access-Control-Allow-Origin (CORS_ORIGINS rỗng = deny) |
| BM25 thấy chunk mới ingest (AC3) | PASS | test_bm25_cache: chèn chunk giả, `_chunks_version` đổi, `hybrid_search` trả đúng chunk mới |
| request_id xuyên 4 tầng (AC4) | PASS | 1 request → grep log theo rid thấy api·router·retrieval·composer·verifier |
| Error Boundary fallback (AC5) | PASS | tsc --noEmit exit 0; boundary class component, nút "Tải lại trang", không trắng trang |
| Repo < 30 MB (AC6) | PASS | git objects 1.30 MiB; node_modules chưa từng track; .next/node_modules đã ignore |
| Tổng pytest | 41/41 | trong container python:3.12 (36 cũ + 5 mới) |

### Chi tiết dấu chân request_id (AC4)
```
rid=verify-trace-002
  api        request
  router     intent
  retrieval  retrieved
  composer   composed
  verifier   verified
  -> four-layer footprint present: True
```

## ISSUES

1. **Bug tự bắt trong lúc verify (đã fix):** bản đầu đặt request_id trong
   dependency `request_ctx`. Dependency sync của FastAPI chạy ở context
   threadpool riêng nên contextvar KHÔNG propagate xuống `answer_pipeline`,
   grep log chỉ thấy đúng dòng `api request`, ba tầng sau lệch id. Sửa: gộp
   thành `guard()` trả rid, endpoint gọi `log.set_request_id(rid)` trong thân
   mình (cùng context chạy pipeline; nhánh stream dựa vào asyncio.to_thread
   copy context). Re-verify: đủ 4 tầng.
2. **Rate limit trong tiến trình, không chia sẻ giữa worker.** Một container
   một tiến trình cho pilot là đủ. Scale ngang nhiều worker thì mỗi worker giữ
   bộ đếm riêng, hạn mức thực tế nhân lên theo số worker. Ghi chú sẵn trong
   ratelimit.py, đường nâng cấp là Redis.
3. **CORS mặc định deny mọi cross-origin.** An toàn vì web và api chung origin
   sau Caddy (không cần CORS cho app thật). Dev gọi API trực tiếp cross-origin
   thì khai `CORS_ORIGINS`.

## DEVIATIONS (luật một-câu v6.1)

1. **Cổng Postgres host tham số hóa `DB_HOST_PORT` (mặc định giữ 5433).** Máy
   này đã có `hiveos-db` chiếm 5433, dựng stack default sẽ đụng cổng. Mặc định
   không đổi nên hành vi cũ nguyên vẹn; verify chạy `DB_HOST_PORT=5434`. Đây là
   hardening đúng tinh thần deviation #5 của report vòng 1 (cổng đụng trên máy
   chung), giữ luôn.
2. **print() trong scripts/ (CLI offline) giữ nguyên,** chỉ thay print đường
   phục vụ request (app/). Scripts là công cụ người chạy tay, print là output
   cho người, không phải log máy.

## SUGGESTIONS

1. Khi có key và chạy TIP-08: đường LLM sẽ phát sinh log `router.llm` và
   `composer.llm` (model + token) cùng request_id, tiện đối soát chi phí.
2. Trước push đầu: `git rm -r --cached` không cần (node_modules chưa từng track).
   Repo sạch, đẩy thẳng được.
