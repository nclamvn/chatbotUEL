"""Structured logging JSON có request_id (TIP-11.4).

request_id sinh một lần mỗi request, giữ trong contextvar nên propagate xuyên
router, retrieval, composer, verifier mà không phải luồn qua từng chữ ký hàm.
asyncio.to_thread copy context nên pipeline chạy trong thread vẫn thấy đúng id.
grep log theo request_id thấy đủ dấu chân bốn tầng pipeline.
"""
from contextvars import ContextVar
import json
import logging
import sys
import uuid

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def new_request_id() -> str:
    rid = uuid.uuid4().hex[:12]
    _request_id.set(rid)
    return rid


def set_request_id(rid: str) -> None:
    _request_id.set(rid)


def get_request_id() -> str:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "component": record.name,
            "request_id": _request_id.get(),
            "msg": record.getMessage(),
        }
        for key, val in getattr(record, "extra_fields", {}).items():
            payload[key] = val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def event(component: str, msg: str, **fields) -> None:
    logging.getLogger(component).info(msg, extra={"extra_fields": fields})
