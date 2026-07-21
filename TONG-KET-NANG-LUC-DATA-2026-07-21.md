# Tổng kết năng lực & dữ liệu — TKT-BOT (Chatbot Khoa Toán Kinh tế UEL)

> **Tài liệu gốc của dự án · Phiên bản 1.0** — phê chuẩn 21/07/2026.
> Ba đời sống: (1) kịch bản demo (mục 4.3 + 5 + 8), (2) phụ lục kỹ thuật đính kèm email Khoa, (3) khung bản chào nhân bản (mục 2–7, đổi tên & số).
>
> Chốt ngày **21/07/2026**, sau commit `d40d118` (registry v1.3).
> Trạng thái: **đóng băng ổn định** — bản build tốt nhất dự án từng có, chờ 3 cửa (Render / email Khoa / API key) mà chỉ Human mở được.
> Số liệu dưới đây **rút sống** từ registry + code + hệ đang chạy, không viết từ trí nhớ.

---

## 1. Một dòng trạng thái

Chatbot hỏi–đáp về Khoa Toán Kinh tế UEL, **grounded từng con số vào bằng chứng verbatim**, đang chạy chế độ `template` (chưa gắn API key) với **139 claim** phủ tuyển sinh 2025–2026 + hồ sơ 17 giảng viên. Chất lượng đo được: golden **0.945**, smoke **12/12**.

---

## 2. Kiến trúc & hạ tầng

| Thành phần | Công nghệ | Cổng | Trạng thái |
|---|---|---|---|
| Web (UI chat) | Next.js 15 | `3002` (trực tiếp), **`8080` qua Caddy** | Up |
| API | FastAPI | `8000` | Up (bản 139) |
| DB | Postgres 16 + pgvector | `5453→5432` | Up (healthy) |
| Reverse proxy | Caddy 2 | `8080` | Up |

- Chạy: `DB_HOST_PORT=5453 docker compose up -d --build` trong `tkt-bot/`.
- **Link UI local: http://localhost:8080** (đường production, proxy `/api` sẵn, gate tắt ở local).
- Engine tinh lọc dữ liệu (`toan_kinh_te_uel/refinery.py`) **domain-agnostic**, tách khỏi app phục vụ; app nạp bản sao đã đóng băng ở `tkt-bot/api/data/`.

---

## 3. Dữ liệu hiện tại (Registry v1.3)

**139 claim · 23 thực thể · 46 field schema · 41 snapshot · digest `a3ea65c1`** (idempotent + auditor OK, hai đường kiểm độc lập).

### 3.1 Thực thể (23)
| Loại | Số | Gồm |
|---|---|---|
| `nhan_su` (giảng viên) | 17 | Hồ sơ CV: chức vụ, học hàm/học vị, chuyên môn, nơi đào tạo tiến sĩ, năm về trường… |
| `chuyen_nganh` | 3 | Toán ứng dụng KT-QT-TC, bản Tiếng Anh, Phân tích dữ liệu |
| `nganh` / `don_vi` / `truong` | 1 + 1 + 1 | Ngành Toán kinh tế, Khoa Toán Kinh tế, Trường ĐH Kinh tế–Luật |

### 3.2 Độ tin cậy nguồn (tier)
| Tier | Số | Ý nghĩa |
|---|---|---|
| A | 98 | Nguồn chính hãng — **98/98 đều first-party** `*.uel.edu.vn` (maths 91 · tuyensinh 6 · uel 1). Không claim tier-A nào trỏ ngoài UEL. |
| B | 7 | Nguồn thứ ba mạnh, có snapshot + span |
| C | 34 | Nguồn tham khảo (điểm chuẩn ts247, báo chí), có snapshot + span |

> *Ghi chú hai trục đo, để không lẫn:* con số **98/98** đo trục **first-party** (nguồn có phải tên miền UEL không). Nếu đo theo trục **loại snapshot**, 98 claim tier-A gồm **83 tựa trang web `.html` + 15 tựa sidecar CV `.txt`** (lý lịch KH đăng trên site Khoa) — cả hai đều first-party. (Số 41 ở mục 3 là số *file* snapshot; nhiều claim dùng chung một file, nên claim-count > file-count.)

**Mọi claim (kể cả A) đều mang snapshot + `evidence_span` verbatim** — 139/139, hai đường kiểm (engine fail-loud + verifier độc lập) cùng xác nhận 0 span-not-found.

### 3.3 Nguồn dữ liệu
`maths.uel.edu.vn` (91) · `diemthi.tuyensinh247.com` (29) · `plo.vn`/tuoitre (7) · `tuyensinh.uel.edu.vn` (6) · `huongnghiep.hocmai.vn` (5) · `uel.edu.vn` (1).

### 3.4 Phủ nội dung
- **Điểm chuẩn 2025 đủ 5 phương thức**: THPT (A00/A01, D01/D07/X25/X26), ĐGNL, ƯTXTT (ưu tiên xét tuyển thẳng), **ƯTXT danh sách 149 trường**, **SAT**.
- **Tuyển sinh 2026**: chỉ tiêu (theo chuyên ngành), phương thức xét tuyển.
- **Học phí** 2025–2026 (chương trình tiếng Việt / tiếng Anh).
- **Học bổng 2026**: Tiên phong, Vượt trội.
- **Mã tuyển sinh / mã trường / tín chỉ / học kỳ**.
- **Thông tin đơn vị**: lịch sử thành lập, định hướng nghiên cứu, triết lý, tầm nhìn, địa chỉ, email, điện thoại, bộ môn.
- **Hồ sơ 17 giảng viên**: học vấn tiến sĩ, chuyên môn, chức vụ, email (10 GV).

---

## 4. Khả năng trả lời (chế độ template hiện tại — không cần LLM)

App có **27 FIELD_RULES** cho tra cứu có cấu trúc (deterministic), phủ toàn bộ nội dung mục 3.4. Điểm mạnh nằm ở **cách xử lý biên**, không chỉ ở "trả được số":

### 4.1 Tra cứu có cấu trúc
- Nhận diện field theo câu hỏi + thực thể; câu về điểm/mã tự mở ra 3 chuyên ngành.
- **Bảng điểm ấn phẩm đa chuyên ngành** khi đủ ma trận (≥4 ô), thay vì lặp N câu.
- **Lọc theo năm** (`_year_filter`): hỏi "chỉ tiêu 2026" trả đúng ô 2026 (cấp chuyên ngành), không kéo nhầm 2025.

### 4.2 Nhân sự (17 GV) — hỏi bằng ngôn ngữ thật
- Gọi theo **tên riêng + kính ngữ** ("cô Uyên", "thầy Sơn") — khớp từ cuối tên.
- **Nhắm đúng khía cạnh CV** (học ở đâu / chuyên ngành TS / về trường năm nào / học vị) thay vì đổ cả hồ sơ.
- Tìm người theo **chức vụ** ("trưởng khoa là ai").

### 4.3 Hai loại nhập nhằng — xử khác nhau theo luật
| Kiểu | Ví dụ | Cách xử |
|---|---|---|
| **Hai đáp án đều đúng** | "điểm ưu tiên xét tuyển" (ƯTXTT vs 149) | **Trình CẢ HAI ô**, mỗi ô một citation |
| **Không đáp án nào chắc** | "cô Uyên" (3 người trùng tên) | **Hỏi lại** đúng người, không đoán |
| Viết tắt lạ chưa giải | "cntt" | Chặn đoán → honest-null |

### 4.4 Chịu lỗi đầu vào
- Sai chính tả (Levenshtein tự viết, ngưỡng 2), **viết tắt** (`tkte`, `hp`, `dc`, `cn`, `ptdl`…), **không dấu**.
- **Anti-guess**: viết tắt lạ chặn *trước* fuzzy để không co bừa.

### 4.5 honest-null (thà trống còn hơn sai)
- Hỏi năm không có dữ liệu (điểm 2024) → null có lý do.
- Hỏi ngoài phạm vi (bóng đá, đầu tư coin) → OOS.
- Số/tên không neo được vào bằng chứng → không hiển thị.

---

## 5. Kỷ luật bằng chứng (điểm khác biệt cốt lõi)

- **Mỗi con số ↔ một `evidence_span` verbatim** nằm trong snapshot raw đã lưu; sai một ký tự → gate cắn, build dừng (`SPAN_NOT_FOUND`).
- **7 cổng fail-loud** trong engine: SOURCED_ATTR, CAPTURE_MISSING, SPAN_NOT_FOUND, AMBIGUOUS_MERGE_UNFLAGGED, DISTRIBUTION_NO_DENOMINATOR, IDEMPOTENT, và các cổng domain-gates (origin/no-inferred…).
- **Verifier trace** ở tầng trả lời: tách hai tập allowed, chỉ đối chiếu value + span + text chunk; tên nguồn/snapshot mask khỏi câu trả lời trước khi bóc số.
- **EvidenceSheet "Hồ sơ bằng chứng"** trên UI: chip tier + URL nguồn link sống + đoạn trích cho từng ô.
- **Build tất định** (idempotent, digest cố định); auditor re-derive độc lập với builder.

---

## 6. Chất lượng đo được

| Bộ đo | Kết quả |
|---|---|
| **Golden set** (55 câu, đường fallback) | status_accuracy **0.945** · recall 0.955 · citation_coverage 0.955 |
| Theo nhóm | core 28/30 · typo 11/12 · tip18 6/6 · v13 3/3 · v19 4/4 |
| **Smoke** (12 câu, qua HTTP + rate limit thật) | **12/12 PASS** · P95 0.07s |
| Gate kỷ luật | `--compare` delta ≥ 0 (tuần này +0.022, **0 regression**) |
| pytest | 58/58 (phiên gần nhất) |

**3 MISS còn lại — đều pre-existing, có tên có lý do**: (1) ĐGNL chuyên ngành PTDL (gap regex), (2) "ma tuiển sinh" (typo nhập nhằng tuyển/tiên, cố ý không sửa), (3) dự đoán bóng đá (router heuristic, fix khi có LLM).

---

## 7. Bảo mật & vận hành (đã hardening — TIP-11/13)

- **Rate limit** theo IP: 10 req/phút, 100 req/giờ (đọc `X-Forwarded-For` sau Caddy). **Không có cửa sau** — smoke tự giãn nhịp 7s/req thay vì nới rào.
- Cap câu hỏi 500 ký tự → 422.
- **CORS** đóng mặc định (deny), mở theo `CORS_ORIGINS`.
- **Log JSON có cấu trúc** + `request_id` xuyên 4 tầng.
- **Staging gate**: basic auth + `noindex` + `robots.txt`; `/admin` telemetry riêng.
- Feedback bar → telemetry; endpoint `/telemetry/nulls` để soạn câu đo.
- **API**: `/health`, `/chat`, `/chat/stream`, `/telemetry`, `/telemetry/nulls`, `/telemetry/stats`, `/admin`.

---

## 8. Giới hạn hiện tại (trung thực)

- **Đang chạy `MODE=template`** — chưa gắn `ANTHROPIC_API_KEY`. Câu trả lời hiện dựng từ template deterministic trên ô structured; **composer LLM (diễn đạt tự nhiên, đọc chunk văn bản dài) chưa bật**. `LLM_ENABLED` là authoritative (khóa LLM dù key về nếu `MODE=template`).
- Một số dữ liệu đã vào registry nhưng chỉ **reachable qua LLM** (đọc chunk), ví dụ mô tả học bổng dài — bản template chỉ trả ô có FIELD_RULE.
- `diem_sat_2025` / `diem_utxt149_2025` đã wiring + có golden; các field CV sâu hơn phủ dần theo nhu cầu.
- Con số golden đo trên **đường fallback**, chưa phải số production sau khi bật LLM.

---

## 9. Ba cửa mở giá trị mới (chỉ Human)

| Cửa | Mở ra |
|---|---|
| **Render** (provision + secret + `CREATE EXTENSION vector`) | Link staging gửi được → điền vào email Khoa |
| **Email `khoatkt@uel.edu.vn`** | Khoa xác nhận nhân sự → thành đối tác dữ liệu |
| **`ANTHROPIC_API_KEY`** (+ spend limit) | Bật composer LLM → số diễn tập thành số production, mở TIP-08/09/10 phần còn lại |

Sản phẩm đã thôi cần thêm code. Nó chỉ còn cần được **nhìn thấy**.

---
*Tài liệu gốc v1.0 · sinh từ trạng thái thực: registry commit `d40d118` · digest `a3ea65c1` · `claims_loaded=139` · tier-A 98/98 first-party.*
