# COMPLETION REPORT — TKT-BOT · TIP-12 Giai đoạn 1 (đổi da chat surface)
Thợ (Claude Code) · 20/07/2026 · Vibecode Kit v6.1
Khế ước: AMENDMENT-REQ08v2-TIP-12.md · chuẩn thị giác: mockup-tkt-uel-edition.html

## STATUS

DONE giai đoạn 1 (P0). **DỪNG tại checkpoint Human duyệt design** trước khi làm
giai đoạn 2 (landing + đồ thị + /registry/meta), đúng ràng buộc TIP-12.
Không đổi contract trả lời, không đổi cấu trúc luồng component, chỉ token,
typography, hình khối. Bản production dựng qua Caddy tại http://localhost:8080.

## TIỀN ĐỀ

Hai file khế ước nêu "Chủ nhà chép vào" chưa nằm trong repo lúc nhận việc. Thợ
tìm thấy trong ~/Downloads và chép vào đúng chỗ:
- `Logo-DH-Kinh-Te-Luat-UEL.webp` → `web/public/`
- `mockup-tkt-uel-edition.html` → repo root (đưa vào version control làm chuẩn)

## FILES CHANGED

Mới:
```
web/components/TierBadge.tsx(+.module.css)   badge tier dùng chung duy nhất (A3)
web/public/Logo-DH-Kinh-Te-Luat-UEL.webp     logo gốc
AMENDMENT-REQ08v2-TIP-12.md, mockup-tkt-uel-edition.html
```
Sửa:
```
web/app/layout.tsx           next/font Fraunces + Be Vietnam Pro (subset vietnamese),
                             phơi --font-serif/--font-sans; bỏ theme-init (dark = Phase 2)
web/app/globals.css          thay trọn token sang bảng A1; --serif/--sans; bỏ .dark
web/components/ChatSurface.*  masthead logo + wordmark + verified (số từ /health, không hardcode)
web/components/MessageBubble.* user = đề từ serif "Hỏi —" + hairline; bot = prose editorial
web/components/CitationChip.*  cite chip trắng viền line-2 bo 3px + TierBadge sm
web/components/EvidenceSheet.* dossier "Hồ sơ bằng chứng": stamp, TierBadge lg, blockquote
                             serif viền uel, mark gạch chân uel-wash, dl metadata; giữ
                             hành vi bottom sheet <1100px và panel phải ≥1100px
web/components/DisputedBlock.* viền trái amber, gradient amber-wash
web/components/NullBlock.*     token mới, nút liên hệ viền uel-deep
web/components/InputBar.*      InputBar v2 (mockup vá 20/07): ô duy nhất, nút gửi ghost
                             40px trong góc phải, mũi tên SVG currentColor, hover/focus
                             đảo nền uel-deep 180ms, focus-within sáng viền uel; trạng thái
                             rỗng = mũi tên muted disabled, đang stream = ô vuông dừng
web/lib/api.ts               streamChat nhận AbortSignal; fetchClaimsCount đọc /health
web/components/ChatSurface.*  abortRef + stop(): nút dừng hủy stream thật, giữ phần đã hiện
web/components/SeasonCards.*   thẻ editorial: eyebrow uel-deep + tiêu đề serif
web/lib/api.ts               thêm fetchClaimsCount() đọc /health
web/Dockerfile               COPY public ./public (logo trước đây bị bỏ khỏi image)
```
ModeToggle.tsx giữ nguyên trong cây, tạm không render (dark = Phase 2).

## TEST RESULTS

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| tsc --noEmit | PASS | exit 0 sau đổi da |
| next/font subset vietnamese | PASS | dev + production build biên dịch sạch, Fraunces có glyph Việt |
| Production build (đường deploy) | PASS | `docker compose build web` exit 0 |
| Logo phục vụ trong container | PASS | GET /Logo...webp qua Caddy → 200, 109474 bytes (khớp file) |
| Masthead + welcome desktop | PASS | ảnh chụp :3100 và :8080 1280px: logo, wordmark serif, verified "110 dữ kiện" |
| Số verified không hardcode | PASS | đọc claims_loaded từ /health, lỗi thì ẩn số |
| Q&A grounded desktop | PASS | câu hỏi = đề từ serif "Hỏi —"; trả lời prose; 2 chip tier C badge vuông + tên nguồn đủ |
| Dossier evidence panel ≥1100px | PASS | panel phải: stamp "HỒ SƠ BẰNG CHỨNG", TierBadge lg, blockquote serif số uel-deep gạch chân, dl mã dẫn nguồn + URL, nút đóng, cột chat bị đẩy |
| Badge tier khai một chỗ (AC) | PASS | TierBadge dùng ở chip (sm) và sheet (lg), tâm chữ đúng cả hai cỡ |
| Contract trả lời không đổi | PASS | Answer JSON nguyên vẹn, chỉ đổi cách render |
| InputBar v2 rỗng/enabled/focus | PASS | ảnh zoom :8080: rỗng = mũi tên muted; có chữ = mũi tên uel-deep + viền ô sáng xanh (focus-within); placeholder italic, chữ gõ upright |
| Nút dừng khi stream | PASS (cấu trúc) | swap mũi tên↔ô vuông trong cùng slot 40px, không giật layout; onStop hủy AbortController thật |

## SCREENSHOTS

Chụp trực tiếp bằng Chrome:
- Desktop 1280px welcome (:3100 dev và :8080 prod)
- Desktop 1280px Q&A grounded với 2 citation chip
- Desktop dossier evidence panel bên phải (đã lưu đĩa)

## ISSUES

1. **Chụp mobile 390px chưa lấy được bằng công cụ browser.** resize_window kẹp
   bề rộng cửa sổ ở ~1230px trên môi trường này, thử 3 cỡ không reflow. Dừng
   không đào sâu. Reflow mobile bảo đảm bằng media query đã rà tay: verified pill
   ẩn <620px, thẻ mùa 1 cột <520px, evidence thành bottom sheet <1100px. Checkpoint
   Human xem trên máy thật là đường xác nhận cuối. AC "chụp cạnh mockup 390px"
   còn treo phần mobile, desktop đã xong.
2. **Lighthouse a11y/perf chưa đo lại.** AC yêu cầu a11y giữ 100 và perf không
   tụt quá 5 điểm. Chưa chạy trong phiên này, đề nghị đo trong checkpoint hoặc
   phiên sau khi Human duyệt hướng thẩm mỹ.

## FIX PHÁT SINH (Human bắt lỗi 20/07)

**Evidence_span hiện ra mã HTML.** 9 claim tier-C điểm chuẩn (nguồn ts247) lưu
evidence_span nguyên khối `<tr class="ant-table-row">...</tr>` vì trang render
điểm bằng bảng HTML, mà gate SPAN_NOT_FOUND của refinery buộc span là chuỗi con
verbatim của snapshot, nên markup là đoạn gốc duy nhất bắt được. Frontend hiện
đúng span đã lưu, không phải lỗi render.

- Fix trong tầng của Thợ (frontend): `cleanEvidence()` gỡ thẻ, nối ô bảng bằng
  " · ", giữ highlight số, không đụng claim. Kết quả đọc được:
  "Toán kinh tế (Chuyên ngành ...) · A00; A01 · 25.75". Verify trên :8080.
- **Fix gốc thuộc refinery (Chủ thầu):** hoặc thêm field `evidence_display`
  sạch song song span verbatim, hoặc chụp text-extracted cho ts247. Còn ảnh hưởng
  khác: composer LLM cũng nhận HTML thô cho 9 claim này (phí token nhẹ), chỉ fix
  dữ liệu mới dứt điểm cả frontend lẫn context. Đề nghị gộp vào TIP-09.

## DEVIATIONS (luật một-câu v6.1)

1. **web/Dockerfile thêm COPY public ./public.** Bản standalone của Next không
   tự chép public/, logo mới sẽ 404 trong container. Không có deviation này thì
   masthead vỡ ảnh ở production. Sửa và verify 200.
2. **Bỏ phone-shell (vỏ điện thoại 480-900px), chuyển full-bleed editorial mọi
   bề rộng.** Mockup không có khung điện thoại; giữ khung sẽ lệch "cùng hệ thiết
   kế" ở 390px. Cấu trúc component và hành vi evidence sheet giữ nguyên.
3. **Gỡ ModeToggle khỏi header.** Amendment A1 chốt dark mode là Phase 2. Giữ
   file component để Phase 2 khôi phục, chỉ không render.

## CHECKPOINT

Theo TIP-12 constraint: **Human duyệt design giai đoạn 1 trước khi Thợ làm giai
đoạn 2.** Xem tại http://localhost:8080 (bản production) hoặc chạy dev để soi kỹ.
Nếu duyệt, giai đoạn 2 gồm: endpoint /registry/meta phía api, landing route /,
đồ thị SVG tự vẽ từ registry (hàm scale có unit test giá trị biên), timeline 2026
tự ẩn ngoài khung, count-up tôn trọng prefers-reduced-motion, route chat về /chat.

## SUGGESTIONS

1. Duyệt hướng thẩm mỹ desktop trước, mobile Thợ chụp lại được khi có công cụ
   emulation, hoặc Human liếc trên điện thoại.
2. Giai đoạn 2 nên mở endpoint /registry/meta trước để cả stat strip lẫn đồ thị
   dùng chung một nguồn số, đúng nguyên tắc "không hardcode số".
