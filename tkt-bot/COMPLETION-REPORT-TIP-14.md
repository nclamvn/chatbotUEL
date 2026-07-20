# COMPLETION REPORT — TKT-BOT · TIP-14 (Chịu lỗi chính tả và tiếng Việt không dấu)
Thợ (Claude Code) · 20/07/2026 · khế ước VISION-V2-ROADMAP.md (TIP-14)

## STATUS
DONE, đo trước sửa sau. Chạy tất định trên fallback, không cần key. Gate PASS:
core delta 0, typo 4/12 → 11/12. pytest 47/47.

## ĐO TRƯỚC (baseline code cũ, 42 câu = 30 core + 12 typo)
| | core | typo | overall |
|---|---|---|---|
| Baseline (trước sửa) | 27/30 | **4/12** | 0.738 |
| Sau TIP-14 | 27/30 | **11/12** | 0.905 |
| delta | 0 (đạt AC) | +7 | +0.167 |

registry_hit_recall 0.727→0.909, citation_coverage 0.727→0.909. GATE OK (mọi chỉ số ≥0).

## THAY ĐỔI
```
constitution.py   ABBREVIATIONS (data): tkte,hp,dc,cn,gv,sv,pt,ptdl,fi + mở rộng
retrieval.py      _lev (Levenshtein tự viết, FUZZY_MAX=2 hằng số kèm lý do),
                  _vocab (từ FIELD_RULES đã bỏ escape regex + alias + tên người +
                  token _detect_*), _expand_abbrev, _fuzzy_fix, _unknown_acronym;
                  structured_lookup + retrieve gọi lớp repair, anti-guess TRƯỚC fuzzy
scripts/eval_golden.py  status_by_group; TRUNCATE answer_cache đầu mỗi lần đo
data/golden.jsonl 12 câu typo (group=typo)
data/eval_baseline.json  baseline mới (post-fix) làm mốc cho TIP sau
tests/test_typo_v14.py   6 test (gồm anti-guess cntt)
```

## AC
- "diem chuan phan tich du lieu 2025" → trúng đúng ô như bản có dấu. PASS (norm fold + repair).
- "thay Le Hong Nhat con day ko" → grounded kèm ghi chú nghỉ hưu. PASS.
- "hoc phi cntt" → KHÔNG đoán bừa, honest-null. PASS + test. (cntt là chuỗi phụ âm
  không nguyên âm, không giải được → chặn cả structured lẫn chunk trước khi fuzzy
  co nhầm về "cn").
- harness 62 câu: core delta 0, typo ≥10/12. PASS (thực tế core 30 câu vì golden
  hiện 30, chưa mở rộng 50; typo 11/12).

## BÀI HỌC / BUG TỰ BẮT TRONG LÚC VERIFY
1. **Cache che kết quả:** answer_cache khóa theo registry_version, KHÔNG đổi khi
   CODE đổi → harness phục vụ câu cũ đã cache, che cải tiến. Fix: eval_golden
   TRUNCATE answer_cache đầu mỗi lần đo. (Quan trọng cho mọi eval sau này.)
2. **Vocab bẩn từ regex:** bóc [a-z]+ thẳng từ pattern FIELD_RULES biến "\\bemail\\b"
   thành "bemailb", "email" mất khỏi vocab → fuzzy nghiền "email" → email vỡ (core
   tụt 27→26). Fix: strip escape regex trước khi bóc từ.
3. **Fuzzy nghiền từ hợp lệ ngoài vocab:** "viet" (qualifier ngôn ngữ) không có
   trong vocab → bị sửa nhầm. Fix: bổ sung token _detect_* vào vocab.

## GHI CHÚ TRUNG THỰC
- "ma tuiển sinh" (typo còn lại, 11/12) CỐ Ý không sửa: "tuien" cách đều distance 1
  giữa "tuyen" VÀ "tien" → nhập nhằng → giữ nguyên đúng luật "nhập nhằng thì không
  đoán". Muốn 12/12 cần fuzzy có ngữ cảnh (bigram "tuyen sinh"), để dành nếu cần.
- Golden hiện 30 core (chưa phải 50): Chủ thầu chưa chốt mở rộng + 20 slot telemetry.
  Gate vẫn đúng bản chất (core không tụt, typo cải thiện dương).
- 3 miss core còn lại (DGNL, UTXTT, bóng đá) là phát hiện TIP-10 cũ, ngoài phạm vi
  TIP-14, không đổi.

## CÁCH CHẠY
`docker compose exec api python scripts/eval_golden.py --compare` (tự xóa cache, gate delta≥0).
