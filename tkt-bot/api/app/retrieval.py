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

from .constitution import ABBREVIATIONS
from .db import connect
from .embeddings import embed

RRF_K = 60
TOP_K = 8

# TIP-14: ngưỡng edit distance chặt. Chọn 2 vì đủ chữa gõ nhầm/thiếu 1-2 ký tự
# ("chuien"->"chuyen", "tuien"->"tuyen") nhưng không nới tới mức lẫn hai field gần
# nhau ("diem"<->"dien", "hoc"<->"hop"). Nhập nhằng (nhiều ứng viên cùng min) thì
# GIỮ NGUYÊN token, không đoán.
FUZZY_MAX = 2


def norm(s: str) -> str:
    s = s.lower().replace("đ", "d")
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def _lev(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > FUZZY_MAX:
        return FUZZY_MAX + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


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
    (r"diem chuan|diem trung tuyen|nguong dau vao|muc trung tuyen|bao nhieu diem|lay bao nhieu"
     r"|diem sat|\bsat\b|xet sat|chung chi quoc te|\b149\b|danh sach 149|uu tien xet tuyen|utxtt",
     "diem", True),
    (r"hoc phi", "hoc_phi", True),
    (r"chi tieu", ["chi_tieu_2025", "chi_tieu_2026"], True),
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
    (r"hoc bong", ["hoc_bong_tien_phong_2026", "hoc_bong_vuot_troi_2026"], True),
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
    if re.search(r"diem sat|\bsat\b|xet sat|chung chi quoc te", q):
        return ["diem_sat_2025"]  # registry chỉ có SAT, chưa tách ACT/A-Level -> nhãn ghi rõ ngưỡng SAT
    if re.search(r"\b149\b|danh sach 149|149 truong", q):
        return ["diem_utxt149_2025"]
    # "ưu tiên xét tuyển thẳng" (thủ khoa trường chuyên/năng khiếu) -> ƯTXTT rõ ràng
    if re.search(r"utxtt|xet tuyen thang|uu tien xet tuyen thang|thu khoa|nang khieu", q):
        return ["diem_utxtt_2025"]
    # "ưu tiên xét tuyển" trần = nhập nhằng HAI ĐÁP ÁN ĐỀU ĐÚNG (ƯTXTT vs danh sách 149):
    # không đoán, trả CẢ HAI ô, mỗi ô một citation (khác cntt = không đáp án nào chắc -> hỏi lại)
    if re.search(r"uu tien xet tuyen", q):
        return ["diem_utxtt_2025", "diem_utxt149_2025"]
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


def _year_filter(q: str, fields):
    """Field gắn năm trong tên: câu hỏi nêu năm thì CHỈ giữ field khớp năm đó
    (vd 'chỉ tiêu 2026' -> chi_tieu_2026, không kéo chi_tieu_2025 trả nhầm năm).
    Câu không nêu năm -> giữ nguyên. Không field nào khớp -> [] (honest-null,
    vd hỏi 2026 mà chỉ có dữ liệu 2025)."""
    years = set(re.findall(r"\b(20\d\d)\b", q))
    if not years:
        return list(fields)
    return [f for f in fields if years & set(re.findall(r"20\d\d", f))]


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
                 "dinh_huong_nghien_cuu", "noi_dao_tao_tien_si",
                 "chuyen_nganh_tien_si", "nam_ve_truong", "hoc_vi_nam_dat", "bo_mon")

# TIP-18: câu hỏi nhắm đúng khía cạnh CV thì trả đúng field đó, không dump cả người
# (tránh kéo ô disputed như hoc_ham của cô Uyên vào câu hỏi về học vấn).
PERSON_TOPIC = [
    (r"hoc.*o dau|dao tao.*o dau|tot nghiep.*o dau|du hoc|tien si.*o dau|nuoc nao|hoc tien si|lam tien si",
     ["noi_dao_tao_tien_si", "chuyen_nganh_tien_si"]),
    (r"chuyen nganh tien si|nganh tien si|tien si nganh gi", ["chuyen_nganh_tien_si", "noi_dao_tao_tien_si"]),
    (r"ve truong nam nao|ve khoa nam nao|ve uel|nam nao ve|nam.*ve truong", ["nam_ve_truong"]),
    (r"bo mon nao|thuoc bo mon", ["bo_mon"]),
    (r"hoc vi|hoc ham|bang cap", ["hoc_ham_hoc_vi", "hoc_vi_nam_dat"]),
]


@lru_cache(maxsize=1)
def _person_entities() -> tuple:
    """Danh sách entity loại nhan_su, hỏi được bằng tên (Registry v1.1)."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT entity FROM registry_cells
                       WHERE field='loai' AND value_json::text LIKE '%nhan_su%'""")
        return tuple(r["entity"] for r in cur.fetchall())


# TIP-19: người dùng thật gọi nhân sự bằng tên riêng ("cô Uyên", "thầy Sơn"), không
# đủ họ tên. Tên riêng = từ cuối (tiếng Việt). Chỉ soi khi có kính ngữ đứng NGAY
# trước để tránh trùng từ thường ("an", "hoa", "vũ"). Tên riêng DUY NHẤT thì resolve;
# TRÙNG (Uyên×3, Nhật×2 sau khi bỏ dấu) thì nhập nhằng -> không đoán.
_TITLE = r"(?:co|thay|giang vien|giao vien)"


@lru_cache(maxsize=1)
def _given_name_map() -> dict:
    """tên riêng (norm, từ cuối) -> tuple entity nhân sự mang tên đó."""
    m: dict[str, list[str]] = {}
    for p in _person_entities():
        toks = norm(p).split()
        if toks:
            m.setdefault(toks[-1], []).append(p)
    return {k: tuple(v) for k, v in m.items()}


def _given_name_hits(q: str) -> tuple[list[str], bool]:
    """(entity resolve chắc chắn, có_nhập_nhằng). Nhập nhằng = tên riêng có kính
    ngữ nhưng ứng nhiều người."""
    gmap = _given_name_map()
    hits, ambiguous = [], False
    for m in re.finditer(_TITLE + r"\s+(\w+)", q):
        ents = gmap.get(m.group(1))
        if not ents:
            continue
        if len(ents) == 1:
            hits.append(ents[0])
        else:
            ambiguous = True
    return hits, ambiguous


def _person_ambiguous(q: str) -> bool:
    """Câu chỉ nêu tên riêng TRÙNG (vd "cô Uyên") mà không đủ họ tên và không có
    nhân sự nào khớp: cấm đoán để khỏi rơi xuống rule 'ở đâu' trả nhầm địa chỉ."""
    _, ambiguous = _given_name_hits(q)
    return ambiguous and not any(norm(p) in q for p in _person_entities())


def ambiguous_persons(question: str) -> list[str]:
    """Danh sách ứng viên khi câu nhập nhằng tên riêng (vd 'cô Uyên' -> 3 người),
    giữ thứ tự, bỏ trùng. Rỗng nếu không nhập nhằng. Dùng cho câu hỏi-lại."""
    q = _fuzzy_fix(_expand_abbrev(norm(question)))
    if not _person_ambiguous(q):
        return []
    gmap = _given_name_map()
    seen, out = set(), []
    for m in re.finditer(_TITLE + r"\s+(\w+)", q):
        for e in gmap.get(m.group(1), ()) if len(gmap.get(m.group(1), ())) > 1 else ():
            if e not in seen:
                seen.add(e)
                out.append(e)
    return out


def _person_lookup(q: str) -> list[dict]:
    hits = [p for p in _person_entities() if norm(p) in q]
    for p in _given_name_hits(q)[0]:
        if p not in hits:
            hits.append(p)
    if not hits:
        return []
    fields = next((fs for pat, fs in PERSON_TOPIC if re.search(pat, q)), None)
    return _fetch_cells([(p, f) for p in hits for f in (fields or PERSON_FIELDS)])


@lru_cache(maxsize=1)
def _vocab() -> frozenset:
    """Từ vựng đích cho fuzzy: từ trong FIELD_RULES + alias entity + giá trị viết
    tắt + token tên người. Từ hợp lệ nằm sẵn đây nên không bị sửa nhầm."""
    words = set()
    for rule in FIELD_RULES:
        # bỏ escape regex (\b, \d...) trước khi bóc từ, kẻo "\bemail\b" thành "bemailb"
        pat = re.sub(r"\\[a-z]", " ", rule[0])
        words |= {w for w in re.findall(r"[a-z]+", pat) if len(w) >= 3}
    for alias, _ent in ENTITY_ALIASES:
        words |= {w for w in alias.split() if len(w) >= 2}
    for exp in ABBREVIATIONS.values():
        words |= {w for w in exp.split() if len(w) >= 2}
    for p in _person_entities():
        words |= {w for w in norm(p).split() if len(w) >= 2}
    # token hợp lệ mà _detect_* dùng nhưng không nằm trong FIELD_RULES/alias:
    # qualifier ngôn ngữ + tổ hợp + phương thức. Có mặt ở đây để fuzzy không sửa nhầm.
    words |= {"viet", "anh", "dgnl", "utxtt", "danh", "gia", "nang", "luc",
              "uu", "tien", "xet", "chuong", "trinh", "thac", "cao", "sau", "dai",
              # TIP-19: kính ngữ, có mặt để fuzzy không nghiền ("thay"->"thac")
              "thay", "giang", "vien", "giao"}
    return frozenset(words)


def _expand_abbrev(q: str) -> str:
    out = []
    for t in q.split():
        out.extend(ABBREVIATIONS[t].split() if t in ABBREVIATIONS else [t])
    return " ".join(out)


def _fuzzy_fix(q: str) -> str:
    """Sửa gõ nhầm token về từ vựng gần nhất (distance ≤ FUZZY_MAX, duy nhất).
    Chỉ nhắm từ vựng ≥3 ký tự để không co token lạ về viết tắt 2 ký tự."""
    vocab = _vocab()
    out = []
    for t in q.split():
        if len(t) >= 4 and t not in vocab:
            cands = [(w, _lev(t, w)) for w in vocab if len(w) >= 3]
            cands = [(w, d) for w, d in cands if d <= FUZZY_MAX]
            if cands:
                md = min(d for _, d in cands)
                best = [w for w, d in cands if d == md]
                if len(best) == 1:
                    out.append(best[0])
                    continue
        out.append(t)
    return " ".join(out)


def _repair_query(q: str) -> str:
    return _fuzzy_fix(_expand_abbrev(q))


def _unknown_acronym(q: str) -> str | None:
    """Token viết tắt lạ (chuỗi phụ âm không nguyên âm, 2-5 ký tự) không giải được
    = qualifier chưa rõ (vd 'cntt'). Có nó thì cấm đoán, trả honest-null."""
    vocab = _vocab()
    for t in q.split():
        if t.isalpha() and 2 <= len(t) <= 5 and not (set(t) & set("aeiou")) \
                and t not in vocab:
            return t
    return None


def structured_lookup(question: str) -> list[dict]:
    q1 = _expand_abbrev(norm(question))
    # TIP-14 anti-guess: viết tắt lạ chưa giải được thì không đoán (chặn TRƯỚC fuzzy
    # để 'cntt' không bị co về 'cn')
    if _unknown_acronym(q1):
        return []
    q = _fuzzy_fix(q1)

    role_cells = _role_lookup(q)
    if role_cells:
        return role_cells

    person_cells = _person_lookup(q)
    if person_cells:
        return person_cells
    # TIP-19: "cô Uyên" (3 người) không đủ họ tên -> honest-null, khỏi rơi xuống
    # rule 'ở đâu' bên dưới trả nhầm địa chỉ Khoa.
    if _person_ambiguous(q):
        return []

    fields = None
    for pattern, f, year_bound in FIELD_RULES:
        if re.search(pattern, q):
            if f == "diem":
                fields = _detect_diem_fields(q)
            elif f == "hoc_phi":
                fields = _detect_hoc_phi_fields(q)
            else:
                fields = f
            if year_bound:
                fields = _year_filter(q, fields)
                if not fields:
                    return []
            break
    if fields is None:
        return []

    # TIP-18 bẫy: học bổng dữ liệu chỉ có bậc đại học; hỏi thạc sĩ/cao học/NCS thì
    # không đoán bừa học bổng đại học, trả honest-null. Soi q1 (trước fuzzy) để
    # 'thac si' không bị fuzzy nghiền mất.
    if fields[0].startswith("hoc_bong") and re.search(r"thac si|cao hoc|sau dai hoc|nghien cuu sinh", q1):
        return []

    def _defaults() -> list[str]:
        # chi_tieu_2026 chỉ công bố ở cấp chuyên-ngành (khác chi_tieu_2025 cấp Trường)
        if fields[0].startswith(("diem_", "ma_tuyen")) or fields[0] == "chi_tieu_2026":
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
    _given_name_map.cache_clear()
    _vocab.cache_clear()


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
    # viết tắt lạ (vd 'cntt'): đừng để chunk đoán bừa, honest-null cả hai đường
    if _unknown_acronym(_expand_abbrev(norm(question))):
        return {"cells": [], "chunks": []}
    cells = structured_lookup(question)
    # TIP-19: tên riêng trùng (vd 'cô Uyên') -> hỏi lại đúng người; clear chunks để
    # tất định (không để chunk CV của một người lọt thành câu trả lời) + đính ứng viên
    if not cells:
        amb = ambiguous_persons(question)
        if amb:
            return {"cells": [], "chunks": [], "ambiguous_persons": amb}
    return {"cells": cells, "chunks": hybrid_search(question)}
