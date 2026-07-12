"""Registry v1.1: 3 field mới và person-name lookup. Cần DB đã nạp v1.1."""
from app.retrieval import structured_lookup


def test_lich_tuyen_sinh_2026_grounded():
    cells = structured_lookup("lịch nhận hồ sơ xét tuyển 2026 thế nào")
    assert any(c["field"] == "lich_tuyen_sinh_2026" and c["status"] != "null"
               for c in cells), cells


def test_lich_tuyen_sinh_wrong_year_empty():
    # hỏi lịch 2025 thì không được trả ô 2026
    cells = structured_lookup("lịch nhận hồ sơ xét tuyển 2025")
    assert not any(c["field"] == "lich_tuyen_sinh_2026" for c in cells)


def test_person_lookup_retired_lecturer():
    cells = structured_lookup("thầy Lê Hồng Nhật còn giảng dạy không")
    ghi_chu = [c for c in cells if c["field"] == "ghi_chu"]
    assert ghi_chu and "Nghỉ hưu" in str(ghi_chu[0]["value_json"])


def test_tien_than_truong():
    cells = structured_lookup("tiền thân của trường là gì")
    assert any(c["field"] == "tien_than" for c in cells), cells


def test_chi_tieu_2026_still_null_path():
    # hồi quy honest-null: chi_tieu chỉ có dữ liệu 2025
    assert structured_lookup("chỉ tiêu 2026") == []
