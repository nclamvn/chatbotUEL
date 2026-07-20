# BÁO CÁO TRẠNG THÁI TKT-BOT — cho Chủ thầu quyết plan tiếp theo
Thợ (Claude Code) · 20/07/2026 tối · nhánh main @ 21af9cb (sạch, đã đồng bộ origin)

## TRẠNG THÁI MỘT DÒNG
Sản phẩm chạy được, đã đẩy trọn lên GitHub. Stack 4 container sống local
(mode=template, 121 claims). Mọi việc phần Thợ làm được không cần key đã xong.
Bàn cờ giờ nghẽn ở ba quân phía Chủ nhà và vài quyết định thẩm mỹ/kỹ thuật.

## ĐÃ SHIP (từ registry v1.1 sáng nay → giờ, 6 commit)
1. **TIP-11 hardening**: rate limit theo IP (đọc X-Forwarded-For), CORS đóng, vá
   cache BM25, structured log + request_id, ErrorBoundary.
2. **TIP-12 giai đoạn 1**: đổi da "UEL Edition" (Fraunces + Be Vietnam Pro,
   TierBadge, dossier evidence, InputBar v2 nút gửi ghost + stop). CHỜ duyệt design.
3. **TIP-10 phần 1**: golden-set eval harness (42 câu, gate delta, tự xóa cache).
4. **TIP-13 staging v0**: MODE=template authoritative (khóa LLM dù có key), banner
   + noindex + robots, basic auth mời, /admin, feedback, render.yaml. Verify local 6/6.
5. **TIP-14 chống typo**: fold không dấu + viết tắt + fuzzy + anti-guess. Golden
   typo 4/12 → 11/12, core delta 0, overall 0.905.
6. **Registry v1.2**: 121 claims (+học bổng 2026, chiều sâu CV nhân sự), idempotent.
7. **Polish**: điểm chuẩn đa chuyên ngành → bảng ấn phẩm (bỏ 6 câu lặp); URL nguồn
   → link sống.

Bằng chứng chung: pytest 47/47, golden 0.905 không giẫm, privacy scrub sạch.

## BA QUÂN CHỜ TAY CHỦ NHÀ (không quân nào Thợ làm được)
| Quân | Mở cổng gì | Giá của mỗi ngày trễ |
|---|---|---|
| **Render** (provision staging) | TIP-15 load test; người dùng thật đổ câu vào null backlog | ~30 câu thí sinh/ngày không được trả + không ghi backlog |
| **Email Khoa** (gửi GOI-XAC-NHAN) | xác nhận 5 ô disputed + nhân sự → nguồn ưu tiên cao nhất | dữ liệu nhân sự chưa chốt, chưa go-live thật được |
| **API key** (vào .env) | TIP-08 → TIP-09 proper → TIP-16; baseline chuyển từ diễn tập sang thật | phần diễn giải + học bổng/CV chưa grounded ở template |

## CỔNG ĐANG ĐÓNG (đúng roadmap, không tự mở)
- TIP-08 (key) · TIP-09 proper (key + văn bản Khoa) · TIP-15 (Render sống) ·
  TIP-16 vision (key + Khoa) · TIP-17 voice (telemetry) · TIP-12 G2 landing (duyệt G1).

## >>> QUYẾT ĐỊNH CẦN CHỦ THẦU CHỐT

**D-A. Món học bổng + CV nhân sự: chờ hay làm ngay?** (quan trọng nhất)
Dữ liệu v1.2 ĐÃ vào registry đúng, nhưng "Khoa có học bổng gì" / "cô Uyên học ở
đâu" vẫn NULL ở template mode vì composer fallback chỉ dựng từ ô có FIELD_RULE.
- Đường 1 (giữ cổng): chờ TIP-08, LLM đọc chunk → tự grounded, không thêm code.
- Đường 2 (follow-up deterministic, ~1 phiên, không cần key): thêm FIELD_RULE học
  bổng + PERSON_FIELDS cho CV, kèm golden case, đo delta. Grounded NGAY ở pilot,
  kịp mùa nhập học. Rủi ro thấp, đúng kiểu TIP-14.
→ Chủ thầu muốn "kịp mùa nhập học" mà key chưa chắc kịp: đề xuất **Đường 2**.

**D-B. Bảng ấn phẩm cho các câu đa giá trị khác?**
Điểm chuẩn đã thành bảng. Học phí VN/EN, so sánh chuyên ngành... hiện vẫn prose.
Có nên áp cùng kiểu bảng? (nhỏ, deterministic)

**D-C. Duyệt design TIP-12 giai đoạn 1?**
Đang treo. Duyệt thì mở giai đoạn 2 (landing + đồ thị SVG + /registry/meta). Không
cần key. Nếu chưa ưng chỗ nào thì chỉ, Thợ sửa trước khi sang G2.

**D-D. Thứ tự khi cổng mở**: khi key về, chạy TIP-08 trước (bật LLM, đo baseline
thật) rồi TIP-09 proper; khi Render sống, TIP-15. Xác nhận thứ tự này.

## ĐỀ XUẤT CỦA THỢ (nếu Chủ thầu muốn Thợ không đứng yên)
Trong lúc chờ ba quân: làm **D-A đường 2** (học bổng/CV grounded ngay, đo golden)
+ **D-B** (bảng cho học phí) + chờ **D-C** để mở G2. Cả ba deterministic, không
cần key, không giẫm ba việc trên bàn Chủ nhà. Nếu Chủ thầu giữ kỷ luật cổng thì
Thợ đứng yên tới khi một quân chạm bàn.
