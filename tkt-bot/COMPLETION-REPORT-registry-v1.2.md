# COMPLETION REPORT — TKT-BOT · Nạp Registry v1.2 (phần deterministic của TIP-09)
Thợ (Claude Code) · 20/07/2026 · gói toan_kinh_te_uel_v1.2.zip (Chủ thầu)

## STATUS
DONE phần "loader nuốt". Deterministic, không cần key. 121 claims, 23 thực thể,
idempotent, không giẫm golden. Phần WIRING để dữ liệu mới GROUNDED trong template
mode (field rule học bổng, PERSON_FIELDS cho CV) chưa làm, thuộc TIP-09 proper
(cổng key) hoặc một follow-up deterministic nếu Chủ thầu cho phép (xem CÒN LẠI).

## ĐÃ NẠP
- claims.jsonl 121 (từ 110), 23 thực thể, đợt mới toàn tier A (+11). Byte-identical
  giữa toan_kinh_te_uel/ (nguồn) và tkt-bot/api/data/ (deploy).
- snapshots mới: tuyensinh-hoc-bong-2026.html + 4 CV (pdf) + 4 sidecar (.txt).
- domain.yaml thêm field: noi_dao_tao_tien_si, nam_ve_truong, chuyen_nganh_tien_si,
  hoc_bong_tien_phong_2026, hoc_bong_vuot_troi_2026 (universe.estimate giữ 23).

## VERIFY
| Hạng mục | Kết quả |
|---|---|
| /health claims_loaded | **121** · registry ba437255b63cc71d · mode template |
| Idempotent | load_data 2 lần: claims=121 entities=23 khớp |
| pytest | 47/47 (test_ingest 14→15) |
| Golden harness (42 câu) | core 27/30, typo 11/12, 0.905 — KHÔNG regression |
| Cells v1.2 trong registry | có: hoc_bong_*, noi_dao_tao_tien_si, nam_ve_truong... (sourced) |
| Sidecar CV | .txt/.pdf skip chunk (evidence-only), 15 HTML → 256 chunks |
| Privacy scrub | không có SĐT di động/CCCD/địa chỉ nhà; email institutional (uyenph@uel.edu.vn) |

## THAY ĐỔI LOADER (tối thiểu, cho loại snapshot mới)
- ingest_chunks: sidecar .txt và PDF nhị phân = evidence cho registry span gate,
  KHÔNG chunk hóa vòng này (defer TIP-09). missing_ref chỉ tính .html. Đây là
  thích ứng bắt buộc cho loại file mới (v1.1 chưa có PDF), không đổi logic build
  registry của load_data.
- Hằng số acceptance: smoke_test 110→121, test_ingest 14→15 snapshot HTML.

## CÒN LẠI — dữ liệu ĐÃ có nhưng chưa REACHABLE trong template mode
Đây là điểm trung thực quan trọng nhất của báo cáo:
- Composer fallback (template, chưa có key) chỉ dựng câu từ **ô registry** qua
  structured lookup, KHÔNG từ chunk. "Khoa có học bổng gì" hiện trả **null** vì:
  (a) chưa có FIELD_RULE map "học bổng" → ô hoc_bong_*, và (b) chunk chỉ được
  composer đọc khi LLM bật.
- CV học vấn ("cô Uyên học ở đâu về") cũng chưa reachable: field mới chưa nằm
  trong PERSON_FIELDS của person_lookup.
- Dữ liệu ĐÚNG và ĐỦ trong registry (đã kiểm). Reachability cần một trong hai:
  1. **TIP-08 (key):** composer LLM đọc chunk hoc-bong + ô CV → grounded, không
     cần thêm code. Đúng tinh thần "loader nuốt, wiring để TIP-09".
  2. **Follow-up deterministic (nếu Chủ thầu mở cổng):** thêm FIELD_RULE học bổng
     + PERSON_FIELDS cho CV, kèm 2-3 golden case, đo delta — kiểu TIP-14, không
     cần key, grounded ngay trong pilot template. ~1 phiên nhỏ.
- Thợ KHÔNG tự thêm wiring (ngoài phạm vi "loader nuốt" + là việc TIP-09 proper).
  Chờ Chủ thầu quyết đường 1 hay 2.

## PHÂN VAI / DEFERRED (TIP-09 proper, cổng key)
6 CV còn lại (có cv-le-thanh-hoa on-disk, chưa claim) + trang công bố khoa học,
chunk hóa CV/publications, và wiring reachability — để dành vòng chính thức.
