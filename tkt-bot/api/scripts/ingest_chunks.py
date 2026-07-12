"""Ingest corpus tầng 2: snapshots HTML -> chunks kèm metadata nguồn bắt buộc.

Amendment 2026-07-12: chỉ ingest snapshot được claims tham chiếu. File dưới 1 KB
hoặc không xuất hiện trong bất kỳ capture.snapshot nào thì bỏ qua và log tên.
Chunk thiếu metadata (url, snapshot, fetched_at, tier) thì fail loud, exit khác 0.
"""
import hashlib
import json
import os
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import DATA_DIR  # noqa: E402
from app.db import connect, ensure_schema  # noqa: E402
from app.embeddings import embed  # noqa: E402

MIN_SNAPSHOT_BYTES = 1024
CHUNK_CHARS = 800
CHUNK_OVERLAP = 120
REQUIRED_META = ("url", "snapshot", "fetched_at", "tier")


def snapshot_metadata() -> dict:
    """snapshot -> {url, fetched_at, tier, source} suy từ claims, tất định."""
    meta = {}
    with open(os.path.join(DATA_DIR, "claims.jsonl"), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cap = c["capture"]
            key = cap["snapshot"]
            cand = {"url": cap["url"], "fetched_at": cap["fetched_at"],
                    "tier": c["tier"], "source": cap["source"]}
            if key not in meta:
                meta[key] = cand
            elif meta[key] != cand:
                # xung đột metadata giữa các claim cùng snapshot: chọn tất định
                # theo (tier, url) nhỏ nhất và báo để audit
                pick = min(meta[key], cand, key=lambda m: (m["tier"], m["url"], m["fetched_at"]))
                print(f"[ingest] WARN metadata lệch trong snapshot {key}, chọn tất định {pick['tier']}·{pick['url']}")
                meta[key] = pick
    return meta


def html_to_text(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "lxml")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if len(ln) > 2]
    return "\n".join(lines)


def chunk_text(text: str) -> list[str]:
    chunks, buf = [], ""
    for para in text.split("\n"):
        if len(buf) + len(para) + 1 <= CHUNK_CHARS:
            buf = f"{buf}\n{para}" if buf else para
            continue
        if buf:
            chunks.append(buf)
            buf = buf[-CHUNK_OVERLAP:] + "\n" + para if CHUNK_OVERLAP else para
        while len(buf) > CHUNK_CHARS:
            chunks.append(buf[:CHUNK_CHARS])
            buf = buf[CHUNK_CHARS - CHUNK_OVERLAP:]
    if buf.strip():
        chunks.append(buf)
    return [c.strip() for c in chunks if len(c.strip()) >= 80]


def main() -> None:
    snap_dir = os.path.join(DATA_DIR, "snapshots")
    meta = snapshot_metadata()
    referenced = set(meta)

    on_disk = sorted(f for f in os.listdir(snap_dir) if not f.startswith("."))
    selected, skipped = [], []
    for name in on_disk:
        path = os.path.join(snap_dir, name)
        size = os.path.getsize(path)
        if size < MIN_SNAPSHOT_BYTES:
            skipped.append(f"{name} (dưới 1 KB: {size} bytes)")
            continue
        if name not in referenced:
            skipped.append(f"{name} (không được claim nào tham chiếu)")
            continue
        selected.append(name)

    for s in skipped:
        print(f"[ingest] SKIP {s}")
    missing_ref = referenced - set(selected)
    if missing_ref:
        print(f"[ingest] FAIL: snapshot được claims tham chiếu nhưng thiếu trên đĩa: {sorted(missing_ref)}")
        sys.exit(1)
    print(f"[ingest] nguồn ingest: {len(selected)} snapshot (kỳ vọng 14 theo Amendment 2026-07-12)")

    rows = []
    for name in selected:
        m = meta[name]
        record = {"snapshot": name, **m}
        for k in REQUIRED_META:
            if not record.get(k):
                print(f"[ingest] FAIL: snapshot {name} thiếu metadata bắt buộc '{k}'")
                sys.exit(1)
        text = html_to_text(os.path.join(snap_dir, name))
        for i, chunk in enumerate(chunk_text(text)):
            cid = "chk_" + hashlib.sha1(f"{name}:{i}:{chunk[:64]}".encode()).hexdigest()[:12]
            rows.append((cid, chunk, m["url"], name, m["fetched_at"], m["tier"]))

    if not rows:
        print("[ingest] FAIL: không sinh được chunk nào")
        sys.exit(1)

    if os.environ.get("SKIP_DB") == "1":
        print(f"[ingest] SKIP_DB=1, dừng trước bước nạp ({len(rows)} chunks đã dựng)")
        return

    vecs = embed([r[1] for r in rows])
    with connect() as conn:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE chunks")
            for (cid, chunk, url, snap, fetched, tier), vec in zip(rows, vecs):
                cur.execute(
                    """INSERT INTO chunks (chunk_id, text, url, snapshot, fetched_at, tier, embedding)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (cid, chunk, url, snap, fetched, tier, str(vec)))
        conn.commit()
    print(f"[ingest] OK: {len(rows)} chunks từ {len(selected)} snapshot")


if __name__ == "__main__":
    main()
