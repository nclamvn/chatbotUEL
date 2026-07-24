# TKT-BOT · Cổng hỏi đáp Khoa Toán Kinh tế UEL

Chatbot tuyển sinh grounded trên 139 claims đã kiểm chứng của domain refinery
`toan_kinh_te_uel` (Registry v1.3). Mọi con số và tên riêng truy vết được về evidence_span,
bốn trạng thái trả lời: grounded, disputed, honest-null, oos.

## Khởi chạy bản bàn giao

```bash
cp .env.example .env
docker compose up -d --build
```

Khi chưa cấu hình key, giữ `MODE=template`. Ứng dụng khởi động ở chế độ
**Demo**, dùng câu trả lời deterministic và không gọi dịch vụ AI bên ngoài.

- Cổng chính (Caddy): http://localhost:8080 (đổi qua `HTTP_PORT`)
- API trực tiếp: http://localhost:8000 · web trực tiếp: http://localhost:3002
- Postgres (pgvector): host port 5433
- Toggle trên masthead mặc định ở **Demo** (template ổn định, không gọi API).
  Chỉ chế độ **AI trực tiếp** mới gọi OpenAI và tự động fallback sang Claude.

Loader và ingest chạy tự động khi container api khởi động, idempotent,
chạy lại bao nhiêu lần cũng cho cùng registry (digest in ra log).

## Cấu hình API do Trường quản lý

Không có API key cá nhân nào trong repository. Quản trị viên của Trường thực hiện:

1. Tạo key riêng cho dự án trong tài khoản do Trường quản lý.
2. Đặt `OPENAI_API_KEY` và, nếu cần fallback, `ANTHROPIC_API_KEY` trong secret
   manager của nền tảng triển khai. Không commit file `.env`.
3. Đặt hạn mức chi tiêu và cảnh báo usage ở từng nhà cung cấp.
4. Đổi `MODE=llm`, sau đó recreate API:

```bash
docker compose up -d --force-recreate api
curl http://localhost:8000/health
```

Kết quả health phải hiển thị `primary: openai` và, khi có key Claude,
`fallback: anthropic`. Nếu chưa có key hợp lệ, giữ `MODE=template`.

## Smoke test

```bash
python3 scripts/smoke_test.py               # mặc định localhost:8000
python3 scripts/smoke_test.py http://host:8000
```

12 câu phủ bốn trạng thái (6 grounded, 3 disputed, 1 null, 2 oos), assert
status đúng và P95 dưới 6 giây khi chưa cache.

## Unit test

```bash
docker compose run --rm -e MODE=template api python -m pytest tests/
```

## Cấu trúc

Xem BLUEPRINT-TKT-BOT.md (khế ước) và TIP-PACK-TKT-BOT.md. Tóm tắt:

- `api/` FastAPI: retrieval ba đường (registry lookup, BM25, pgvector RRF),
  composer OpenAI chính, Claude fallback và template deterministic, verifier hai tầng
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
