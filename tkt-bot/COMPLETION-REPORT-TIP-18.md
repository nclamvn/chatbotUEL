# COMPLETION REPORT — TKT-BOT · TIP-18 (Reachability học bổng + CV) + D-B (TABLE_MIN)
Thợ (Claude Code) · 20/07/2026 khuya · D-A đường 2 (Chủ thầu chốt)

## GHI CHÚ ĐỒNG BỘ HỒ SƠ
Registry v1.2 (commit c0c5acf) là NGUYÊN LIỆU (data). Phần WIRING reachability tôi
cố ý hoãn chờ quyết D-A, nay về đúng mã TIP-18. Không "một việc hai tên": v1.2 =
tiền đề, TIP-18 = làm dữ liệu đó GROUNDED ở template mode, không cần key.

## STATUS
DONE, deterministic, đo trước sửa sau. Gate PASS. pytest 47/47.

| | pre-TIP-18 | sau | delta |
|---|---|---|---|
| tip18 (6 câu) | 2/6 | **6/6** | +4 |
| core (30) | 27/30 | 27/30 | 0 |
| typo (12) | 11/12 | 11/12 | 0 |
| overall | 0.833 | **0.917** | +0.084 |

## TIP-18 (D-A đường 2)
- **FIELD_RULE học bổng** → ô hoc_bong_tien_phong_2026 + hoc_bong_vuot_troi_2026
  (year-bound). "Khoa có học bổng gì" giờ GROUNDED ở template, kịp mùa nhập học.
- **PERSON_FIELDS + PERSON_TOPIC**: thêm field CV (noi_dao_tao_tien_si,
  chuyen_nganh_tien_si, nam_ve_truong, hoc_vi_nam_dat, bo_mon). Câu nhắm đúng khía
  cạnh trả ĐÚNG field đó, KHÔNG dump cả người, nên "cô Uyên học tiến sĩ ở đâu"
  grounded chứ không bị ô hoc_ham disputed của cô kéo thành disputed.
- **BẪY thạc sĩ**: học bổng dữ liệu chỉ bậc đại học. Hỏi "học bổng thạc sĩ 2026"
  → honest-null, không đoán bừa học bổng đại học. Verify: status null.
- **FIELD_LABELS** tiếng Việt cho mọi field mới (render không lộ tên field thô).

## D-B (TABLE_MIN)
- Hằng số **TABLE_MIN = 4** khai trong constitution dạng data, kèm nguyên tắc:
  "bảng phục vụ so sánh hai chiều, prose phục vụ thông báo". Bảng chỉ khi >= 4 ô
  cùng nhóm (ma trận thật). Điểm chuẩn 3 chuyên ngành (6 ô) → bảng; học phí Việt/Anh
  (một cặp) → giữ prose, một câu hai citation.

## BÀI HỌC (nối chuỗi TIP-14)
Bẫy thạc sĩ trượt vòng đầu vì "thac" không có trong vocab → _fuzzy_fix nghiền mất
"thac si". Fix: soi marker bẫy trên q1 (TRƯỚC fuzzy), như anti-guess acronym; thêm
thac/cao/sau/dai vào vocab phòng thủ. Cùng họ với bug email/viet của TIP-14: fuzzy
nghiền từ hợp lệ ngoài vocab — nay có ba lớp chắn (q1 pre-fuzzy cho marker, vocab
đủ, ngưỡng chặt).

## CÁCH CHẠY
`docker compose exec api python scripts/eval_golden.py --compare` (tự xóa cache, gate).

## CÒN LẠI
- "Cô Uyên" gọi tắt bằng tên vẫn nhập nhằng (2 người tên Uyên): golden dùng tên đầy
  đủ. Match theo token cuối + disambiguation để dành (cần khi telemetry cho thấy nhu cầu).
- D-C: chờ chữ "Duyệt" của Human để mở TIP-12 giai đoạn 2.
