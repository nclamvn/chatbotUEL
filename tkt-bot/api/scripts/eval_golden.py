"""Golden-set eval harness (TIP-10 phần 1, "đo trước chỉnh sau").

Một lệnh, ba chỉ số + độ trễ:
- status_accuracy: trạng thái dự đoán khớp expect_status.
- registry_hit_recall: structured_lookup có trả đúng ô kỳ vọng không (recall trên expect_cells).
- citation_coverage: claim được trích có phủ ô kỳ vọng không.

Cách chạy (trong container api):
  python scripts/eval_golden.py            # chạy + ghi eval_baseline.json
  python scripts/eval_golden.py --compare  # chạy lại, diff baseline, GATE delta>=0
  python scripts/eval_golden.py --show-nulls  # in null-backlog thật để soạn 20 câu telemetry

Lưu ý: chạy trên đường fallback đo retrieval + template, CHƯA đo composer Claude.
Con số production lấy khi chạy lại sau TIP-08 (có ANTHROPIC_API_KEY).
"""
import json
import math
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # cho phép import app/

from app.pipeline import answer_pipeline
from app.retrieval import structured_lookup
from app.db import connect
from app import telemetry

DATA = Path(__file__).resolve().parent.parent / "data"
GOLDEN = DATA / "golden.jsonl"
BASELINE = DATA / "eval_baseline.json"
HEADLINE = ("status_accuracy", "registry_hit_recall", "citation_coverage")


def load_golden() -> list[dict]:
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    return [json.loads(x) for x in lines if x.strip()]


def cells_of_claims(claim_ids: list[str]) -> set[tuple[str, str]]:
    if not claim_ids:
        return set()
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT entity, field FROM claims WHERE claim_id = ANY(%s)",
                    ([str(x) for x in claim_ids],))
        return {(r["entity"], r["field"]) for r in cur.fetchall()}


def structured_cells(question: str) -> set[tuple[str, str]]:
    return {(c["entity"], c["field"]) for c in structured_lookup(question)}


def p95(vals: list[float]) -> float:
    if not vals:
        return 0.0
    idx = max(0, math.ceil(0.95 * len(vals)) - 1)
    return round(sorted(vals)[idx], 1)


def run() -> tuple[dict, list[dict]]:
    golden = load_golden()
    # cache theo registry_version không đổi khi CODE đổi; xóa để đo mã mới, không
    # phục vụ câu trả lời cũ đã cache (bài học TIP-14).
    with connect() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE answer_cache")
        conn.commit()
    per, lat = [], []
    for g in golden:
        t = time.perf_counter()
        answer, _meta = answer_pipeline(g["question"])
        dt = (time.perf_counter() - t) * 1000
        lat.append(dt)
        exp = {tuple(c) for c in g.get("expect_cells", [])}
        cited = cells_of_claims([c["claim_id"] for c in answer.get("citations", [])])
        got = structured_cells(g["question"])
        per.append({
            "q": g["question"],
            "group": g.get("group", "core"),
            "expect": g["expect_status"],
            "pred": answer["status"],
            "status_ok": answer["status"] == g["expect_status"],
            "cell_recall": (len(exp & got) / len(exp)) if exp else None,
            "cite_coverage": (len(exp & cited) / len(exp)) if exp else None,
            "ms": round(dt, 1),
        })

    by: dict[str, list[int]] = {}
    for p in per:
        by.setdefault(p["expect"], [0, 0])
        by[p["expect"]][0] += int(p["status_ok"])
        by[p["expect"]][1] += 1
    grp: dict[str, list[int]] = {}
    for p in per:
        grp.setdefault(p["group"], [0, 0])
        grp[p["group"]][0] += int(p["status_ok"])
        grp[p["group"]][1] += 1
    recs = [p["cell_recall"] for p in per if p["cell_recall"] is not None]
    covs = [p["cite_coverage"] for p in per if p["cite_coverage"] is not None]
    metrics = {
        "n": len(per),
        "status_accuracy": round(sum(p["status_ok"] for p in per) / len(per), 3),
        "status_by_class": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by.items())},
        "status_by_group": {k: f"{v[0]}/{v[1]}" for k, v in sorted(grp.items())},
        "registry_hit_recall": round(statistics.mean(recs), 3) if recs else None,
        "citation_coverage": round(statistics.mean(covs), 3) if covs else None,
        "latency_p50_ms": round(statistics.median(lat), 1) if lat else 0.0,
        "latency_p95_ms": p95(lat),
    }
    return metrics, per


def main() -> None:
    if "--show-nulls" in sys.argv:
        rows = telemetry.null_backlog(limit=20)
        print(f"== null-backlog thật ({len(rows)} câu) — nguồn cho 20 slot telemetry ==")
        for r in rows:
            print(f"  [{r['count']}x] {r['sample_question']}")
        if not rows:
            print("  (rỗng, chưa có traffic thật — đổ đầy sau khi mở cho người dùng)")
        return

    metrics, per = run()
    print("== GOLDEN EVAL (fallback path) ==")
    for p in per:
        extra = ""
        if p["cell_recall"] is not None:
            extra = f" rec={p['cell_recall']:.2f} cov={p['cite_coverage']:.2f}"
        flag = "" if p["status_ok"] else "  <-- MISS"
        print(f"  [{p['expect']:9s}->{p['pred']:9s}]{extra} {p['ms']:6.0f}ms  {p['q'][:58]}{flag}")

    print("\n-- metrics --")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    if "--compare" in sys.argv and BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))["metrics"]
        print("\n-- delta vs baseline --")
        gate_ok = True
        for k in HEADLINE:
            b, n = base.get(k), metrics.get(k)
            if b is None or n is None:
                continue
            d = round(n - b, 3)
            if d < 0:
                gate_ok = False
            print(f"  {k}: {b} -> {n}  (delta {d:+}) {'ok' if d >= 0 else 'REGRESSION'}")
        if not gate_ok:
            print("\nGATE FAIL: có chỉ số tụt, không được merge thay đổi retrieval.")
            sys.exit(1)
        print("\nGATE OK: mọi chỉ số delta >= 0.")
    else:
        BASELINE.write_text(
            json.dumps({"metrics": metrics, "per_case": per}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nĐã ghi baseline: {BASELINE.name}")


if __name__ == "__main__":
    main()
