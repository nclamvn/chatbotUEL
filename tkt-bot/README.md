# TKT-BOT · Cổng hỏi đáp Khoa Toán Kinh tế UEL

Chatbot tuyển sinh grounded trên 110 claims đã kiểm chứng của domain refinery
`toan_kinh_te_uel` (Registry v1.1, 23 thực thể). Mọi con số và tên riêng truy vết được về evidence_span,
bốn trạng thái trả lời: grounded, disputed, honest-null, oos.

## Chạy một lệnh

```bash
cp .env.example .env    # điền OPENAI_API_KEY và ANTHROPIC_API_KEY cho demo
docker compose up -d --build
```

- Cổng chính (Caddy): http://localhost:8080 (đổi qua `HTTP_PORT`)
- API trực tiếp: http://localhost:8000 · web trực tiếp: http://localhost:3002
- Postgres (pgvector): host port 5433
- Toggle trên masthead mặc định ở **Demo** (template ổn định, không gọi API).
  Chỉ chế độ **AI trực tiếp** mới gọi OpenAI và tự động fallback sang Claude.

Loader và ingest chạy tự động khi container api khởi động, idempotent,
chạy lại bao nhiêu lần cũng cho cùng registry (digest in ra log).

## Smoke test

```bash
python3 scripts/smoke_test.py               # mặc định localhost:8000
python3 scripts/smoke_test.py http://host:8000
```

12 câu phủ bốn trạng thái (4 grounded, 3 disputed, 3 null, 2 oos), assert
status đúng và P95 dưới 6 giây khi chưa cache.

## Unit test

```bash
docker compose run --rm api python -m pytest tests/
```

## Cấu trúc

Xem BLUEPRINT-TKT-BOT.md (khế ước) và TIP-PACK-TKT-BOT.md. Tóm tắt:

- `api/` FastAPI: retrieval ba đường (registry lookup, BM25, pgvector RRF),
  composer Claude API kèm fallback deterministic, verifier hai tầng
  (trace số/tên riêng + style_lint), telemetry và cache 24h theo registry version.
- `web/` Next.js 15 App Router, token thị giác lấy nguyên từ mockup đã duyệt,
  SSE streaming sau khi style gate duyệt xong.
- `Caddyfile` reverse proxy: `/api/*` vào api, còn lại vào web. Đặt
  `SITE_ADDRESS` để Caddy tự lo TLS trên production.

## Ghi chú vận hành

- Đổi env thì `docker compose up -d --force-recreate <service>`.
- Dữ liệu Postgres nằm trong volume `tkt_pgdata`, restart không mất.
- OpenAI là provider chính; nếu lỗi mạng, rate limit, model không khả dụng hoặc
  trả JSON sai contract, bot tự động thử Claude. Nếu cả hai thất bại, bot vẫn
  chạy bằng fallback deterministic.
- Bot chưa có API key vẫn chạy được ở chế độ fallback deterministic
  (đủ bốn trạng thái, câu chữ template). Có key thì composer viết tự nhiên hơn
  và vòng viết lại của style gate hoạt động đầy đủ.
- Điều kiện go-live: xác nhận dữ liệu nhân sự với văn phòng Khoa
  (khoatkt@uel.edu.vn). Xem Decisions Log trong Blueprint.
