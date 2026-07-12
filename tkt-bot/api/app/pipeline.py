"""Dây chuyền trả lời: router -> retrieval -> composer -> verifier.
Vi phạm cứng thì composer viết lại, tối đa hai vòng, quá thì fallback an toàn kèm log.
"""
from . import telemetry
from .composer import NULL_ANSWER, DEFAULT_FOLLOWUPS, compose, compose_fallback, finalize
from .config import ANTHROPIC_API_KEY
from .retrieval import retrieve
from .router import classify
from .verifier import verify

MAX_REWRITES = 2

SAFE_FALLBACK = {"answer_markdown": NULL_ANSWER, "status": "null",
                 "citation_ids": [], "followups": DEFAULT_FOLLOWUPS}


def answer_pipeline(question: str) -> tuple[dict, dict]:
    """Trả về (Answer dict theo contract, meta cho telemetry)."""
    intent = classify(question)

    if intent == "factual":
        cached = telemetry.cache_get(question)
        if cached is not None:
            telemetry.incr_counter("cache_hits")
            return cached, {"intent": intent, "rewrites": 0,
                            "style_fallback": False, "cache_hit": True,
                            "soft_warnings": []}

    retrieved = (retrieve(question) if intent in ("factual", "interpretive")
                 else {"cells": [], "chunks": []})
    telemetry.incr_counter("composer_calls")

    raw, lookup = compose(question, intent, retrieved)
    meta = {"intent": intent, "rewrites": 0, "style_fallback": False}

    check = verify(raw.get("answer_markdown", ""), lookup, question)
    while not check["ok"] and meta["rewrites"] < MAX_REWRITES and ANTHROPIC_API_KEY:
        meta["rewrites"] += 1
        print(f"[pipeline] vi phạm, yêu cầu viết lại vòng {meta['rewrites']}:\n{check['feedback']}")
        raw, lookup = compose(question, intent, retrieved, feedback=check["feedback"])
        check = verify(raw.get("answer_markdown", ""), lookup, question)

    if not check["ok"]:
        print(f"[pipeline] STYLE_FALLBACK sau {meta['rewrites']} vòng viết lại, "
              f"vi phạm còn lại:\n{check['feedback']}")
        meta["style_fallback"] = True
        raw = dict(SAFE_FALLBACK)

    meta["soft_warnings"] = [v for v in check["violations"] if v["severity"] == "soft"]
    meta["cache_hit"] = False
    answer = finalize(raw, lookup, retrieved, intent=intent)
    if intent == "factual" and not meta["style_fallback"]:
        telemetry.cache_put(question, answer)
    return answer, meta
