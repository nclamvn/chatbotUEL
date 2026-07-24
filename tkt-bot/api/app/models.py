"""Pydantic models cho JSON contract của TKT-BOT (Blueprint mục 3)."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Capture(BaseModel):
    url: str
    fetched_at: str
    snapshot: str
    source: str


class Claim(BaseModel):
    claim_id: str
    entity: str
    field: str
    value: Any
    evidence_span: str
    extraction: str
    tier: Literal["A", "B", "C"]
    capture: Capture


class RegistryCell(BaseModel):
    entity: str
    field: str
    status: Literal["corroborated", "sourced", "disputed", "null"]
    value_json: Any = None
    claim_ids: list[str] = Field(default_factory=list)


class Chunk(BaseModel):
    chunk_id: str
    text: str
    url: str
    snapshot: str
    fetched_at: str
    tier: Literal["A", "B", "C"]


class Citation(BaseModel):
    claim_id: str
    source: str
    tier: Literal["A", "B", "C"]
    fetched_at: str
    evidence_span: str
    url: str


class Answer(BaseModel):
    answer_markdown: str
    status: Literal["grounded", "disputed", "null", "oos"]
    citations: list[Citation] = Field(default_factory=list)
    followups: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    # mock là mặc định an toàn/ổn định cho demo; api mới gọi provider thật.
    response_mode: Literal["mock", "api"] = "mock"
