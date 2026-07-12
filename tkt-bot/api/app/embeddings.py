"""Embedder pluggable. Số liệu không bao giờ đi qua embedding để trả lời (REQ-04),
embedding chỉ phục vụ tìm đoạn văn.

- hash: tất định, offline, char n-gram hashing 384 chiều. Dùng cho dev/test và pilot.
- e5:   intfloat/multilingual-e5-small qua fastembed (ONNX, không cần torch).
"""
import hashlib
import math
import re
import unicodedata

from .config import EMBEDDING_DIM, EMBEDDINGS

_e5_model = None


def _strip_diacritics(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    norm = _strip_diacritics(text.lower())
    words = re.findall(r"[a-z0-9]+", norm)
    grams = words + [" ".join(p) for p in zip(words, words[1:])]
    padded = f"  {norm}  "
    grams += [padded[i:i + 3] for i in range(len(padded) - 2)]
    for g in grams:
        h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big")
        vec[h % EMBEDDING_DIM] += 1.0 if (h >> 63) else -1.0
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


def embed(texts: list[str]) -> list[list[float]]:
    if EMBEDDINGS == "e5":
        global _e5_model
        if _e5_model is None:
            from fastembed import TextEmbedding
            _e5_model = TextEmbedding("intfloat/multilingual-e5-small")
        return [list(map(float, v)) for v in _e5_model.embed(texts)]
    return [_hash_embed(t) for t in texts]
