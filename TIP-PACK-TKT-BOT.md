# TIP PACK — TKT-BOT · Vibecode Kit v6.1
Phát cho Thợ (Claude Code) theo thứ tự dependency sau khi Human approve Blueprint.
Mỗi TIP nộp Completion Report chuẩn: STATUS, FILES CHANGED, TEST RESULTS, ISSUES, DEVIATIONS, SUGGESTIONS.

═══════════════════════════════════════════════════════════════

# TIP-01: Scaffold monorepo và data loader

## HEADER
- TIP-ID: TIP-01 · Project: TKT-BOT · Module: core/data
- Depends on: None · Priority: P0 · Effort: ~45 phút

## CONTEXT
- Working directory: ~/tkt-bot (tạo mới)
- Key files: nhận từ Chủ nhà thư mục `toan_kinh_te_uel/` gồm claims.jsonl, snapshots/, registry_output.txt
- Pattern: cấu trúc thư mục theo mục 3 của BLUEPRINT-TKT-BOT.md, đính kèm

## TASK
Dựng skeleton hai service api (FastAPI, Python 3.12) và web (Next.js 15, TypeScript) cùng docker-compose có postgres:16 với extension pgvector. Viết `api/scripts/load_data.py` đọc claims.jsonl, build registry.json tất định (entity × field, trạng thái corroborated, sourced, disputed, honest-null tính đúng luật refinery: disputed khi tồn tại từ hai value khác nhau, corroborated cần từ hai nguồn độc lập tier A hoặc B), rồi nạp bảng `claims` và `registry_cells` vào Postgres. Loader chạy lại nhiều lần cho cùng kết quả.

## SPECIFICATIONS
- Bảng claims giữ nguyên mọi field gốc kể cả evidence_span và capture.
- registry_cells: entity, field, status, value_json, claim_ids[].
- /health trả version và số claim đã nạp.
- Không gọi LLM ở TIP này.

## ACCEPTANCE CRITERIA
- Given claims.jsonl 71 dòng, When chạy load_data.py hai lần, Then registry_cells giống hệt nhau giữa hai lần và đủ 11 entity.
- Given ô so_giang_vien_co_huu của Khoa Toán Kinh tế, When query registry_cells, Then status là disputed và claim_ids chứa đúng hai claim.
- Given docker compose up, When gọi GET /health, Then trả 200 kèm claims_loaded=71.

## CONSTRAINTS
- Không sửa nội dung claims.jsonl, file là read-only đầu vào.
- Không thêm bảng ngoài spec, cần thêm thì escalate L2.

═══════════════════════════════════════════════════════════════

# TIP-02: Retrieval hybrid

## HEADER
- TIP-ID: TIP-02 · Module: api/retrieval · Depends on: TIP-01 · Priority: P0 · Effort: ~60 phút

## TASK
Cài ba đường truy xuất. Một, structured lookup: câu hỏi factual map về entity × field qua bảng từ khóa và trả thẳng ô registry kèm claim. Hai, BM25 trên chunks (dùng rank_bm25 hoặc tsvector tiếng Việt có dấu). Ba, vector search pgvector với model embedding đa ngữ. Hợp nhất hai đường sau bằng reciprocal rank fusion rồi sắp lại theo tier A trước B trước C khi độ liên quan tương đương. Ingest đúng 14 snapshot được claims tham chiếu (Amendment 2026-07-12) thành chunks kèm metadata bắt buộc url, snapshot, fetched_at, tier. Bước liệt kê nguồn phải loại file placeholder và bản chụp thừa: file dưới 1 KB hoặc không xuất hiện trong bất kỳ capture.snapshot nào của claims.jsonl thì bỏ qua và log tên. Chunk thiếu metadata thì ingest phải fail loud.

## ACCEPTANCE CRITERIA
- Given câu "điểm chuẩn phân tích dữ liệu 2025", When gọi retrieval, Then structured lookup trả ô diem_thpt_2025 của CN Phân tích dữ liệu trước mọi kết quả semantic.
- Given một chunk cố tình thiếu fetched_at, When chạy ingest, Then process dừng với exit khác 0 và thông báo tên chunk.
- Given thư mục snapshots chứa file placeholder dưới 1 KB và file không được claim nào tham chiếu, When chạy ingest, Then hai loại file này bị bỏ qua kèm log tên và tổng nguồn ingest đúng 14.
- Given câu hỏi diễn giải "học ngành này ra làm gì", When retrieval, Then top 5 kết quả đều mang metadata nguồn đầy đủ.

## CONSTRAINTS
- Số liệu không đi qua embedding để trả lời, embedding chỉ phục vụ tìm đoạn văn.
- Không hardcode câu hỏi mẫu vào code.

═══════════════════════════════════════════════════════════════

# TIP-03: Answer composer và Domain Constitution

## HEADER
- TIP-ID: TIP-03 · Module: api/composer · Depends on: TIP-02 · Priority: P0 · Effort: ~60 phút

## TASK
Viết constitution.py chứa system prompt theo mục 4 Blueprint, đủ sáu luật văn phong và luật ứng xử: honest-null nói thẳng chưa có dữ liệu kèm kênh liên hệ, disputed trình bày mọi phiên bản kèm nguồn, không hứa hẹn kết quả trúng tuyển, không tư vấn tài chính cá nhân. Composer gọi Claude API model claude-sonnet-4-6, nhận context là các claim và chunk kèm citation id, trả đúng JSON contract mục 3. Router intent chạy trước bằng một lệnh gọi nhỏ few-shot trả JSON, smalltalk đi thẳng composer không tốn retrieval.

## ACCEPTANCE CRITERIA
- Given câu "trưởng khoa là ai", When compose, Then status=disputed và citations chứa cả hai claim học hàm.
- Given câu "chỉ tiêu 2026", When compose, Then status=null, answer nêu rõ chưa công bố và không chứa con số bịa.
- Given câu "nên đầu tư coin nào", When router chạy, Then intent=oos và bot từ chối lịch sự kèm gợi ý kênh đúng.
- Given mười câu hỏi thử trong bộ test kèm TIP, When compose, Then output parse được JSON hợp lệ cả mười.

## CONSTRAINTS
- API key đọc từ env, không hardcode.
- Không stream ở TIP này, streaming để TIP-05 nối.

═══════════════════════════════════════════════════════════════

# TIP-04: Verifier và style_lint

## HEADER
- TIP-ID: TIP-04 · Module: api/verifier · Depends on: TIP-03 · Priority: P0 · Effort: ~50 phút

## TASK
Hai tầng kiểm sau composer. Tầng trace: bóc mọi số và tên riêng trong answer_markdown, đối chiếu tập claim đã cấp, số nào không truy vết được thì chặn và yêu cầu composer viết lại kèm chỉ dẫn. Tầng style_lint (pure function, file riêng): luật cứng gồm cấm ký tự em-dash và en-dash, chấm phẩy tối đa một, cấm chuỗi ", và" và ", &"; luật mềm gồm cảnh báo từ nội dung lặp quá hai lần trong một đoạn sau khi chuẩn hóa dấu và lowercase, bỏ qua stopwords tiếng Việt. Vi phạm cứng thì viết lại tối đa hai vòng, quá thì trả fallback an toàn và log.

## ACCEPTANCE CRITERIA
- Given answer chứa "25,75 điểm" khi context không có claim 25,75, When verify, Then answer bị chặn và có retry.
- Given answer chứa em-dash, When style_lint, Then trả violation code EMDASH và composer nhận yêu cầu viết lại.
- Given answer chứa "toán, và kinh tế", When style_lint, Then trả violation COMMA_VA.
- Given đoạn lặp "điểm chuẩn" bốn lần, When style_lint, Then trả warning REPEAT kèm gợi ý đồng nghĩa từ bảng trong constitution.
- Given bộ 20 unit test kèm TIP cho style_lint, When pytest, Then 20/20 pass.

## CONSTRAINTS
- style_lint không gọi mạng, không gọi LLM, thuần deterministic.
- Không nới luật cứng thành mềm, muốn nới thì escalate L2.

═══════════════════════════════════════════════════════════════

# TIP-05: Frontend theo mockup

## HEADER
- TIP-ID: TIP-05 · Module: web · Depends on: TIP-01 (chạy song song với 02-04 bằng mock API) · Priority: P0 · Effort: ~90 phút

## CONTEXT
- Key file: mockup-chatbot-toan-kinh-te-uel.html đính kèm, là chuẩn thị giác đã duyệt. Token màu, spacing, hành vi bottom sheet lấy nguyên từ đây.

## TASK
Dựng Next.js App Router các component ChatSurface, MessageBubble, CitationChip, EvidenceSheet, DisputedBlock, NullBlock, SeasonCards, InputBar, ModeToggle. Nối /chat với streaming SSE. Render đúng ba trạng thái theo status trong JSON contract. Bottom sheet hiển thị evidence_span có highlight, tier badge, fetched_at, url. Dark mode toggle lưu localStorage... dùng cookie hoặc state server-safe thay localStorage nếu môi trường không cho. Mobile-first 360px, WCAG AA, prefers-reduced-motion.

## ACCEPTANCE CRITERIA
- Given viewport 360px, When mở trang, Then không tràn ngang và bốn thẻ mùa hiển thị đủ.
- Given câu trả lời disputed từ API thật, When render, Then khối vàng liệt kê đủ mọi value kèm nguồn.
- Given chạm citation chip, When sheet mở, Then thấy đoạn gốc nguyên văn có highlight và ngày chụp.
- Given bật dark mode rồi reload, When trang tải lại, Then giữ nguyên chế độ.
- Given Lighthouse mobile, When audit, Then accessibility ≥ 95.

## CONSTRAINTS
- Không đưa thêm thư viện UI nặng, styling bằng CSS modules hoặc Tailwind, chọn một và nhất quán.
- Không đổi token màu đã duyệt, đổi là đổi khế ước.

═══════════════════════════════════════════════════════════════

# TIP-06: Telemetry và cache

## HEADER
- TIP-ID: TIP-06 · Module: api/telemetry · Depends on: TIP-03 · Priority: P1 · Effort: ~40 phút

## TASK
Log mỗi lượt hỏi dạng ẩn danh: hash phiên, câu hỏi, status, citations, thumbs. Endpoint /telemetry/nulls trả các câu rơi honest-null nhiều lần làm backlog crawl. Cache trả lời theo khóa chuẩn hóa câu hỏi với TTL 24 giờ cho intent factual, bỏ cache khi registry version đổi.

## ACCEPTANCE CRITERIA
- Given cùng một câu factual hỏi hai lần, When lần hai, Then trả từ cache và không gọi Claude API (đếm bằng counter).
- Given ba phiên khác nhau hỏi cùng câu honest-null, When gọi /telemetry/nulls, Then câu đó đứng đầu danh sách kèm count=3.

═══════════════════════════════════════════════════════════════

# TIP-07: Deploy và smoke test

## HEADER
- TIP-ID: TIP-07 · Module: infra · Depends on: TIP-04, TIP-05, TIP-06 · Priority: P1 · Effort: ~45 phút

## TASK
Hoàn thiện docker-compose production, Caddyfile reverse proxy, env template, README chạy một lệnh. Viết smoke test script bắn 12 câu chuẩn (bốn grounded, ba disputed, ba honest-null, hai oos) và assert status đúng cùng thời gian phản hồi P95 dưới 6 giây khi chưa cache.

## ACCEPTANCE CRITERIA
- Given máy sạch có Docker, When docker compose up -d và chạy smoke, Then 12/12 pass.
- Given container restart, When gọi /health, Then dữ liệu còn nguyên nhờ volume Postgres.

## GHI CHÚ CHUNG CHO THỢ
Bài học hạ tầng đã trả giá từ các dự án trước: hardcode URL trong Next.js standalone build, dùng --force-recreate khi đổi env, đường dẫn static file của Caddy là path trong container không phải trên host. Thấy cách tốt hơn spec thì ghi SUGGESTIONS, không tự đổi kiến trúc. Ambiguity nhỏ đủ context thì tự quyết và ghi DEVIATIONS theo luật một-câu v6.1.
