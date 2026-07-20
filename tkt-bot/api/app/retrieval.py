"""Retrieval ba đường (REQ-04):
1. structured lookup: câu hỏi factual map về entity × field, trả thẳng ô registry kèm claim
2. BM25 trên chunks
3. vector search pgvector
Hai đường sau hợp nhất bằng reciprocal rank fusion, sắp lại theo tier khi độ
liên quan tương đương. Số liệu không đi qua embedding để trả lời.
"""
import json
import re
import unicodedata
from functools import lru_cache

from rank_bm25 import BM25Okapi

from .db import connect
from .embeddings import embed

RRF_K = 60
TOP_K = 8


def norm(s: str) -> str:
    s = s.lower().replace("đ", "d")
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", norm(s))


# ── structured lookup ────────────────────────────────────────────────

ENTITY_ALIASES = [
    ("cn phan tich du lieu", "CN Phân tích dữ liệu"),
    ("phan tich du lieu", "CN Phân tích dữ liệu"),
    ("toan ung dung tieng anh", "CN Toán ứng dụng trong Kinh tế, Quản trị và Tài chính (Tiếng Anh)"),
    ("chuong trinh tieng anh", "CN Toán ứng dụng trong Kinh tế, Quản trị và Tài chính (Tiếng Anh)"),
    ("toan ung dung", "CN Toán ứng dụng trong Kinh tế, Quản trị và Tài chính"),
    ("nganh toan kinh te", "Ngành Toán kinh tế"),
    ("khoa toan kinh te", "Khoa Toán Kinh tế"),
    ("kinh te luat", "Trường Đại học Kinh tế - Luật"),
    ("uel", "Trường Đại học Kinh tế - Luật"),
]

CN_ENTITIES = [
    "CN Toán ứng dụng trong Kinh tế, Quản trị và Tài chính",
    "CN Toán ứng dụng trong Kinh tế, Quản trị và Tài chính (Tiếng Anh)",
    "CN Phân tích dữ liệu",
]

# (regex trên câu đã norm, danh sách field, year_bound: field gắn năm trong tên)
FIELD_RULES = [
    (r"diem chuan|diem trung tuyen|nguong dau vao|muc trung tuyen|bao nhieu diem|lay bao nhieu",
     "diem", True),
    (r"hoc phi", "hoc_phi", True),
    (r"chi tieu", ["chi_tieu_2025"], True),
    (r"lich tuyen sinh|lich nhan ho so|nhan ho so|nop ho so|lich xet tuyen|bao gio (nop|nhan|xet)",
     ["lich_tuyen_sinh_2026"], True),
    (r"tien than|truoc day la truong nao|xuat than tu dau", ["tien_than", "nam_thanh_lap"], False),
    (r"ma tuyen sinh|ma nganh|ma xet tuyen", ["ma_tuyen_sinh"], False),
    (r"ma truong", ["ma_truong"], False),
    (r"bao nhieu tin chi|so tin chi|tin chi", ["tin_chi"], False),
    (r"bao nhieu hoc ky|may hoc ky|so hoc ky", ["so_hoc_ky"], False),
    (r"bao nhieu giang vien|so giang vien|giang vien co huu", ["so_giang_vien_co_huu"], False),
    (r"co cau hoc vi", ["co_cau_hoc_vi"], False),
    (r"bo mon", ["bo_mon_truc_thuoc"], False),
    (r"dia chi|o dau|nam o dau", ["dia_chi"], False),
    (r"\bemail\b|thu dien tu", ["email"], False),
    (r"dien thoai|so may|hotline", ["dien_thoai"], False),
    (r"thanh lap|ra doi|len khoa|lich su",
     ["nam_thanh_lap", "nam_thanh_lap_bo_mon", "nam_len_khoa", "nam_mo_nganh"], False),
    (r"triet ly", ["triet_ly_giao_duc"], False),
    (r"tam nhin", ["tam_nhin"], False),
    (r"dinh huong nghien cuu|huong nghien cuu", ["dinh_huong_nghien_cuu"], False),
    (r"chuyen nganh nao|nhung chuyen nganh|cac chuyen nganh|chuyen nganh gi",
     ["chuyen_nganh_2025"], False),
    (r"truc thuoc|thuoc truong nao|thuoc don vi nao", ["truc_thuoc"], False),
]

ROLE_VALUES = [
    "pho truong khoa", "truong khoa", "thu ky khoa",
    "truong bo mon toan kinh te", "truong bo mon phan tich du lieu",
]


def _detect_entities(q: str) -> list[str]:
    found, used = [], set()
    rest = q
    for alias, ent in ENTITY_ALIASES:
        if alias in rest and ent not in used:
            found.append(ent)
            used.add(ent)
            rest = rest.replace(alias, " ")
    return found


def _detect_diem_fields(q: str) -> list[str]:
    if re.search(r"dgnl|danh gia nang luc", q):
        return ["diem_dgnl_2025"]
    if re.search(r"utxtt|uu tien xet tuyen", q):
        return ["diem_utxtt_2025"]
    if re.search(r"\ba00\b|\ba01\b", q):
        return ["diem_thpt_2025_A00_A01"]
    if re.search(r"\bd01\b|\bd07\b|\bx25\b|\bx26\b", q):
        return ["diem_thpt_2025_D01_D07_X25_X26"]
    return ["diem_thpt_2025_A00_A01", "diem_thpt_2025_D01_D07_X25_X26"]


def _detect_hoc_phi_fields(q: str) -> list[str]:
    if "tieng anh" in q:
        return ["hoc_phi_tieng_anh_2025_2026"]
    if "tieng viet" in q:
        return ["hoc_phi_tieng_viet_2025_2026"]
    return ["hoc_phi_tieng_viet_2025_2026", "hoc_phi_tieng_anh_2025_2026"]


def _year_mismatch(q: str, fields) -> bool:
    """Field gắn năm trong tên: câu hỏi nêu năm không có trong tên field
    thì không được trả ô đó (vd hỏi 2026 mà field chỉ có dữ liệu 2025)."""
    years = set(re.findall(r"\b(20\d\d)\b", q))
    if not years:
        return False
    ok = {y for f in fields for y in re.findall(r"20\d\d", f)}
    return not (years & ok)


def _fetch_cells(entity_fields: list[tuple[str, str]]) -> list[dict]:
    if not entity_fields:
        return []
    out = []
    with connect() as conn, conn.cursor() as cur:
        for ent, field in entity_fields:
            cur.execute(
                "SELECT * FROM registry_cells WHERE entity=%s AND field=%s", (ent, field))
            row = cur.fetchone()
            if not row or row["status"] == "null":
                continue
            cur.execute(
                "SELECT * FROM claims WHERE claim_id = ANY(%s)",
                ([str(x) for x in row["claim_ids"]],))
            row["claims"] = cur.fetchall()
            out.append(row)
    return out


def _role_lookup(q: str) -> list[dict]:
    """Câu 'trưởng khoa là ai': tìm người theo giá trị chuc_vu, kèm học hàm và chuyên môn."""
    matched_role = next((r for r in ROLE_VALUES if r in q), None)
    if not matched_role:
        return []
    out = []
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM registry_cells WHERE field='chuc_vu' AND status != 'null'")
        for row in cur.fetchall():
            val = row["value_json"]
            if val is None or norm(str(val)) != matched_role:
                continue
            person = row["entity"]
            cur.execute(
                """SELECT * FROM registry_cells WHERE entity=%s
                   AND field IN ('chuc_vu','hoc_ham_hoc_vi','chuyen_mon','ghi_chu')
                   AND status != 'null'""", (person,))
            for cell in cur.fetchall():
                cur.execute("SELECT * FROM claims WHERE claim_id = ANY(%s)",
                            ([str(x) for x in cell["claim_ids"]],))
                cell["claims"] = cur.fetchall()
                out.append(cell)
    return out


PERSON_FIELDS = ("chuc_vu", "hoc_ham_hoc_vi", "chuyen_mon", "ghi_chu",
                 "dinh_huong_nghien_cuu")


@lru_cache(maxsize=1)
def _person_entities() -> tuple:
    """Danh sách entity loại nhan_su, hỏi được bằng tên (Registry v1.1)."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT entity FROM registry_cells
                       WHERE field='loai' AND value_json::text LIKE '%nhan_su%'""")
        return tuple(r["entity"] for r in cur.fetchall())


def _person_lookup(q: str) -> list[dict]:
    hits = [p for p in _person_entities() if norm(p) in q]
    return _fetch_cells([(p, f) for p in hits for f in PERSON_FIELDS])


def structured_lookup(question: str) -> list[dict]:
    q = norm(question)

    role_cells = _role_lookup(q)
    if role_cells:
        return role_cells

    person_cells = _person_lookup(q)
    if person_cells:
        return person_cells

    fields = None
    for pattern, f, year_bound in FIELD_RULES:
        if re.search(pattern, q):
            if f == "diem":
                fields = _detect_diem_fields(q)
            elif f == "hoc_phi":
                fields = _detect_hoc_phi_fields(q)
            else:
                fields = f
            if year_bound and _year_mismatch(q, fields):
                return []
            break
    if fields is None:
        return []

    def _defaults() -> list[str]:
        if fields[0].startswith(("diem_", "ma_tuyen")):
            return list(CN_ENTITIES)
        return ["Khoa Toán Kinh tế", "Ngành Toán kinh tế",
                "Trường Đại học Kinh tế - Luật"]

    entities = _detect_entities(q) or _defaults()
    # câu về điểm/mã tuyển sinh nhắm ngành chung thì mở rộng ra ba chuyên ngành
    if fields[0].startswith("diem_") and entities == ["Ngành Toán kinh tế"]:
        entities = list(CN_ENTITIES)

    cells = _fetch_cells([(e, f) for e in entities for f in fields])
    # entity match được nhưng ô toàn null (vd học phí nằm ở entity Trường,
    # câu hỏi lại nêu tên chuyên ngành): thử lại với bộ entity mặc định
    if not cells:
        cells = _fetch_cells([(e, f) for e in _defaults() for f in fields])
    return cells


# ── hybrid semantic: BM25 + pgvector + RRF ───────────────────────────

def _chunks_version() -> str:
    """Vân tay của bảng chunks cộng registry_version. Thêm, bớt hay đổi tên
    một chunk là chuỗi này đổi, cache BM25 tự chết (không còn phụ thuộc lệnh
    invalidate thủ công, vốn là bug hẹn giờ khi API server chạy dài)."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS n, coalesce(md5(string_agg(chunk_id, ',' "
            "ORDER BY chunk_id)), '') AS h FROM chunks")
        row = cur.fetchone()
        cur.execute("SELECT value FROM meta WHERE key = 'registry_version'")
        rv = cur.fetchone()
    return f"{rv['value'] if rv else ''}:{row['n']}:{row['h']}"


@lru_cache(maxsize=4)
def _bm25_index(version: str):
    # version chỉ đóng vai khóa cache, thân hàm đọc lại chunks tươi mỗi lần key đổi
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT chunk_id, text, url, snapshot, fetched_at, tier FROM chunks ORDER BY chunk_id")
        rows = cur.fetchall()
    corpus = [tokens(r["text"]) for r in rows]
    return (BM25Okapi(corpus) if corpus else None), rows


def invalidate_bm25_cache() -> None:
    _bm25_index.cache_clear()
    _person_entities.cache_clear()


def hybrid_search(question: str, k: int = TOP_K) -> list[dict]:
    bm25, rows = _bm25_index(_chunks_version())
    if bm25 is None:
        return []
    q_tokens = tokens(question)

    scores = bm25.get_scores(q_tokens)
    bm25_rank = {rows[i]["chunk_id"]: r for r, i in enumerate(
        sorted(range(len(rows)), key=lambda i: -scores[i])[:k * 3])}

    qvec = embed([question])[0]
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT chunk_id FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s",
            (str(qvec), k * 3))
        vec_rank = {r["chunk_id"]: i for i, r in enumerate(cur.fetchall())}

    by_id = {r["chunk_id"]: r for r in rows}
    fused = {}
    for cid in set(bm25_rank) | set(vec_rank):
        s = 0.0
        if cid in bm25_rank:
            s += 1.0 / (RRF_K + bm25_rank[cid] + 1)
        if cid in vec_rank:
            s += 1.0 / (RRF_K + vec_rank[cid] + 1)
        fused[cid] = s

    # độ liên quan tương đương (bucket 0.002) thì tier A trước B trước C
    ranked = sorted(fused, key=lambda cid: (-round(fused[cid] / 0.002),
                                            by_id[cid]["tier"], -fused[cid]))
    return [by_id[cid] for cid in ranked[:k]]


def retrieve(question: str) -> dict:
    cells = structured_lookup(question)
    chunks = hybrid_search(question)
    return {"cells": cells, "chunks": chunks}
