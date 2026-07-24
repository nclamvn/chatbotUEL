import pytest

import app.llm as llm


def _result(provider: str) -> llm.LLMResult:
    return llm.LLMResult(provider=provider, model=f"{provider}-test",
                         input_tokens=10, output_tokens=5)


def test_openai_is_primary(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "test-openai")
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setattr(llm, "_record_success", lambda *args: None)
    monkeypatch.setattr(
        llm, "_call_openai",
        lambda *args: (calls.append("openai") or '{"status":"ok"}',
                       _result("openai")))
    monkeypatch.setattr(
        llm, "_call_anthropic",
        lambda *args: (calls.append("anthropic") or '{"status":"ok"}',
                       _result("anthropic")))

    data, result = llm.generate_json("system", "user", 20, "test")

    assert data == {"status": "ok"}
    assert result.provider == "openai"
    assert calls == ["openai"]


def test_falls_back_to_anthropic_when_openai_fails(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "test-openai")
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setattr(llm, "_record_success", lambda *args: None)

    def fail_openai(*args):
        calls.append("openai")
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(llm, "_call_openai", fail_openai)
    monkeypatch.setattr(
        llm, "_call_anthropic",
        lambda *args: (calls.append("anthropic") or '{"status":"ok"}',
                       _result("anthropic")))

    data, result = llm.generate_json("system", "user", 20, "test")

    assert data == {"status": "ok"}
    assert result.provider == "anthropic"
    assert calls == ["openai", "anthropic"]


def test_invalid_openai_json_also_falls_back(monkeypatch):
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "test-openai")
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setattr(llm, "_record_success", lambda *args: None)
    monkeypatch.setattr(
        llm, "_call_openai", lambda *args: ("not-json", _result("openai")))
    monkeypatch.setattr(
        llm, "_call_anthropic",
        lambda *args: ('{"intent":"factual"}', _result("anthropic")))

    data, result = llm.generate_json(
        "system", "user", 20, "test",
        validate=lambda value: value.get("intent") == "factual")

    assert data["intent"] == "factual"
    assert result.provider == "anthropic"


def test_no_provider_raises(monkeypatch):
    monkeypatch.setattr(llm, "OPENAI_API_KEY", "")
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "")

    with pytest.raises(llm.LLMUnavailable, match="no provider configured"):
        llm.generate_json("system", "user", 20, "test")
