"""BM25 cache gắn version (TIP-11.3). Cần DB đã nạp chunks.

Hồi quy bug hẹn giờ: trước khi vá, lru_cache maxsize=1 không khóa theo version
nên chunk mới ingest lúc server đang chạy không bao giờ vào ứng viên BM25.
"""
from app.db import connect
from app.embeddings import embed
from app.retrieval import _chunks_version, hybrid_search, invalidate_bm25_cache

FAKE_ID = "chk_test_bm25_cache"
TOKEN = "zqxywvtoken"  # token hiếm, chỉ chunk giả mang


def test_new_chunk_appears_after_ingest():
    version_before = _chunks_version()
    hybrid_search(TOKEN)  # dựng cache cho trạng thái hiện tại

    emb = embed([f"{TOKEN} noi dung gia lap de kiem cache"])[0]
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chunks (chunk_id, text, url, snapshot, fetched_at, tier, embedding) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s::vector) ON CONFLICT (chunk_id) DO NOTHING",
                (FAKE_ID, f"{TOKEN} noi dung gia lap de kiem cache",
                 "http://example/fake", "fake.html", "2026-07-20T00:00:00Z", "A", str(emb)))
            conn.commit()

        # vân tay đổi vì có thêm một chunk
        assert _chunks_version() != version_before

        hits = hybrid_search(TOKEN)
        assert any(h["chunk_id"] == FAKE_ID for h in hits), \
            [h["chunk_id"] for h in hits]
    finally:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE chunk_id = %s", (FAKE_ID,))
            conn.commit()
        invalidate_bm25_cache()
