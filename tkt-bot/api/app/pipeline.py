"""Dây chuyền trả lời: router -> retrieval -> composer -> verifier.
Vi phạm cứng thì composer viết lại, tối đa hai vòng, quá thì fallback an toàn kèm log.
"""
from . import log, telemetry
from .composer import NULL_ANSWER, DEFAULT_FOLLOWUPS, compose, compose_fallback, finalize
from .config import LLM_ENABLED
from .retrieval import retrieve
from .router import classify
from .verifier import verify

MAX_REWRITES = 2

SAFE_FALLBACK = {"answer_markdown": NULL_ANSWER, "status": "null",
                 "citation_ids": [], "followups": DEFAULT_FOLLOWUPS}


def answer_pipeline(question: str) -> tuple[dict, dict]:
    """Trả về (Answer dict theo contract, meta cho telemetry)."""
    intent = classify(question)
    log.event("router", "intent", intent=intent)

    if intent == "factual":
        cached = telemetry.cache_get(question)
        if cached is not None:
            telemetry.incr_counter("cache_hits")
            log.event("pipeline", "cache_hit", intent=intent)
            return cached, {"intent": intent, "rewrites": 0,
                            "style_fallback": False, "cache_hit": True,
                            "soft_warnings": []}

    retrieved = (retrieve(question) if intent in ("factual", "interpretive")
                 else {"cells": [], "chunks": []})
    log.event("retrieval", "retrieved", cells=len(retrieved["cells"]),
              chunks=len(retrieved["chunks"]))
    telemetry.incr_counter("composer_calls")

    raw, lookup = compose(question, intent, retrieved)
    meta = {"intent": intent, "rewrites": 0, "style_fallback": False}
    log.event("composer", "composed", status=raw.get("status"))

    check = verify(raw.get("answer_markdown", ""), lookup, question)
    log.event("verifier", "verified", ok=check["ok"],
              violations=len(check["violations"]))
    while not check["ok"] and meta["rewrites"] < MAX_REWRITES and LLM_ENABLED:
        meta["rewrites"] += 1
        log.event("pipeline", "rewrite", round=meta["rewrites"],
                  feedback=check["feedback"])
        raw, lookup = compose(question, intent, retrieved, feedback=check["feedback"])
        check = verify(raw.get("answer_markdown", ""), lookup, question)
        log.event("verifier", "verified", ok=check["ok"],
                  violations=len(check["violations"]), round=meta["rewrites"])

    if not check["ok"]:
        log.event("pipeline", "style_fallback", rewrites=meta["rewrites"],
                  feedback=check["feedback"])
        meta["style_fallback"] = True
        raw = dict(SAFE_FALLBACK)

    meta["soft_warnings"] = [v for v in check["violations"] if v["severity"] == "soft"]
    meta["cache_hit"] = False
    answer = finalize(raw, lookup, retrieved, intent=intent)
    if intent == "factual" and not meta["style_fallback"]:
        telemetry.cache_put(question, answer)
    return answer, meta
