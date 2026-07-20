"""TIP-19: gọi nhân sự bằng tên riêng + kính ngữ ("cô Uyên", "thầy Sơn").
Tên riêng duy nhất -> resolve; trùng -> honest-null (không trả nhầm địa chỉ). Cần DB đã nạp."""
from app.retrieval import (structured_lookup, _person_ambiguous, _given_name_hits,
                           ambiguous_persons)
from app.composer import compose_fallback


def _entities(cells):
    return {c["entity"] for c in cells}


def test_unique_given_name_resolves():
    # "thầy Sơn" chỉ có một Nguyễn Phúc Sơn -> resolve, không cần đủ họ tên
    cells = structured_lookup("thay Son la ai")
    assert "Nguyễn Phúc Sơn" in _entities(cells)


def test_unique_given_name_cv_topic():
    # tên riêng duy nhất + hỏi CV vẫn nhắm đúng field
    cells = structured_lookup("co An day mon gi")
    assert "Lê Thị Thanh An" in _entities(cells)


def test_ambiguous_given_name_is_null_not_address():
    # "cô Uyên" ứng 3 người (Huỳnh Tố Uyên, Phạm Hoàng Uyên, Võ Thị Lệ Uyển):
    # KHÔNG đoán, KHÔNG rơi xuống rule 'ở đâu' trả nhầm địa chỉ Khoa/trường.
    assert _person_ambiguous("co uyen hoc o dau") is True
    cells = structured_lookup("cô Uyên học ở đâu?")
    assert _entities(cells) == set() or "Khoa Toán Kinh tế" not in _entities(cells)
    # không có ô địa chỉ nào lọt ra
    assert not any(c["field"].startswith("dia_chi") for c in cells)


def test_ambiguous_nhat():
    # "thầy Nhật" ứng Lê Hồng Nhật và Trương Quang Nhật -> nhập nhằng
    assert _person_ambiguous("thay nhat con day khong") is True


def test_full_name_still_resolves_ambiguous_given():
    # đủ họ tên thì khớp thẳng người đúng dù tên riêng trùng
    cells = structured_lookup("Cô Phạm Hoàng Uyên học tiến sĩ ở đâu?")
    assert "Phạm Hoàng Uyên" in _entities(cells)
    assert "Huỳnh Tố Uyên" not in _entities(cells)


def test_given_name_needs_title():
    # tên riêng trùng từ thường mà KHÔNG có kính ngữ thì không kích hoạt
    hits, ambiguous = _given_name_hits("hoc phi nam nay co cao khong")
    assert hits == [] and ambiguous is False


def test_title_not_fuzzed_to_thac():
    # "thay" không bị fuzzy nghiền về "thac" (bẫy học bổng thạc sĩ)
    cells = structured_lookup("thay Son la ai")
    assert "Nguyễn Phúc Sơn" in _entities(cells)


def test_ambiguous_candidates_listed():
    # "cô Uyên" liệt kê đủ 3 ứng viên (Uyển gộp vì norm bỏ dấu)
    cands = ambiguous_persons("cô Uyên học ở đâu?")
    assert set(cands) == {"Huỳnh Tố Uyên", "Phạm Hoàng Uyên", "Võ Thị Lệ Uyển"}


def test_full_name_not_ambiguous_candidates():
    assert ambiguous_persons("Cô Phạm Hoàng Uyên học tiến sĩ ở đâu?") == []
    assert ambiguous_persons("thay Son la ai") == []


def test_compose_fallback_asks_which_person():
    # composer dựng câu hỏi-lại kèm followup 'X là ai?' thay vì null chung
    r = {"cells": [], "chunks": [],
         "ambiguous_persons": ["Huỳnh Tố Uyên", "Phạm Hoàng Uyên", "Võ Thị Lệ Uyển"]}
    out = compose_fallback("co uyen la ai", "factual", r)
    assert out["status"] == "null"
    md = out["answer_markdown"]
    assert "Phạm Hoàng Uyên" in md and "Huỳnh Tố Uyên" in md
    assert out["followups"] and all("là ai" in f for f in out["followups"])
    assert out.get("clarify_names")  # whitelist cho verifier


def test_disambiguation_passes_verifier():
    # REGRESSION: câu hỏi-lại nêu tên riêng phải QUA verifier (clarify_names
    # whitelist), không bị bác rồi rơi xuống null chung. Không có số trong câu.
    from app.retrieval import retrieve
    from app.composer import compose
    from app.verifier import verify
    q = "Cô Uyên học ở đâu?"
    r = retrieve(q)
    assert r.get("ambiguous_persons")
    raw, lookup = compose(q, "factual", r)
    chk = verify(raw["answer_markdown"], lookup, q, raw.get("clarify_names"))
    assert chk["ok"], chk["feedback"]
    assert "Phạm Hoàng Uyên" in raw["answer_markdown"]
