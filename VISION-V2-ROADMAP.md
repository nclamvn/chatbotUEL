# VISION-V2 — TKT-BOT sản phẩm thật · Roadmap có cổng
Chủ thầu soạn 20/07/2026, Human phê duyệt triển khai lần lượt.
Nguyên tắc xuyên suốt: mỗi năng lực mới đi qua ba cổng như mọi thứ trước nó: golden set đo được, verifier có răng, trạng thái trung thực. Thứ tự phát: TIP-14 ngay, TIP-15 khi staging Render sống, TIP-16 khi key về và Khoa thành đối tác có văn bản, TIP-17 khi telemetry chứng minh nhu cầu.

═══════════════════════════════════════════════════════════════

# TIP-14: Chịu lỗi chính tả và tiếng Việt không dấu

## HEADER
- TIP-ID: TIP-14 · Module: api/retrieval · Depends on: TIP-10 phần 1 (harness đã có) · Priority: P0
- Điều kiện phát: không có, chạy được trên fallback ngay hôm nay · Effort: ~1 phiên

## TASK
1. Bổ sung 12 câu typo vào golden.jsonl trước khi sửa một dòng code nào: không dấu ("diem chuan phan tich du lieu"), sai phụ âm ("hoc fi", "chuiên ngành"), viết tắt phổ biến ("tktế", "pt dữ liệu", "đc 2025"), tên người thiếu dấu ("thay Le Hong Nhat"). Chạy harness lấy baseline typo trên code hiện tại, ghi số trước.
2. Lớp chuẩn hóa truy vấn trong structured lookup: fold không dấu (NFD strip diacritics) chạy song song bản có dấu, cả hai cùng đổ vào bảng regex hiện có ở dạng đã fold.
3. Fuzzy match tên thực thể và alias field: edit distance có trọng số trên 23 entity cộng bảng alias, ngưỡng chặt (distance ≤ 2 và không nhập nhằng giữa hai ứng viên, nhập nhằng thì hỏi lại thay vì đoán). Tên người ưu tiên match theo token cuối vì người Việt gọi bằng tên.
4. Bảng viết tắt khai báo trong constitution dạng data, không rải trong code: tktế, đc, hp, cn, gv cùng nhãn mở rộng.
5. Chạy lại harness đủ 62 câu (50 cũ cộng 12 typo), gate delta không âm trên nhóm cũ và cải thiện dương trên nhóm typo.

## ACCEPTANCE CRITERIA
- Given "diem chuan phan tich du lieu 2025", When structured lookup, Then trúng đúng ô như bản có dấu.
- Given "thay Le Hong Nhat con day ko", When /chat, Then trả grounded kèm ghi chú nghỉ hưu.
- Given "học phí cntt" (chuyên ngành không tồn tại, viết tắt nhập nhằng), When lookup, Then không đoán bừa, trả câu hỏi làm rõ hoặc honest-null, có test.
- Given harness 62 câu, Then nhóm 50 câu cũ delta bằng 0, nhóm 12 typo từ baseline lên tối thiểu 10/12 đúng trạng thái.

## CONSTRAINTS
- Không thêm thư viện fuzzy nặng, tự viết edit distance hoặc dùng difflib chuẩn.
- Ngưỡng fuzzy là hằng số khai một chỗ kèm chú thích lý do chọn.

═══════════════════════════════════════════════════════════════

# TIP-15: Load test và van xả quy mô

## HEADER
- TIP-ID: TIP-15 · Module: infra · Depends on: TIP-13 D6 đóng (staging Render sống)
- Điều kiện phát: Human đã provision Render · Priority: P0 trước go-live công khai

## TASK
1. Kịch bản load test bằng k6 hoặc locust mô phỏng ngày công bố điểm: 80 phần trăm lưu lượng rơi vào 20 câu factual lặp lại, 20 phần trăm câu đuôi dài, ramp 0 lên 500 người đồng thời trong 10 phút, giữ 15 phút.
2. Đo và ghi: P50 P95 P99, tỉ lệ cache hit, tỉ lệ 429, hành vi DB connection. Tìm điểm gãy đầu tiên và gọi tên nó.
3. Vá theo số đo, không vá theo phỏng đoán: connection pool Postgres, cache warm 20 câu mùa vụ lúc khởi động, static asset qua CDN của Render.
4. Van xả tải cho tương lai LLM: thiết kế degrade mode, khi hàng đợi LLM vượt ngưỡng thì câu factual phục vụ bằng template (vốn là đường D0), câu diễn giải trả thông báo đợi tử tế kèm gợi ý câu factual. Cắm cờ sẵn, bật thật ở TIP-08 trở đi.

## ACCEPTANCE CRITERIA
- Given 500 người đồng thời hồ sơ 80/20, Then P95 câu factual dưới 2 giây, không lỗi 5xx, cache hit trên 70 phần trăm.
- Given DB bị ép quá pool, Then request xếp hàng hoặc 429, không sập container.
- Given degrade mode bật tay, Then câu factual vẫn grounded kèm citation, câu diễn giải nhận thông báo đợi.

═══════════════════════════════════════════════════════════════

# TIP-16: Đối chiếu ảnh thông báo công khai

## HEADER
- TIP-ID: TIP-16 · Module: api/vision · Depends on: TIP-08 DONE (cần Claude vision), văn bản đồng ý phạm vi từ Khoa
- Điều kiện phát: cả hai điều kiện trên có bằng chứng trong Decisions Log · Priority: P1

## TASK
1. Cửa nhận ảnh trên UI: người dùng tải ảnh một thông báo, hệ đọc bằng Claude vision, bóc các trường khẳng định được (ngày, số hiệu, đơn vị ban hành, mốc thời gian, con số).
2. Đối chiếu từng trường với registry và corpus: khớp thì grounded kèm citation về nguồn gốc, lệch thì disputed trình cả hai phía, không có gì đối chiếu được thì honest-null nói thẳng hệ không xác nhận được thật giả và chỉ kênh chính thức.
3. Phạm vi cứng khai trong constitution: chỉ nhận tài liệu công khai của Trường và Khoa. Ảnh chứa dữ liệu cá nhân (thẻ sinh viên, CCCD, bảng điểm cá nhân, ảnh chân dung) bị từ chối xử lý ngay tại cửa bằng thông điệp giải thích, ảnh không lưu, không log nội dung, chỉ log sự kiện từ chối không kèm ảnh.
4. Verifier mở rộng: mọi con số hệ nói về ảnh phải hoặc nằm trong ảnh (trích thị giác) hoặc nằm trong registry (đối chiếu), gắn nhãn nguồn gốc rõ hai loại.

## ACCEPTANCE CRITERIA
- Given ảnh thông báo thật của Trường có trong corpus, Then các trường khớp trả grounded kèm citation.
- Given ảnh thông báo bịa số liệu, Then các trường lệch hiện disputed nêu đúng chỗ lệch, không kết luận "giả" vượt bằng chứng.
- Given ảnh thẻ sinh viên, Then từ chối tại cửa, không request vision nào được gọi, có test.
- Given cùng một ảnh gửi hai lần, Then không tồn tại bản lưu nào trên đĩa sau phiên, chứng minh bằng kiểm thư mục.

## CONSTRAINTS
- Thẻ sinh viên và mọi giấy tờ cá nhân nằm ngoài phạm vi TIP này vĩnh viễn, muốn làm phải có TIP riêng kèm thiết kế privacy được Human và Khoa duyệt bằng văn bản.

═══════════════════════════════════════════════════════════════

# TIP-17: Cửa vào bằng giọng nói ba miền

## HEADER
- TIP-ID: TIP-17 · Module: api/voice · Depends on: go-live ổn định, telemetry chứng minh nhu cầu (mốc gợi ý: trên 15 phần trăm phiên từ người dùng trên 45 tuổi hoặc yêu cầu trực tiếp từ Khoa)
- Điều kiện phát: Human quyết sau khi xem số · Priority: P2

## TASK
Kiến trúc cửa vào, không đụng lõi: audio thu trên client, ASR bằng PhoWhisper self-host hoặc API thương mại (quyết theo chi phí lúc đó), text đổ vào pipeline hiện hành như một câu gõ tay. Hiển thị transcript cho người dùng sửa trước khi gửi, đây là chốt chất lượng quan trọng nhất với giọng vùng miền: người nói tự xác nhận máy nghe đúng chưa thay vì hệ đoán. Golden set thêm nhánh audio: 30 mẫu ba miền đọc 10 câu chuẩn, đo tỉ lệ transcript ra đúng ô registry sau khi qua pipeline.

## ACCEPTANCE CRITERIA
- Given mẫu giọng Quảng đọc "điểm chuẩn phân tích dữ liệu", Then transcript hiển thị cho người dùng xác nhận và sau xác nhận trả đúng ô như bản gõ tay.
- Given môi trường ồn transcript vỡ, Then hệ đề nghị gõ tay thay vì đoán, không có đường nào từ audio thẳng ra câu trả lời bỏ qua bước người dùng thấy transcript.

═══════════════════════════════════════════════════════════════

## Nhật ký cổng (Chủ thầu giữ)
- TIP-14: PHÁT ngay hôm nay.
- TIP-15: chờ bằng chứng staging sống (URL cộng smoke từ ngoài).
- TIP-16: chờ key cộng văn bản Khoa, hai điều kiện đều phải nằm trong Decisions Log.
- TIP-17: chờ số telemetry sau go-live, Human quyết.
