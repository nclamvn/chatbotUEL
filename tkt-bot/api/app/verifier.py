"""Verifier hai tầng (REQ-06, REQ-07).

Tầng trace: bóc mọi số và tên riêng trong answer_markdown, đối chiếu tập
claim/chunk đã cấp cho composer. Số không truy vết được thì chặn.
Tên riêng: đối chiếu danh bạ thực thể của registry, tên có trong danh bạ
mà không nằm trong context được cấp thì chặn (chống lẫn người này sang người kia).

Tầng style: style_lint (file riêng, pure function).
"""
import re
from functools import lru_cache

from .composer import NULL_ANSWER, OOS_ANSWER, SMALLTALK_ANSWER
from .config import CONTACT_EMAIL, CONTACT_PHONE
from .db import connect
from .retrieval import norm
from .style_lint import hard_violations, lint

# số xuất hiện trong template cố định (kênh liên hệ, năm trong nhãn field)
_TEMPLATE_DIGITS = set(re.findall(r"\d+", CONTACT_PHONE + CONTACT_EMAIL)) | {"2025", "2026"}
# tên riêng trong các template cố định (bot tự giới thiệu) không cần truy vết
_TEMPLATE_TEXT = norm(NULL_ANSWER + OOS_ANSWER + SMALLTALK_ANSWER)


@lru_cache(maxsize=1)
def known_entity_names() -> tuple:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT DISTINCT entity FROM claims")
        return tuple(r["entity"] for r in cur.fetchall())


def _digit_tokens(text: str) -> set:
    return {t for t in re.findall(r"\d+(?:[.,]\d+)*", text)}


def _canon_number(tok: str) -> str:
    return re.sub(r"\D", "", tok)


def _evidence_text(lookup: dict) -> str:
    """Tập đối chiếu SỐ: chỉ value cộng evidence_span của claim và text chunk
    (evidence tầng 2). Tên nguồn, snapshot không nằm đây (L2 chốt 12/07):
    số dính trong tên nguồn không được phép hợp thức hóa số rời trong answer."""
    parts = []
    for rec in lookup.values():
        if rec["kind"] == "claim":
            parts += [str(rec["value"]), rec["evidence_span"]]
        else:
            parts.append(rec["text"])
    return "\n".join(parts)


def _name_text(lookup: dict) -> str:
    """Tập đối chiếu TÊN RIÊNG: đủ những gì composer thấy trong build_context,
    gồm cả tên nguồn và snapshot."""
    parts = []
    for rec in lookup.values():
        if rec["kind"] == "claim":
            parts += [rec["entity"], str(rec["value"]), rec["evidence_span"],
                      rec["source"]]
        else:
            parts += [rec["text"], rec["snapshot"]]
    return "\n".join(parts)


def _metadata_strings(lookup: dict) -> set:
    """Chuỗi metadata được mask khỏi answer trước khi bóc số: tên nguồn và
    snapshot trong context. \"tuyensinh247.com\" nguyên chuỗi hợp lệ,
    \"247\" đứng rời thì không."""
    out = set()
    for rec in lookup.values():
        if rec["kind"] == "claim":
            out.add(rec["source"])
        else:
            out.add(rec["snapshot"])
        out.add(rec.get("url", ""))
    return {s for s in out if s}


def trace_check(answer_markdown: str, lookup: dict, question: str) -> list[dict]:
    violations = []
    masked = answer_markdown
    for s in sorted(_metadata_strings(lookup), key=len, reverse=True):
        masked = masked.replace(s, " ")
    allowed = {_canon_number(t) for t in
               _digit_tokens(_evidence_text(lookup)) | _digit_tokens(question)
               | _TEMPLATE_DIGITS}
    for tok in _digit_tokens(masked):
        if _canon_number(tok) not in allowed:
            violations.append({
                "code": "UNTRACED_NUMBER", "severity": "hard",
                "detail": f"số \"{tok}\" không truy vết được về claim nào trong context"})

    ctx_norm = norm(_name_text(lookup))
    ans_norm = norm(answer_markdown)
    for name in known_entity_names():
        n = norm(name)
        if n in ans_norm and n not in ctx_norm and n not in _TEMPLATE_TEXT:
            violations.append({
                "code": "UNTRACED_NAME", "severity": "hard",
                "detail": f"tên riêng \"{name}\" không nằm trong context được cấp"})
    return violations


def verify(answer_markdown: str, lookup: dict, question: str) -> dict:
    violations = trace_check(answer_markdown, lookup, question) + lint(answer_markdown)
    hard = hard_violations(violations)
    feedback = "\n".join(f"- [{v['code']}] {v['detail']}" +
                         (f" · gợi ý: {v['suggestion']}" if v.get("suggestion") else "")
                         for v in violations)
    return {"ok": not hard, "violations": violations, "feedback": feedback}
