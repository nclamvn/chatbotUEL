"""TIP-04: 20 unit test cho style_lint. Pure function, chạy không cần DB."""
from app.style_lint import hard_violations, lint


def codes(text):
    return [v["code"] for v in lint(text)]


def hard_codes(text):
    return [v["code"] for v in hard_violations(lint(text))]


# ── EMDASH (luật cứng 1) ─────────────────────────────────────────────

def test_emdash_blocked():
    assert "EMDASH" in codes("Khoa Toán Kinh tế — đơn vị trẻ của UEL.")


def test_endash_blocked_same_code():
    assert "EMDASH" in codes("Giai đoạn 2019–2025 Khoa phát triển nhanh.")


def test_emdash_is_hard():
    assert "EMDASH" in hard_codes("Điểm chuẩn — mức trúng tuyển năm nay.")


def test_hyphen_allowed():
    assert "EMDASH" not in codes("Năm học 2025-2026 học phí là 31,5 triệu đồng.")


def test_emdash_multiple_reported_once():
    found = [c for c in codes("A — B — C") if c == "EMDASH"]
    assert len(found) == 1


# ── SEMICOLON (luật cứng 2) ──────────────────────────────────────────

def test_two_semicolons_blocked():
    assert "SEMICOLON" in hard_codes("Khoa có hai bộ môn; ba chuyên ngành; một ngành.")


def test_one_semicolon_allowed():
    assert "SEMICOLON" not in codes("Khoa có hai bộ môn; cả hai đều mạnh về định lượng.")


def test_zero_semicolons_allowed():
    assert "SEMICOLON" not in codes("Khoa có hai bộ môn.")


# ── COMMA_VA (luật cứng 3) ───────────────────────────────────────────

def test_comma_va_blocked():
    assert "COMMA_VA" in hard_codes("Khoa dạy toán, và kinh tế.")


def test_comma_va_with_space_blocked():
    assert "COMMA_VA" in hard_codes("Toán,  và kinh tế.")


def test_comma_ampersand_blocked():
    assert "COMMA_VA" in hard_codes("Kinh tế, & tài chính.")


def test_va_without_comma_allowed():
    assert "COMMA_VA" not in codes("Khoa dạy toán và kinh tế.")


def test_comma_vao_not_flagged():
    # "và" phải là nguyên từ, "vào" không tính
    assert "COMMA_VA" not in codes("Nộp hồ sơ trước 17h, vào cổng tuyển sinh của Trường.")


# ── REPEAT (luật mềm 4) ──────────────────────────────────────────────

def test_repeat_diem_chuan_four_times_warns():
    text = ("Điểm chuẩn năm nay tăng nhẹ. Điểm chuẩn A00 là 26.43. "
            "Điểm chuẩn DGNL là 927. Điểm chuẩn các năm đều ổn định.")
    vs = [v for v in lint(text) if v["code"] == "REPEAT"]
    assert vs, "phải cảnh báo REPEAT"
    assert all(v["severity"] == "soft" for v in vs)


def test_repeat_suggestion_from_synonyms():
    text = "Điểm chuẩn cao. Điểm chuẩn thấp. Điểm chuẩn vừa. Điểm chuẩn ổn."
    v = next(v for v in lint(text) if v["code"] == "REPEAT" and "điểm chuẩn" in v["detail"])
    assert "mức trúng tuyển" in v["suggestion"]


def test_repeat_twice_allowed():
    assert "REPEAT" not in codes("Điểm chuẩn A00 là 26.43. Điểm chuẩn DGNL là 927.")


def test_repeat_counts_per_paragraph():
    # ba lần nhưng tách hai đoạn, mỗi đoạn không quá hai
    text = "Điểm chuẩn cao. Điểm chuẩn thấp.\n\nĐiểm chuẩn DGNL là 927."
    assert "REPEAT" not in codes(text)


def test_repeat_normalizes_diacritics_and_case():
    text = "ĐIỂM CHUẨN cao. điểm chuẩn thấp. Diem chuan vừa. Điểm chuẩn ổn."
    assert any(v["code"] == "REPEAT" and "điểm chuẩn" in v["detail"] for v in lint(text))


def test_repeat_ignores_stopwords():
    assert "REPEAT" not in codes(
        "Bạn hỏi thì mình trả lời. Bạn cần thì mình gửi thêm. Bạn chọn nhé.")


# ── tổng hợp ─────────────────────────────────────────────────────────

def test_clean_text_no_violations():
    text = ("Mức trúng tuyển 2025 của CN Phân tích dữ liệu là 26.43 cho tổ hợp A00 và A01. "
            "Bạn cần thêm chi tiết thì xem chip nguồn bên dưới nhé.")
    assert lint(text) == []


def test_khoatkt_not_counted_as_khoa():
    # hồi quy vĩnh viễn: "khoatkt" trong email không được tính là một lần "khoa"
    text = ("Bạn liên hệ Khoa qua email khoatkt@uel.edu.vn nhé. "
            "Văn phòng Khoa mở cửa giờ hành chính.")
    assert "REPEAT" not in codes(text)
