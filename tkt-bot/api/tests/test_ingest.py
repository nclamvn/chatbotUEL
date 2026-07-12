"""TIP-02 AC2: chunk thiếu metadata nguồn thì ingest fail loud, exit khác 0 kèm tên."""
import json
import os
import shutil
import subprocess
import sys

API_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(API_DIR, "data")


def _run_ingest(data_dir: str):
    env = {**os.environ, "DATA_DIR": data_dir, "SKIP_DB": "1"}
    return subprocess.run(
        [sys.executable, os.path.join(API_DIR, "scripts", "ingest_chunks.py")],
        capture_output=True, text=True, env=env)


def _make_broken_dataset(tmp_path):
    """Copy dataset thật, xoá fetched_at của mọi claim trỏ vào maths-home.html."""
    dd = tmp_path / "data"
    dd.mkdir()
    shutil.copytree(os.path.join(DATA_DIR, "snapshots"), dd / "snapshots")
    shutil.copy(os.path.join(DATA_DIR, "domain.yaml"), dd / "domain.yaml")
    lines = []
    with open(os.path.join(DATA_DIR, "claims.jsonl"), encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["capture"]["snapshot"] == "maths-home.html":
                c["capture"]["fetched_at"] = ""
            lines.append(json.dumps(c, ensure_ascii=False))
    (dd / "claims.jsonl").write_text("\n".join(lines), encoding="utf-8")
    return str(dd)


def test_missing_fetched_at_fails_loud(tmp_path):
    proc = _run_ingest(_make_broken_dataset(tmp_path))
    assert proc.returncode != 0
    out = proc.stdout + proc.stderr
    assert "maths-home.html" in out
    assert "fetched_at" in out


def test_skip_rules_and_source_count(tmp_path):
    """File dưới 1 KB và file không được tham chiếu bị loại kèm log, tổng nguồn 14."""
    dd = tmp_path / "data"
    dd.mkdir()
    shutil.copytree(os.path.join(DATA_DIR, "snapshots"), dd / "snapshots")
    shutil.copy(os.path.join(DATA_DIR, "domain.yaml"), dd / "domain.yaml")
    shutil.copy(os.path.join(DATA_DIR, "claims.jsonl"), dd / "claims.jsonl")
    proc = _run_ingest(str(dd))
    out = proc.stdout + proc.stderr
    assert "SKIP tuyensinh-nganh-la-gi.html (dưới 1 KB" in out
    assert "SKIP maths-cao-hoc.html (không được claim nào tham chiếu)" in out
    assert "nguồn ingest: 14 snapshot" in out
