"""TIP-04: vi phạm cứng thì composer nhận yêu cầu viết lại, quá hai vòng thì
fallback an toàn kèm log. Giả lập đường LLM bằng monkeypatch."""
import app.pipeline as pipeline


def _fake_compose_factory(answers):
    calls = {"n": 0, "feedbacks": []}

    def fake_compose(question, intent, retrieved, feedback=None, use_llm=None):
        calls["feedbacks"].append(feedback)
        raw = {"answer_markdown": answers[min(calls["n"], len(answers) - 1)],
               "status": "grounded", "citation_ids": [], "followups": []}
        calls["n"] += 1
        return raw, {}

    return fake_compose, calls


def test_rewrite_on_emdash_then_pass(monkeypatch):
    fake, calls = _fake_compose_factory(
        ["Khoa Toán Kinh tế — đơn vị trẻ.", "Chào bạn, mình đây."])
    monkeypatch.setattr(pipeline, "compose", fake)
    monkeypatch.setattr(pipeline, "classify", lambda q, use_llm=None: "smalltalk")
    monkeypatch.setattr(pipeline, "LLM_ENABLED", True)

    answer, meta = pipeline.answer_pipeline("chào bạn")
    assert calls["n"] == 2
    assert calls["feedbacks"][1] and "EMDASH" in calls["feedbacks"][1]
    assert meta["rewrites"] == 1 and not meta["style_fallback"]
    assert "—" not in answer["answer_markdown"]


def test_fallback_after_two_failed_rewrites(monkeypatch):
    bad = "Toán, và kinh tế — hay; đẹp; vui."
    fake, calls = _fake_compose_factory([bad, bad, bad])
    monkeypatch.setattr(pipeline, "compose", fake)
    monkeypatch.setattr(pipeline, "classify", lambda q, use_llm=None: "smalltalk")
    monkeypatch.setattr(pipeline, "LLM_ENABLED", True)

    answer, meta = pipeline.answer_pipeline("chào bạn")
    assert calls["n"] == 3  # lần đầu + hai vòng viết lại
    assert meta["rewrites"] == 2 and meta["style_fallback"]
    assert answer["status"] == "null"
    assert "—" not in answer["answer_markdown"] and ";" not in answer["answer_markdown"]
