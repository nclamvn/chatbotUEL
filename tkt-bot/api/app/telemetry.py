"""Telemetry ẩn danh và cache câu trả lời (REQ-11, REQ-12).

- Mỗi lượt hỏi log: hash phiên, câu hỏi, status, citations, thumbs.
- Câu honest-null lặp lại nổi lên ở /telemetry/nulls làm backlog crawl.
- Cache theo khóa câu hỏi chuẩn hóa, TTL 24 giờ, chỉ intent factual,
  bỏ cache khi registry_version đổi.
"""
import hashlib
import json

from .db import connect
from .retrieval import norm

CACHE_TTL_HOURS = 24


def session_hash(session_id: str | None) -> str:
    return hashlib.sha256((session_id or "anon").encode()).hexdigest()[:16]


def cache_key(question: str) -> str:
    return hashlib.sha256(norm(question).encode()).hexdigest()[:32]


def registry_version(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM meta WHERE key = 'registry_version'")
        row = cur.fetchone()
    return row["value"] if row else ""


def incr_counter(name: str, by: int = 1) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO meta (key, value) VALUES (%s, %s)
               ON CONFLICT (key) DO UPDATE SET value = (meta.value::int + %s)::text""",
            (f"counter:{name}", str(by), by))
        conn.commit()


def get_counter(name: str) -> int:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM meta WHERE key = %s", (f"counter:{name}",))
        row = cur.fetchone()
    return int(row["value"]) if row else 0


def cache_get(question: str) -> dict | None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT answer FROM answer_cache
               WHERE cache_key = %s AND registry_version = %s
                 AND created_at > now() - make_interval(hours => %s)""",
            (cache_key(question), registry_version(conn), CACHE_TTL_HOURS))
        row = cur.fetchone()
    return row["answer"] if row else None


def cache_put(question: str, answer: dict) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO answer_cache (cache_key, registry_version, answer)
               VALUES (%s, %s, %s)
               ON CONFLICT (cache_key) DO UPDATE
                 SET registry_version = EXCLUDED.registry_version,
                     answer = EXCLUDED.answer, created_at = now()""",
            (cache_key(question), registry_version(conn),
             json.dumps(answer, ensure_ascii=False)))
        conn.commit()


def log_event(session_id: str | None, question: str, status: str,
              citations: list, thumbs: str | None = None) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO telemetry_events
               (session_hash, question, normalized, status, citations, thumbs)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (session_hash(session_id), question, norm(question), status,
             json.dumps(citations, ensure_ascii=False), thumbs))
        conn.commit()


def null_backlog(limit: int = 20) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT normalized, count(*) AS count,
                      count(DISTINCT session_hash) AS sessions,
                      max(question) AS sample_question,
                      max(ts) AS last_seen
               FROM telemetry_events
               WHERE status = 'null'
               GROUP BY normalized
               ORDER BY count DESC, last_seen DESC
               LIMIT %s""", (limit,))
        return [dict(r) for r in cur.fetchall()]
