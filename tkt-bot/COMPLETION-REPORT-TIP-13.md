# COMPLETION REPORT — TKT-BOT · TIP-13 (Staging v0 template-only)
Thợ (Claude Code) · 20/07/2026 · khế ước TIP-13-STAGING-V0.md

## STATUS
Code + config staging DONE và verify cục bộ 6/6 AC. **Việc dựng thật trên Render
cần tài khoản của Chủ nhà** (không làm được từ đây): provision service, đặt secret,
lấy URL, smoke từ ngoài, ước chi phí. Toàn bộ đã đẩy lên origin/main (commit
b8faa8f) để Render build từ repo.

## FILES (TIP-13)
```
api/app/config.py     MODE + LLM_ENABLED (authoritative), ADMIN_USER/PASS
api/app/main.py       /health trả mode; GET /admin (basic auth riêng); feedback comment
api/app/{composer,router,pipeline}.py  gate LLM bằng LLM_ENABLED (không phải chỉ key)
api/app/{telemetry,db}.py  cột comment cho telemetry_events (ALTER idempotent)
web/middleware.ts     gate mời basic auth (STAGING_USER/PASS), chừa robots.txt
web/app/layout.tsx    banner thử nghiệm + meta noindex (NEXT_PUBLIC_STAGING)
web/public/robots.txt disallow all
web/components/FeedbackBar.tsx  thumbs + ô góp ý một dòng -> /telemetry
web/{Dockerfile,globals.css,ChatSurface,MessageBubble,ChatSurface.module,lib/api}
Caddyfile             route /admin -> api
docker-compose.yml    env MODE/ADMIN/STAGING/NEXT_PUBLIC_STAGING
render.yaml           blueprint Render (scaffold)
```

## VERIFY CỤC BỘ (stack docker, template mode)
| AC | Kết quả | Bằng chứng |
|---|---|---|
| AC1 mode=template | PASS | /health → `mode: template`, claims 110 |
| AC2 noindex/robots | PASS | robots.txt disallow all (đọc được không cần auth); meta `noindex, nofollow`; banner hiển thị |
| AC3 rate limit đọc XFF | PASS | 11 req cùng X-Forwarded-For 9.9.9.9 → req 11 = 429; **XFF khác (8.8.8.8) → 200** (chứng minh đọc IP thật, không phải IP proxy chung) |
| AC4 feedback → telemetry | PASS | POST thumbs=down + comment → telemetry_events có comment kèm session_hash |
| AC6 admin 401/200 | PASS | /admin không auth → 401; admin creds → 200, trang mode=template + null backlog + counters |
| Constraint khóa LLM | PASS | key giả + MODE=template: /health template và llm_calls_composer 0→0 (LLM KHÔNG chạy) |
| pytest | 41/41 | gồm refactor LLM_ENABLED + test_pipeline cập nhật |

## CONSTRAINT
- **MODE=template authoritative:** thêm cờ `LLM_ENABLED = key AND MODE != template`,
  gate ở composer/router/pipeline. Key về giữa chừng KHÔNG bật LLM. Đổi mode là
  việc của TIP-08.
- Chưa gắn domain UEL; render.yaml dùng subdomain onrender.com.

## CÒN LẠI CHO CHỦ NHÀ (cần tài khoản Render)
1. Provision theo render.yaml: DB (bật `CREATE EXTENSION vector`), api, web. Đặt
   secret ADMIN_PASS/STAGING_PASS/STAGING_USER; build ARG API_PROXY_URL (URL api),
   NEXT_PUBLIC_STAGING=1. ANTHROPIC_API_KEY để trống.
2. Sau deploy: smoke 12 câu từ ngoài (scripts/smoke_test.py trỏ URL staging), đo
   P95 hạ tầng thật; xác nhận lại AC3 với proxy thật của Render.
3. Ước chi phí tháng (plan free có giới hạn + tự ngủ; nâng nếu cần) ghi vào đây.
4. Điền [LINK-STAGING] vào GOI-XAC-NHAN-KHOA.md và gửi khoatkt@uel.edu.vn.

## CHI PHÍ (ước, cần Chủ nhà xác nhận trên Render)
Plan free (web + web + db) = 0đ nhưng có giới hạn giờ chạy + service tự ngủ khi
rảnh (cold start ~30s). Pilot mời riêng chấp nhận được. Nâng starter (~7 USD/service)
nếu cần luôn nóng. Ghi số thật sau khi tạo.
