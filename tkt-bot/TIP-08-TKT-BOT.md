# TIP-08: Kích hoạt đường LLM thật và đóng D1 D2 D3

## HEADER
- TIP-ID: TIP-08 · Project: TKT-BOT · Module: refine
- Depends on: TIP-01..07 DONE, ANTHROPIC_API_KEY có trong .env
- Priority: P0 · Effort: ~60 phút

## CONTEXT
- Working directory: /Users/os/chatbotUEL/tkt-bot
- Key files: COMPLETION-REPORT.md vòng 1, Decisions Log mục 9 của Blueprint
- Bốn đầu việc đã ghi trong Decisions Log, TIP này là bản thi hành

## TASK
Bật đường LLM thật rồi lặp lại các bằng chứng vốn mới có trên fallback.

0. (L2 đã chốt 12/07) Tách allowed của trace verifier thành hai tập: số chỉ
   đối chiếu value cộng evidence_span cộng text chunk; tên nguồn và snapshot
   chỉ phục vụ trace tên riêng, số dính trong tên nguồn được mask trước khi
   bóc. Unit test: "247" đứng rời khi context không có claim giá trị ấy phải
   bị chặn, "tuyensinh247.com" nguyên chuỗi vẫn hợp lệ. Chạy trước mọi đầu
   việc LLM.
1. Điền key, xác nhận composer gọi claude-sonnet-4-6 và router gọi Haiku thật
   (log model id trong response metadata).
2. Chạy lại smoke 12 câu qua LLM. Ghi trạng thái từng câu và P95 thật,
   ngưỡng 6 giây khi chưa cache.
3. Bộ đánh giá văn phong: 30 câu hỏi đa dạng (eval-questions.txt), mỗi câu
   trả lời thật đi qua style_lint. Báo số vi phạm cứng, số warning REPEAT,
   số vòng viết lại đã kích hoạt. Đọc thủ công 5 câu bất kỳ và nhận xét
   một dòng mỗi câu về độ tự nhiên.
4. Bật EMBEDDINGS=e5, re-ingest, so sánh retrieval trên 10 câu diễn giải:
   với mỗi câu ghi top-3 chunk của hash và của e5, đánh dấu bên nào trúng ý
   hơn. Kết luận một đoạn.
5. (Verify REQ-08 mở rộng, 12/07) Liếc lại reflow ở bề rộng 1100 đến 1200:
   khi SSE stream từng từ làm bubble cao dần trong lúc evidence panel đang
   mở và đẩy cột chat, xem cột có giật không. Giao điểm của hai thứ mới
   chưa từng chạy cùng nhau, một dòng kiểm tra bằng mắt.

## ACCEPTANCE CRITERIA
- Given key hợp lệ, When smoke 12 câu, Then 12/12 đúng trạng thái và P95 < 6s.
- Given 30 câu eval, When qua style_lint, Then 0 vi phạm cứng lọt ra render;
  vòng viết lại nếu có phải được log đủ input output.
- Given EMBEDDINGS=e5, When re-ingest 235 chunks, Then ingest sạch và bảng
  so sánh 10 câu có trong report.
- Given một câu trả lời LLM bất kỳ, When soi citations, Then mọi con số trong
  câu đều có claim_id truy vết được (chọn ngẫu nhiên 3 câu để kiểm tay,
  D1 chứng bằng mắt người chứ không chỉ bằng test tự viết).

## CONSTRAINTS
- Không sửa luật style_lint để "cho pass", lệch thì báo L2.
- Không đổi model ngoài hai model đã khai, muốn đổi thì escalate.
- Ghi chi phí API thực tế của toàn bộ TIP vào report để Chủ nhà chuẩn
  spend limit.

## REPORT FORMAT
COMPLETION REPORT chuẩn, đính kèm bảng smoke, bảng eval văn phong, bảng
so sánh embedding và tổng chi phí API.
