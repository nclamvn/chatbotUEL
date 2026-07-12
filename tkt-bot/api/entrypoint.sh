#!/bin/sh
set -e
echo "[entrypoint] nạp dữ liệu (idempotent)"
python scripts/load_data.py
if [ -f scripts/ingest_chunks.py ]; then
  echo "[entrypoint] ingest chunks corpus tầng 2"
  python scripts/ingest_chunks.py
fi
echo "[entrypoint] khởi động API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
