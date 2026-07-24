"""Điều phối LLM: OpenAI chính, Anthropic dự phòng.

Mỗi provider phải trả JSON hợp lệ trước khi được xem là thành công. Vì vậy lỗi
mạng, rate limit, model không khả dụng và phản hồi sai định dạng đều kích hoạt
fallback sang provider tiếp theo. Khi cả hai không dùng được, caller tự rơi về
heuristic/template an toàn.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable

from .config import (ANTHROPIC_API_KEY, ANTHROPIC_MODEL, OPENAI_API_KEY,
                     OPENAI_MODEL)


class LLMUnavailable(RuntimeError):
    """Không provider nào tạo được JSON hợp lệ."""


@dataclass(frozen=True)
class LLMResult:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


def _json_from_text(text: str) -> dict:
    value = text.strip()
    if value.startswith("```"):
        value = value.strip("`").removeprefix("json").strip()
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")
    return parsed


def _call_openai(system: str, user: str, max_tokens: int) -> tuple[str, LLMResult]:
    from openai import OpenAI

    params = {
        "model": OPENAI_MODEL,
        "instructions": system,
        # JSON mode yêu cầu từ "JSON" xuất hiện trong input, không chỉ instructions.
        "input": f"Trả lời bằng JSON hợp lệ.\n\n{user}",
        "max_output_tokens": max_tokens,
        "text": {"format": {"type": "json_object"}},
    }
    # GPT-5 có reasoning tokens nằm trong max_output_tokens. Giữ mức minimal để
    # router ngắn vẫn còn ngân sách sinh JSON; model không reasoning bỏ qua cờ này.
    if OPENAI_MODEL.startswith(("gpt-5", "o")):
        params["reasoning"] = {"effort": "minimal"}
    response = OpenAI(api_key=OPENAI_API_KEY).responses.create(**params)
    usage = response.usage
    return response.output_text, LLMResult(
        provider="openai",
        model=response.model,
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
    )


def _call_anthropic(system: str, user: str, max_tokens: int) -> tuple[str, LLMResult]:
    import anthropic

    message = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY).messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in message.content
                   if getattr(block, "type", "") == "text")
    return text, LLMResult(
        provider="anthropic",
        model=message.model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )


def _record_success(purpose: str, result: LLMResult) -> None:
    from . import log, telemetry

    # Telemetry không được biến một câu trả lời hợp lệ thành lỗi provider.
    try:
        telemetry.incr_counter(f"llm_calls_{purpose}")
        telemetry.incr_counter(f"llm_calls_{purpose}_{result.provider}")
        telemetry.incr_counter(f"llm_tokens_in_{purpose}", result.input_tokens)
        telemetry.incr_counter(f"llm_tokens_out_{purpose}", result.output_tokens)
    except Exception as exc:
        log.event("llm", "telemetry_error", purpose=purpose, error=str(exc))
    log.event(purpose, "llm", provider=result.provider, model=result.model,
              tokens_in=result.input_tokens, tokens_out=result.output_tokens)


def generate_json(system: str, user: str, max_tokens: int, purpose: str,
                  validate: Callable[[dict], bool] | None = None
                  ) -> tuple[dict, LLMResult]:
    """Gọi provider theo thứ tự và chỉ nhận JSON vượt qua validate."""
    from . import log

    providers = []
    if OPENAI_API_KEY:
        providers.append(("openai", _call_openai))
    if ANTHROPIC_API_KEY:
        providers.append(("anthropic", _call_anthropic))

    errors = []
    for index, (provider, call) in enumerate(providers):
        try:
            text, result = call(system, user, max_tokens)
            data = _json_from_text(text)
            if validate is not None and not validate(data):
                raise ValueError("LLM JSON failed validation")
            _record_success(purpose, result)
            return data, result
        except Exception as exc:
            errors.append(f"{provider}:{type(exc).__name__}")
            log.event(purpose, "provider_failed", provider=provider,
                      error_type=type(exc).__name__)
            if index + 1 < len(providers):
                next_provider = providers[index + 1][0]
                try:
                    from . import telemetry
                    telemetry.incr_counter(
                        f"llm_fallback_{provider}_to_{next_provider}")
                except Exception:
                    pass
                log.event(purpose, "provider_fallback", provider=provider,
                          fallback_provider=next_provider)

    detail = ", ".join(errors) if errors else "no provider configured"
    raise LLMUnavailable(detail)
