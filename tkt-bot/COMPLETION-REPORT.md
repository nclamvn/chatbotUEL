# COMPLETION REPORT — TKT-BOT · TIP-01 → TIP-07
Thợ (Claude Code) · 12/07/2026 · Vibecode Kit v6.1
Khế ước: BLUEPRINT-TKT-BOT.md · TIP-PACK-TKT-BOT.md (kèm Amendment 2026-07-12)

## STATUS

DONE 7/7 TIP. Stack bốn container (db, api, web, caddy) chạy tại
`/Users/os/chatbotUEL/tkt-bot/`, dựng lại từ máy sạch bằng một lệnh
`docker compose up -d --build`.

## FILES CHANGED

Toàn bộ repo tạo mới trong phiên này:

```
tkt-bot/
├── api/
│   ├── app/            main, config, db, models, retrieval, router, composer,
│   │                   verifier, style_lint, constitution, pipeline, telemetry,
│   │                   embeddings
│   ├── scripts/        load_data.py (idempotent), ingest_chunks.py (fail-loud)
│   ├── tests/          test_style_lint (20), test_verifier (4), test_ingest (2),
│   │                   test_pipeline (2)
│   ├── data/           claims.jsonl (read-only copy), domain.yaml, snapshots/,
│   │                   registry.json (loader sinh)
│   ├── Dockerfile · entrypoint.sh · requirements.txt
├── web/                Next.js 15 App Router, CSS Modules
│   ├── app/            layout (theme init, Be Vietnam Pro), page, globals.css (token)
│   ├── components/     ChatSurface, MessageBubble, CitationChip, EvidenceSheet,
│   │                   DisputedBlock, NullBlock, SeasonCards, InputBar, ModeToggle
│   ├── lib/            api.ts (SSE reader), markdown.tsx, types.ts
│   └── Dockerfile      (standalone, không hardcode URL)
├── docker-compose.yml · Caddyfile · .env.example · README.md
├── scripts/smoke_test.py
└── COMPLETION-REPORT.md (file này)
```

## TEST RESULTS

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Loader idempotent (TIP-01) | PASS | 2 lần chạy cùng digest `cec55439dad2433c`, claims=71, entities=11, cells=352 |
| Ô disputed mẫu (TIP-01) | PASS | `so_giang_vien_co_huu` của Khoa: status disputed, đúng 2 claim_ids |
| /health (TIP-01) | PASS | 200, `claims_loaded=71`, kèm registry_version |
| Ingest amendment (TIP-02) | PASS | đúng 14 snapshot được tham chiếu, 6 file loại có log tên (1 file dưới 1 KB, 5 không tham chiếu), 235 chunks |
| Fail loud metadata (TIP-02) | PASS | thiếu fetched_at → exit ≠ 0 kèm tên snapshot (test_ingest) |
| Structured trước semantic (TIP-02) | PASS | "điểm chuẩn phân tích dữ liệu 2025" → 2 ô diem_thpt_2025 của CN PTDL đứng trước chunks |
| Composer 4 AC (TIP-03) | PASS | disputed trưởng khoa đủ 2 claim học hàm, null chỉ tiêu 2026 không số bịa, oos coin từ chối kèm kênh, 10/10 câu ra JSON contract hợp lệ (Pydantic validate) |
| style_lint 20 test (TIP-04) | PASS | pytest 20/20, codes EMDASH SEMICOLON COMMA_VA REPEAT |
| Trace verifier (TIP-04) | PASS | "25,75" ngoài context bị chặn UNTRACED_NUMBER, "31,5" ↔ "31.5" tương đương, tên riêng ngoài context bị chặn UNTRACED_NAME |
| Vòng viết lại (TIP-04) | PASS | test monkeypatch: vi phạm → feedback EMDASH → viết lại pass; 3 lần vi phạm → safe fallback status null kèm log |
| UI 360px (TIP-05) | PASS | viewport 356px không tràn ngang, đủ 4 thẻ mùa (đo bằng Chrome thật) |
| Disputed render (TIP-05) | PASS | khối vàng liệt kê cả hai phiên bản học hàm kèm nguồn · tier |
| Bottom sheet (TIP-05) | PASS | evidence_span nguyên văn, số highlight, ngày chụp, URL, mã claim |
| Dark mode persist (TIP-05) | PASS | toggle → reload → giữ nguyên (localStorage tkt-theme) |
| Lighthouse a11y (TIP-05) | PASS | 100/100, ngưỡng 95, 0 audit fail |
| Cache counter (TIP-06, REQ-12) | PASS | xem khối bằng chứng dưới |
| Null backlog (TIP-06) | PASS | 3 session cùng câu null → /telemetry/nulls count=3 sessions=3 đứng đầu |
| Smoke 12 câu (TIP-07) | PASS | 12/12 đúng trạng thái: 4 grounded, 3 disputed, 3 null, 2 oos |
| Volume persistence (TIP-07) | PASS | compose down/up toàn stack → /health vẫn claims_loaded=71 |
| Tổng pytest | 28/28 | chạy trong container python:3.12 |

### Bằng chứng cache counter (đóng D4 của VERIFY vòng 1)

Chạy ngày 12/07/2026, sau khi TRUNCATE answer_cache và reset counter:

```
== hỏi lần 1: "điểm chuẩn phân tích dữ liệu 2025" (session d4-a) ==
HTTP 200
{"composer_calls":1,"cache_hits":0}
== hỏi lần 2: cùng câu, session d4-b ==
HTTP 200
{"composer_calls":1,"cache_hits":1}
```

composer_calls đứng yên ở 1 trong khi lượt hỏi thứ hai vẫn trả 200: câu trả lời
lấy từ cache, không đi qua composer (đường LLM lẫn fallback đều không chạy).
Cache key là câu hỏi chuẩn hóa, TTL 24h, tự vô hiệu khi registry_version đổi.

## ISSUES

1. **ANTHROPIC_API_KEY chưa được cấp** (Open Question 2). Toàn bộ acceptance
   chạy qua đường fallback deterministic: composer dựng câu từ template và ô
   registry, không gọi LLM. Kiến trúc LLM đã nối sẵn (claude-sonnet-4-6,
   router few-shot, vòng viết lại theo feedback verifier), điền key vào .env
   là kích hoạt, nhưng chưa có bằng chứng chạy thật. Hệ quả: P95 0.08s của
   smoke là số của fallback, không có giá trị dự báo production; fallback
   pass style gate vì chính nó là template. Cả hai điểm này thuộc D1/D2,
   chờ TIP-08.
2. Hai bug thật bị smoke bắt trong phiên, đã fix và re-run 12/12:
   - Template từ chối oos nhắc "Khoa Toán Kinh tế", verifier chặn
     UNTRACED_NAME với context rỗng rồi ép safe fallback → whitelist tên riêng
     xuất hiện trong template cố định (`_TEMPLATE_TEXT` trong verifier.py).
   - "Học phí chương trình tiếng Anh" khóa entity vào chuyên ngành Tiếng Anh
     trong khi ô học phí nằm ở entity Trường → structured_lookup thêm fallback
     sang bộ entity mặc định khi ô của entity đã match toàn null.

## DEVIATIONS (luật một-câu v6.1)

1. Working directory `/Users/os/chatbotUEL/tkt-bot` thay vì `~/tkt-bot` để nằm
   trong workspace được cấp quyền của phiên.
2. Embedding mặc định `hash` tất định offline thay vì model đa ngữ vì corpus
   pilot chỉ 14 tài liệu và BM25 gánh chính; `EMBEDDINGS=e5` bật bằng env.
   (VERIFY vòng 1 đã adopt cho dev và nâng thành D3: production bắt buộc e5.)
3. SSE stream từng từ sau khi verifier duyệt xong thay vì stream token thô từ
   LLM, vì REQ-06 buộc style gate chạy trước khi render.
4. Câu chào welcome bỏ em-dash của mockup cho nhất quán REQ-05; smalltalk trả
   status grounded không citation thay vì oos để lời chào không render thành
   khối từ chối.
5. Postgres map host 5433 và Caddy 8080 vì cổng 5432 và 3000 đã bị dự án khác
   trên máy chiếm (rtr-mrp-db và một app node).

## SUGGESTIONS

1. Khi có API key: chạy TIP-08 (smoke qua LLM đo P95 thật, 30 câu style eval
   với style_lint làm trọng tài, so sánh hash vs e5 trên 10 câu diễn giải,
   bằng chứng counter bổ sung nếu cần đường LLM).
2. Nối /telemetry/nulls vào quy trình crawl bổ sung của refinery làm vòng kín
   dữ liệu: câu honest-null lặp nhiều là backlog crawl có sẵn độ ưu tiên.
3. Điều kiện go-live vẫn treo: xác nhận dữ liệu nhân sự với văn phòng Khoa
   (khoatkt@uel.edu.vn), đã ghi Decisions Log và README (D5).
