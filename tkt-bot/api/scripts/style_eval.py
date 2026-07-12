"""TIP-08 đầu việc 3: bộ eval văn phong.

Đọc eval-questions.txt, mỗi câu chạy qua answer_pipeline (trong container nên
thấy đủ meta: rewrites, style_fallback), rồi soi lại answer_markdown bằng
style_lint. Chạy:
    docker compose run --rm -v $PWD/eval-questions.txt:/srv/api/eval-questions.txt \
        api python scripts/style_eval.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.pipeline import answer_pipeline  # noqa: E402
from app.style_lint import hard_violations, lint  # noqa: E402

QUESTIONS_FILE = os.environ.get("EVAL_FILE", "/srv/api/eval-questions.txt")


def main() -> None:
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        questions = [ln.strip() for ln in f
                     if ln.strip() and not ln.strip().startswith("#")]

    rows, total_hard, total_soft, total_rewrites, total_fallback = [], 0, 0, 0, 0
    for i, q in enumerate(questions, 1):
        answer, meta = answer_pipeline(q)
        violations = lint(answer["answer_markdown"])
        hard = hard_violations(violations)
        soft = [v for v in violations if v["severity"] == "soft"]
        total_hard += len(hard)
        total_soft += len(soft)
        total_rewrites += meta["rewrites"]
        total_fallback += int(meta["style_fallback"])
        rows.append((i, q, answer["status"], meta["rewrites"],
                     meta["style_fallback"], len(hard), len(soft)))
        print(f"[{i:02d}] [{answer['status']:9s}] rewrites={meta['rewrites']} "
              f"fallback={meta['style_fallback']} hard={len(hard)} soft={len(soft)}  {q}")
        for v in hard:
            print(f"      !! HARD LỌT RA RENDER: {v}")
        for v in soft:
            print(f"      ~  {v['code']}: {v['detail']}")

    print("\n== TỔNG KẾT ==")
    print(f"câu: {len(questions)} · vi phạm cứng lọt ra render: {total_hard}"
          f" · warning mềm: {total_soft}")
    print(f"vòng viết lại đã kích hoạt: {total_rewrites}"
          f" · safe fallback: {total_fallback}")
    by_status = {}
    for r in rows:
        by_status[r[2]] = by_status.get(r[2], 0) + 1
    print(f"phân bố status: {by_status}")
    if total_hard:
        sys.exit(1)


if __name__ == "__main__":
    main()
