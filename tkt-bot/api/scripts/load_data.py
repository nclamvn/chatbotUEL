"""Nạp claims.jsonl vào Postgres và build registry tất định.

Luật status lấy nguyên từ refinery.build của domain refinery:
- disputed      khi tồn tại từ hai value khác nhau
- corroborated  khi một value duy nhất có từ hai nguồn độc lập tier A hoặc B
- sourced       khi một value duy nhất chưa đủ hai nguồn mạnh
- null          khi field trong schema không có claim nào

Chạy lại nhiều lần cho cùng kết quả: claim_id là hash nội dung claim,
bảng được ghi đè trong một transaction, registry.json xếp khóa cố định.
"""
import hashlib
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import DATA_DIR  # noqa: E402
from app.db import connect, ensure_schema  # noqa: E402


def claim_id_of(c: dict) -> str:
    canon = json.dumps(c, ensure_ascii=False, sort_keys=True)
    return "clm_" + hashlib.sha1(canon.encode("utf-8")).hexdigest()[:12]


def load_domain_cfg():
    with open(os.path.join(DATA_DIR, "domain.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def canonicalize(cfg: dict, name: str) -> str:
    return cfg.get("alias_map", {}).get(name, name)


def read_claims(cfg: dict) -> list[dict]:
    claims = []
    with open(os.path.join(DATA_DIR, "claims.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            c["entity"] = canonicalize(cfg, c["entity"])
            c["claim_id"] = claim_id_of({k: v for k, v in c.items() if k != "claim_id"})
            claims.append(c)
    return claims


def build_registry(cfg: dict, claims: list[dict]) -> list[dict]:
    fields = cfg["schema"]["fields"]
    grouped: dict[str, dict[str, list[dict]]] = {}
    for c in claims:
        grouped.setdefault(c["entity"], {}).setdefault(c["field"], []).append(c)

    cells = []
    for ent in sorted(grouped):
        for f in fields:
            cs = sorted(grouped[ent].get(f, []), key=lambda c: c["claim_id"])
            if not cs:
                cells.append({"entity": ent, "field": f, "status": "null",
                              "value_json": None, "claim_ids": []})
                continue
            values = {json.dumps(c["value"], ensure_ascii=False, sort_keys=True) for c in cs}
            ids = [c["claim_id"] for c in cs]
            if len(values) > 1:
                cells.append({"entity": ent, "field": f, "status": "disputed",
                              "value_json": None, "claim_ids": ids})
            else:
                strong = {c["capture"]["source"] for c in cs if c["tier"] in ("A", "B")}
                status = "corroborated" if len(strong) >= 2 else "sourced"
                cells.append({"entity": ent, "field": f, "status": status,
                              "value_json": cs[0]["value"], "claim_ids": ids})
    return cells


def registry_digest(cells: list[dict]) -> str:
    canon = json.dumps(cells, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def write_registry_json(cells: list[dict], digest: str) -> None:
    out = {"registry_version": digest, "cells": cells}
    path = os.path.join(DATA_DIR, "registry.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)


def load_postgres(claims: list[dict], cells: list[dict], digest: str) -> None:
    with connect() as conn:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE claims, registry_cells")
            for c in claims:
                cur.execute(
                    """INSERT INTO claims (claim_id, entity, field, value, evidence_span,
                       extraction, tier, url, fetched_at, snapshot, source)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (c["claim_id"], c["entity"], c["field"],
                     json.dumps(c["value"], ensure_ascii=False), c["evidence_span"],
                     c["extraction"], c["tier"], c["capture"]["url"],
                     c["capture"]["fetched_at"], c["capture"]["snapshot"],
                     c["capture"]["source"]))
            for cell in cells:
                cur.execute(
                    """INSERT INTO registry_cells (entity, field, status, value_json, claim_ids)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (cell["entity"], cell["field"], cell["status"],
                     json.dumps(cell["value_json"], ensure_ascii=False),
                     json.dumps(cell["claim_ids"])))
            cur.execute(
                """INSERT INTO meta (key, value) VALUES ('registry_version', %s)
                   ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                (digest,))
        conn.commit()


def main() -> None:
    cfg = load_domain_cfg()
    claims = read_claims(cfg)
    cells = build_registry(cfg, claims)
    digest = registry_digest(cells)
    write_registry_json(cells, digest)

    entities = sorted({c["entity"] for c in claims})
    non_null = [c for c in cells if c["status"] != "null"]
    print(f"claims={len(claims)} entities={len(entities)} "
          f"cells={len(cells)} non_null={len(non_null)} registry_version={digest}")

    if os.environ.get("SKIP_DB") == "1":
        print("SKIP_DB=1, chỉ build registry.json")
        return
    load_postgres(claims, cells, digest)
    print("postgres loaded OK")


if __name__ == "__main__":
    main()
