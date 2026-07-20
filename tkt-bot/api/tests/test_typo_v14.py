"""TIP-14: chịu lỗi chính tả, viết tắt, không dấu. Cần DB đã nạp."""
from app.retrieval import structured_lookup, _repair_query, _unknown_acronym


def _fields(cells):
    return {(c["entity"], c["field"]) for c in cells}


def test_unaccented_hits_same_cell():
    cells = structured_lookup("diem chuan phan tich du lieu 2025")
    assert ("CN Phân tích dữ liệu", "diem_thpt_2025_A00_A01") in _fields(cells)


def test_abbrev_hp_expands():
    assert _repair_query("hp tieng viet") == "hoc phi tieng viet"
    cells = structured_lookup("hp tieng viet")
    assert ("Trường Đại học Kinh tế - Luật", "hoc_phi_tieng_viet_2025_2026") in _fields(cells)


def test_fuzzy_consonant_typo():
    # "chuiên" (norm -> "chuien") sửa về "chuyen"
    assert "chuyen" in _repair_query("chuien nganh nao")
    cells = structured_lookup("chuiên ngành nào của ngành toán kinh te")
    assert ("Ngành Toán kinh tế", "chuyen_nganh_2025") in _fields(cells)


def test_person_name_unaccented():
    cells = structured_lookup("thay Le Hong Nhat con day ko")
    assert any(c["field"] == "ghi_chu" and c["entity"] == "Lê Hồng Nhật" for c in cells)


def test_anti_guess_unknown_acronym():
    # AC TIP-14: viết tắt lạ 'cntt' không đoán bừa học phí chung, trả rỗng (honest-null)
    assert _unknown_acronym("hoc phi cntt") == "cntt"
    assert structured_lookup("hoc phi cntt") == []


def test_no_false_acronym_on_normal_words():
    # từ tự nhiên có nguyên âm không bị coi là viết tắt lạ
    assert _unknown_acronym("hoc phi chuong trinh tieng viet") is None
