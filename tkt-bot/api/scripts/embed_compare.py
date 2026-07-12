"""TIP-08 đầu việc 4: in top-3 chunk cho 10 câu diễn giải dưới mode embedding
hiện hành (env EMBEDDINGS). Chạy hai lần, một lần EMBEDDINGS=hash một lần
EMBEDDINGS=e5 (nhớ re-ingest giữa hai lần), rồi người so sánh đánh dấu bên
nào trúng ý hơn.
    docker compose run --rm -e EMBEDDINGS=e5 api sh -c \
        "python scripts/ingest_chunks.py && python scripts/embed_compare.py"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import EMBEDDINGS  # noqa: E402
from app.retrieval import hybrid_search  # noqa: E402

QUESTIONS = [
    "Học ngành toán kinh tế ra trường làm nghề gì?",
    "Con gái học phân tích dữ liệu có phù hợp không?",
    "Ngành này khác gì với ngành kinh tế học?",
    "Chương trình tiếng Anh có đáng tiền hơn không?",
    "Em học khối D01 thì nên chọn chuyên ngành nào?",
    "Môi trường học tập ở khoa như thế nào?",
    "Cơ hội học lên cao học của ngành ra sao?",
    "Ngành có thiên về lập trình nhiều không?",
    "Doanh nghiệp nào hay tuyển sinh viên ngành này?",
    "Điểm mạnh của khoa so với các trường khác là gì?",
]


def main() -> None:
    print(f"== EMBEDDINGS={EMBEDDINGS} ==")
    for i, q in enumerate(QUESTIONS, 1):
        print(f"\n[{i:02d}] {q}")
        for rank, ch in enumerate(hybrid_search(q, k=3), 1):
            snippet = ch["text"].replace("\n", " ")[:90]
            print(f"   {rank}. [{ch['tier']}·{ch['snapshot']}] {snippet}")


if __name__ == "__main__":
    main()
