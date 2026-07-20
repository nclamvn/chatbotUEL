# COMPLETION REPORT — TKT-BOT · TIP-10 phần 1 (Golden-set eval harness)
Thợ (Claude Code) · 20/07/2026 · theo plan đã duyệt (đo trước chỉnh sau)

## STATUS
DONE thước đo. Đây là bước "đo trước" — CHỈ dựng harness, KHÔNG sửa retrieval.
Baseline chạy trên đường fallback (chưa có key), là cổng delta cho mọi tinh chỉnh
RAG về sau. Con số composer Claude thật lấy khi chạy lại sau TIP-08.

## FILES
```
api/data/golden.jsonl        30 case đề xuất (Chủ thầu chốt), data-driven
api/scripts/eval_golden.py   một lệnh: status accuracy, registry-hit recall,
                             citation coverage, P50/P95; --compare (delta gate);
                             --show-nulls (nguồn 20 câu telemetry)
api/data/eval_baseline.json  baseline tham chiếu (commit để gate xuyên phiên)
```

## BASELINE (fallback path, n=30)
| Chỉ số | Giá trị |
|---|---|
| status_accuracy | **0.90** (27/30) |
| — grounded | 16/18 |
| — disputed | 4/4 |
| — null | 4/4 |
| — oos | 3/4 |
| registry_hit_recall | 0.909 |
| citation_coverage | 0.909 |
| latency P50 / P95 | 33ms / 89ms (fallback, không phải số production) |

`--compare` chạy lại: delta +0.0 mọi chỉ số → GATE OK.

## 3 MISS — đều là phát hiện thật (harness làm đúng việc)
1. **"Điểm đánh giá năng lực chuyên ngành Phân tích dữ liệu 2025?"** → kỳ vọng
   grounded, ra null. Gap thật: FIELD_RULES của diem chỉ khớp "điểm chuẩn / trúng
   tuyển / ngưỡng...", KHÔNG khớp "điểm đánh giá năng lực" → structured trả rỗng.
   Ô `diem_dgnl_2025` có dữ liệu nhưng không tới được.
2. **"Điểm ưu tiên xét tuyển thẳng chương trình tiếng Anh 2025?"** → cùng gap:
   "điểm ưu tiên xét tuyển" không khớp regex diem → null. Ô `diem_utxtt_2025` có.
3. **"Dự đoán tỉ số bóng đá tối nay?"** → kỳ vọng oos, ra null. Router heuristic
   (fallback) không bắt được; kỳ vọng cải thiện khi bật LLM router (TIP-08).

Hai miss (1)(2) là ứng viên số 1 cho bước tinh chỉnh có đo kế tiếp (query rewrite
hoặc mở FIELD_RULES / alias). "Học bổng" trong null-backlog thật (6x) là coverage
gap dữ liệu, đẩy sang TIP-09.

## PHÂN VAI / VIỆC TREO
- 30 golden case là **bản đề xuất**, Chủ thầu chốt (đặc biệt case "Trưởng Khoa +
  học hàm": chuc_vu grounded nhưng hoc_ham disputed → hiện gán disputed, cần chốt).
- 20 slot telemetry: `--show-nulls` đã liệt kê 10 câu null thật tích trong phiên
  (lẫn nhiễu test), đổ đầy sau khi mở cho người dùng thật.

## KỶ LUẬT (đúng plan đã duyệt)
- Không đụng contract, không sửa retrieval trong bước này.
- Mọi thay đổi retrieval sau (query rewrite, multi-cell, reranker) BẮT BUỘC kèm
  `eval_golden.py --compare`, delta ≥ 0 trên cả ba chỉ số mới được merge. Cảm giác
  "có vẻ tốt hơn" không phải bằng chứng.

## CÁCH CHẠY
Trong container api (files có trong repo, rebuild api để bake vào image):
```
docker compose exec api python scripts/eval_golden.py            # ghi baseline
docker compose exec api python scripts/eval_golden.py --compare  # gate delta>=0
docker compose exec api python scripts/eval_golden.py --show-nulls
```
