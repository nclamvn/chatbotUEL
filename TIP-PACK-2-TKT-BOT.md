# TIP PACK 2 — TKT-BOT · TIP-09, TIP-10, TIP-11
Chủ thầu soạn 20/07/2026. Thứ tự thi hành: TIP-11 ngay (không cần key), TIP-09 sau khi TIP-08 xong, TIP-10 cuối vì cần eval harness đo được trước khi tinh chỉnh.

═══════════════════════════════════════════════════════════════

# TIP-11: Hardening trước khi phơi công khai

## HEADER
- TIP-ID: TIP-11 · Module: api/infra · Depends on: không (chạy song song chờ key)
- Priority: P0, nâng từ khuyến nghị X-RAY thành điều kiện go-live · Effort: ~60 phút

## TASK
1. Rate limiting theo IP trên /chat và /chat/stream: 10 request một phút, 100 một giờ, trả 429 kèm thông điệp tử tế đúng văn phong Constitution. Giới hạn câu hỏi 500 ký tự, quá thì 422 với gợi ý rút gọn.
2. CORS đóng về danh sách origin cụ thể đọc từ env, mặc định chỉ SITE_ADDRESS. Dev thêm localhost qua env, không hardcode.
3. Vá BM25 lru_cache: khóa cache gắn registry_version cộng chunks_version (đếm hoặc max updated_at của bảng chunks), đổi version là cache tự chết. Kèm test: ingest thêm một chunk giả, truy vấn ngay, chunk mới phải xuất hiện được trong ứng viên BM25.
4. Structured logging JSON có request_id sinh ở middleware, truyền xuyên router, retrieval, composer, verifier. Thay toàn bộ print().
5. React Error Boundary bọc ChatSurface, fallback tĩnh có nút tải lại, không màn hình trắng.
6. .gitignore chặn node_modules, .next, .env, tkt_pgdata trước lần push đầu. Nếu lịch sử commit đã dính node_modules thì làm sạch bằng filter-repo trước khi push, báo kích thước repo trước và sau.

## ACCEPTANCE CRITERIA
- Given 11 request một phút từ cùng IP, When gọi /chat, Then request 11 nhận 429 và telemetry đếm được.
- Given origin lạ, When preflight, Then bị chặn; origin trong env thì qua.
- Given chunk mới ingest, When BM25 truy vấn ngay sau đó, Then chunk xuất hiện trong ứng viên (test tự động).
- Given một request bất kỳ, When grep log theo request_id, Then thấy đủ dấu chân qua bốn tầng pipeline.
- Given lỗi ném từ component con, When render, Then Error Boundary hiện fallback thay vì trắng trang.
- Given git count-objects sau làm sạch, Then repo dưới 30 MB.

## CONSTRAINTS
- Không thêm dependency nặng cho rate limit, ưu tiên middleware tự viết hoặc slowapi.
- Không đổi contract trả lời.

═══════════════════════════════════════════════════════════════

# TIP-09: Làm giàu dữ liệu vòng 3 — lý lịch khoa học và corpus nghiên cứu

## HEADER
- TIP-ID: TIP-09 · Module: data · Depends on: TIP-08 DONE (cần đường LLM thật để kiểm câu hỏi mới) · Priority: P1 · Effort: ~90 phút, có phần của Chủ thầu

## PHÂN VAI
Phần cào và tinh lọc claim mới do Chủ thầu chạy bằng engine refinery (đúng phân vai đã làm hai vòng trước), Thợ nhận claims.jsonl v1.2 và corpus mới rồi lo phần nạp cộng kiểm.

## TASK (phần Thợ)
1. Nhận gói v1.2: PDF lý lịch khoa học các giảng viên (link có sẵn trong maths-nhan-su.html), claim mới về học vấn, hướng nghiên cứu từng người, cộng chunk hóa trang công bố khoa học đã có snapshot.
2. Nạp bằng loader hiện hành, không sửa logic. Chunk PDF phải mang metadata nguồn đủ bốn trường như mọi chunk khác, thiếu thì ingest fail loud như cũ.
3. Nhãn tiếng Việt cho mọi field mới khai cùng lúc thêm schema, thiếu nhãn thì render fail loud (constraint kế thừa từ bug template lộ tên field thô).
4. Smoke bổ sung 6 câu kiểu "thầy cô nào nghiên cứu về X", "cô Uyên từng học ở đâu", chạy qua đường LLM thật.

## ACCEPTANCE CRITERIA
- Given claims v1.2, When loader chạy hai lần, Then digest trùng và số entity không giảm so với v1.1.
- Given câu "giảng viên nào nghiên cứu về copula", When /chat, Then trả grounded kèm citation về đúng người có công bố liên quan.
- Given một PDF không trích được text sạch, When ingest, Then file bị loại có log tên thay vì sinh chunk rác.

═══════════════════════════════════════════════════════════════

# TIP-10: Nâng cấp RAG — đo trước, chỉnh sau

## HEADER
- TIP-ID: TIP-10 · Module: api/retrieval · Depends on: TIP-08, TIP-09 · Priority: P1 · Effort: ~2 phiên

## TASK
Thứ tự bắt buộc: dựng thước đo trước khi tinh chỉnh bất kỳ thứ gì.
1. Golden set 50 cặp hỏi đáp có đáp án chuẩn và trạng thái kỳ vọng (Chủ thầu soạn 30, Thợ bổ sung 20 từ null backlog thật của telemetry). Script eval chạy một lệnh, báo accuracy trạng thái, precision citation, tỉ lệ trả lời đúng ô registry.
2. Query rewrite: câu ghép ("điểm chuẩn và học phí của chuyên ngành tiếng Anh") tách thành truy vấn nguyên tử trước retrieval, dùng Haiku, có test.
3. Tổng hợp đa ô: intent so sánh ("so sánh ba chuyên ngành") ghép nhiều registry cell thành một bảng trong answer_markdown, mọi số vẫn qua trace gate.
4. Reranker sau RRF cho câu diễn giải, chỉ bật nếu golden set chứng minh tăng điểm, không tăng thì ghi kết luận và không merge.

## ACCEPTANCE CRITERIA
- Given golden set, When chạy eval trước và sau mỗi thay đổi, Then mỗi thay đổi merge được phải kèm delta điểm không âm trên cả ba chỉ số.
- Given câu ghép hai ý, When rewrite, Then hai truy vấn nguyên tử đều có kết quả và câu trả lời phủ đủ hai ý.
- Given câu so sánh ba chuyên ngành, When /chat, Then một bảng ba cột với 9 con số đều truy vết được.

## CONSTRAINTS
- Không merge thay đổi retrieval nào thiếu số đo golden set đi kèm. Cảm giác "có vẻ tốt hơn" không phải bằng chứng.
