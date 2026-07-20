# AMENDMENT REQ-08 v2 + TIP-12 — Design System "UEL Edition"
Chủ thầu soạn 20/07/2026. Hiệu lực khi Human xác nhận trong Decisions Log.
Chuẩn thị giác gốc: mockup-tkt-uel-edition.html (bản đã vá badge). Mockup cũ màu xanh #144e8c hết hiệu lực làm chuẩn, giữ trong repo làm lịch sử.

---

## PHẦN A · AMENDMENT REQ-08 v2

### A1. Token (thay toàn bộ bảng cũ)

| Token | Giá trị | Dùng cho |
|---|---|---|
| --paper | #fafbfc | nền trang |
| --paper-2 | #f1f5f8 | nền section phụ |
| --ink | #14202a | chữ chính |
| --ink-2 | #3f515f | chữ phụ |
| --muted | #7b8894 | nhãn, caption |
| --line / --line-2 | #dfe6ec / #cdd8e1 | hairline, viền |
| --uel | #0090dc | đồ họa, badge A, nút, đồ thị |
| --uel-deep | #0b5c8d | chữ nhấn, headline bold, link |
| --uel-wash | #e8f5fc | nền wash, highlight evidence |
| --amber / --amber-wash | #b07a15 / #fdf5e3 | khối disputed |
| --tierB / --tierC | #4d6274 / #9aa8b3 | badge B, C |

Luật màu: #0090dc không dùng cho chữ dài trên nền sáng (tương phản không đủ), chữ nhấn luôn là --uel-deep. Disputed luôn hổ phách, cấm xanh. Dark mode Phase 2, chưa nằm trong TIP-12, bảng token dark sẽ có amendment riêng khi làm.

### A2. Typography

Fraunces (300/400/500, italic 400) cho display, câu hỏi của người dùng, số liệu lớn, blockquote evidence. Be Vietnam Pro (400/500/600) cho thân, UI, nhãn, badge. Nhãn nhỏ viết hoa tracking .14em đến .26em. Số trong bảng và đồ thị dùng tabular-nums.

### A3. Component đổi da (mapping cũ sang mới)

| Component | Chuẩn mới |
|---|---|
| Logo | logo tròn UEL trong masthead, file webp gốc, không vẽ lại |
| Câu hỏi user | không còn bubble nền đậm: render như đề từ serif, tiền tố "Hỏi — " màu muted, kẻ hairline dưới |
| Câu trả lời bot | prose editorial, strong màu ink, bảng số kiểu ấn phẩm: viền đậm 2px trên đầu, số serif tabular |
| Citation chip | nền trắng viền --line-2 bo 3px, badge tier 16px vuông bo 2px, chữ đủ tên nguồn |
| Badge tier | component dùng chung duy nhất: display grid, place-items center, line-height 1, font sans; khai một chỗ, cấm khai rải theo ngữ cảnh |
| Evidence sheet / panel | phong cách "Hồ sơ bằng chứng": nhãn con dấu --uel-deep góc trên, blockquote serif viền trái --uel, highlight bằng --uel-deep gạch chân --uel-wash, bảng dl hairline. **Nguyên tắc (VERIFY 20/07): hồ sơ bằng chứng cho người đọc chỉ chứa thứ kiểm chứng được bằng MẮT và một cú BẤM; mọi định danh máy (claim_id) ở lại trong payload JSON + telemetry, không hiển thị.** Hình hài cuối bốn tầng: (1) nguồn + tier + ngày chụp · (2) đoạn gốc nguyên văn highlight số · (3) URL nguồn link sống · (4) giải thích tier A/B/C. |
| Disputed | viền trái 2px --amber, nền gradient --amber-wash sang trong suốt 82%, tiêu đề tracking .2em |
| Honest-null, oos | giữ cấu trúc cũ, đổi token, nút liên hệ viền --uel-deep |
| Welcome screen | thêm dải chỉ số count-up (số đọc từ /health và registry meta, không hardcode) và bốn thẻ mùa restyle theo starters |
| Ô nhập (InputBar v2) | Một ô duy nhất: field bên trái, nút gửi 40px vuông bo 3px nằm gọn góc phải bên trong. Nút nghỉ là ghost (nền trong suốt, mũi tên → màu --uel-deep, không chữ). Hover hoặc focus bàn phím đảo sang nền --uel-deep đặc, mũi tên trắng, chuyển 180ms. Cả ô sáng viền --uel khi focus-within. Mũi tên là SVG inline stroke currentColor (một icon, đổi màu theo trạng thái), kèm aria-label. App thật thêm hai trạng thái: field rỗng thì mũi tên hạ về --muted và không hover (disabled); đang stream thì mũi tên thay bằng ô vuông dừng, cùng 40px cùng vị trí để không giật layout. |

### A4. Chuyển động

Reveal fade-up 0.7s cho khối vào khung nhìn, IntersectionObserver threshold 0.25, chạy một lần. Cột đồ thị scaleY 0.9s, thanh ngang scaleX 1s, donut stroke-dashoffset 1.1s, count-up 1.1s ease-out-cubic. Mọi thứ dưới ngưỡng chóng mặt: không parallax, không loop vô hạn trừ chấm pulse trạng thái. prefers-reduced-motion: hiển thị thẳng trạng thái cuối, count hiện số đích, bắt buộc có test.

### A5. Trang và đồ thị

Landing (route /) theo mockup: hero, dải chỉ số, hai panel đồ thị điểm chuẩn và ĐGNL, donut tier, timeline hồ sơ 2026, khối ví dụ hỏi đáp, colophon. Đồ thị SVG thuần tự vẽ từ registry qua API, cấm thư viện chart, cấm hardcode số trong SVG. Timeline chỉ hiện trong khung thời gian có lịch còn hiệu lực, ngoài khung tự ẩn.

---

## PHẦN B · TIP-12: Áp Design System UEL Edition

## HEADER
- TIP-ID: TIP-12 · Project: TKT-BOT · Module: web · Depends on: TIP-11 DONE
- Priority: P0 cho chat surface, P1 cho landing · Effort: ~2 phiên

## CONTEXT
- Working directory: /Users/os/chatbotUEL/tkt-bot/web
- Key files: mockup-tkt-uel-edition.html (chuẩn duy nhất), AMENDMENT phần A ở trên
- Logo: Logo-DH-Kinh-Te-Luat-UEL.webp, Chủ nhà chép vào web/public/

## TASK
Giai đoạn 1 (P0): đổi da chat surface hiện có theo A1 đến A4. Không đổi cấu trúc component, không đổi contract, chỉ token, typography, hình khối. Badge tier gom về một component TierBadge duy nhất. Câu hỏi user chuyển từ bubble sang đề từ serif. EvidenceSheet đổi sang phong cách hồ sơ bằng chứng, giữ nguyên hành vi bottom sheet dưới 1100px và panel phải từ 1100px.
Giai đoạn 2 (P1): dựng landing / theo A5, dữ liệu chỉ số và đồ thị lấy từ API (/health cộng endpoint mới /registry/meta trả số claim, entity, snapshot, phân bố tier, các ô điểm 2025, lịch 2026). Route chat chuyển về /chat.

## SPECIFICATIONS
- Font qua next/font, subset vietnamese, tránh FOUT.
- SVG đồ thị là component nhận data prop, scale tính bằng hàm, có unit test cho hàm scale (bài học lỗi baseline 24 làm cột 24,03 tàng hình đã trả giá ở mockup).
- /registry/meta phía api: đọc từ bảng registry_cells và meta, cache theo registry_version.
- Timeline đọc lich_tuyen_sinh_2026 từ registry, parse hai mốc ngày, ngoài khoảng thì component trả null.

## ACCEPTANCE CRITERIA
- Given trang chat sau đổi da, When chụp cạnh mockup ở 390px và 1280px, Then người thường phân biệt được đây là cùng một hệ thiết kế (Human review, checkpoint design bắt buộc).
- Given badge tier ở chip, ở sheet, ở landing, When đo tâm chữ, Then đúng tâm ở cả ba cỡ, style khai đúng một chỗ.
- Given prefers-reduced-motion, When tải landing, Then không animation nào chạy và mọi con số hiện giá trị đích (test tự động).
- Given registry đổi version, When gọi /registry/meta, Then số mới phản ánh không cần restart web.
- Given hàm scale đồ thị với bộ giá trị biên (min bằng max, giá trị sát baseline), When unit test, Then không sinh cột âm hay cột tàng hình.
- Given Lighthouse mobile sau đổi da, Then accessibility giữ 100 và performance không tụt quá 5 điểm so với trước.

## CONSTRAINTS
- Không đụng api ngoài endpoint /registry/meta.
- Không thêm thư viện UI, chart, animation. CSS Modules hiện hành.
- Số trong đồ thị không bao giờ hardcode, kể cả trong test snapshot.
- Checkpoint: Human duyệt design giai đoạn 1 trước khi làm giai đoạn 2.

## REPORT FORMAT
Completion Report chuẩn kèm ảnh chụp so sánh mockup và bản thật ở hai cỡ màn hình.
