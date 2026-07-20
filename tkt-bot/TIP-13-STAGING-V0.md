# TIP-13: Staging v0 template-only (quyết định D0)

## HEADER
- TIP-ID: TIP-13 · Project: TKT-BOT · Module: infra/release
- Depends on: TIP-11 DONE, TIP-12 giai đoạn 1 (dùng bản đã đổi da nếu Human đã duyệt design, chưa duyệt thì ship da cũ, không chờ)
- Priority: P0 · Effort: ~1 phiên

## CONTEXT
- Quyết định D0 đã được Human phê duyệt ngày 20/07/2026: đường fallback template là sản phẩm dùng được cho câu factual, ship staging trước khi có key. LLM khi về sẽ nâng cấp phần diễn giải, không phải điều kiện tồn tại.
- Deploy target: Render (Open Question 1, phương án mặc định đã chốt). DB_HOST_PORT và cấu hình cổng đã tham số hóa từ TIP-11.

## TASK
1. Dựng staging trên Render: service api, service web, Postgres managed hoặc container kèm volume. Env: EMBEDDINGS=hash chấp nhận được ở v0 vì retrieval factual chạy structured lookup cộng BM25, ghi rõ trong report rằng e5 bật cùng TIP-08.
2. Chế độ template-only tường minh: biến MODE=template, /health trả mode để không ai nhầm staging đang chạy LLM. Banner mảnh đầu trang "Bản thử nghiệm nội bộ, câu trả lời tổng hợp tự động từ nguồn công khai có dẫn nguồn".
3. Chặn index: robots.txt disallow toàn bộ, meta noindex, không sitemap.
4. Bảo vệ truy cập mức nhẹ: đường dẫn staging không đoán được hoặc basic auth một mật khẩu chung, đủ để chỉ người được mời vào, không cần hệ user.
5. Thu hoạch phản hồi: thumbs up down đã có thì nối vào telemetry, thêm ô góp ý một dòng tùy chọn sau mỗi câu trả lời. /telemetry/nulls và stats phải xem được qua một trang admin tối giản có basic auth riêng.
6. Smoke sau deploy: 12 câu chuẩn chạy từ ngoài vào qua URL staging, kèm kiểm rate limit hoạt động trên hạ tầng thật (Render có proxy, xác nhận middleware đọc đúng IP thật từ header X-Forwarded-For, không thì rate limit theo IP proxy là vô nghĩa).

## ACCEPTANCE CRITERIA
- Given URL staging, When mở từ máy ngoài, Then trang tải được, banner thử nghiệm hiển thị và /health trả mode=template.
- Given Googlebot user-agent, When fetch robots.txt, Then disallow all; view-source có meta noindex.
- Given 11 request một phút từ một IP thật phía sau proxy Render, Then request 11 nhận 429 (chứng minh đọc X-Forwarded-For đúng).
- Given người dùng bấm thumbs down kèm góp ý, Then bản ghi xuất hiện trong telemetry với hash session.
- Given smoke 12 câu chạy từ ngoài, Then 12/12 đúng trạng thái, P95 ghi nhận trên hạ tầng thật.
- Given trang admin, When mở không có basic auth, Then 401.

## CONSTRAINTS
- Không bật đường LLM ở staging này kể cả khi key về giữa chừng, đổi mode là việc của TIP-08 với đầy đủ bằng chứng, không đổi âm thầm.
- Không gắn domain chính thức nào của UEL, staging chạy trên subdomain Render mặc định cho đến khi Khoa xác nhận và Human quyết định khác.
- Chi phí hạ tầng ghi vào report để Human nắm con số trước khi nhân bản cho khoa khác.

## REPORT FORMAT
Completion Report chuẩn kèm URL staging, ảnh banner, kết quả smoke từ ngoài và chi phí tháng ước tính.
