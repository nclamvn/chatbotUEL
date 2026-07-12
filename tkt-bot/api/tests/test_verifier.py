"""TIP-04 AC tầng trace: số và tên riêng không truy vết được thì chặn. Cần DB."""
from app.composer import build_context
from app.retrieval import retrieve
from app.verifier import verify


def test_untraced_number_blocked():
    retrieved = retrieve("điểm chuẩn phân tích dữ liệu 2025")
    _, lookup = build_context(retrieved)
    # 25,75 là điểm của chuyên ngành khác, không có trong context này
    check = verify("Mức trúng tuyển là 25,75 điểm.", lookup,
                   "điểm chuẩn phân tích dữ liệu 2025")
    assert not check["ok"]
    assert any(v["code"] == "UNTRACED_NUMBER" and "25,75" in v["detail"]
               for v in check["violations"])


def test_traced_number_passes():
    retrieved = retrieve("điểm chuẩn phân tích dữ liệu 2025")
    _, lookup = build_context(retrieved)
    check = verify("Mức trúng tuyển tổ hợp A00 và A01 là 26.43.", lookup,
                   "điểm chuẩn phân tích dữ liệu 2025")
    assert check["ok"], check["violations"]


def test_untraced_name_blocked():
    retrieved = retrieve("điểm chuẩn phân tích dữ liệu 2025")
    _, lookup = build_context(retrieved)
    check = verify("Bạn liên hệ cô Phạm Hoàng Uyên để biết thêm về 26.43 nhé.",
                   lookup, "điểm chuẩn phân tích dữ liệu 2025")
    assert any(v["code"] == "UNTRACED_NAME" for v in check["violations"])


def test_decimal_comma_dot_equivalent():
    retrieved = retrieve("học phí tiếng việt")
    _, lookup = build_context(retrieved)
    # claim ghi "31,5 triệu đồng", câu trả lời dùng 31.5 vẫn truy vết được
    check = verify("Học phí chương trình tiếng Việt năm thứ nhất là 31.5 triệu đồng.",
                   lookup, "học phí tiếng việt")
    assert not any(v["code"] == "UNTRACED_NUMBER" for v in check["violations"])


# ── mục 0 TIP-08 (L2 chốt 12/07): hai tập allowed tách bạch ─────────

_SRC_LOOKUP = {
    "clm_test1": {
        "kind": "claim", "claim_id": "clm_test1",
        "entity": "Trường Đại học Kinh tế - Luật",
        "value": "Số 669 Quốc lộ 1, Khu phố 3, Phường Linh Xuân",
        "evidence_span": "Số 669 Quốc lộ 1, Khu phố 3, Phường Linh Xuân, TP. Thủ Đức",
        "tier": "C", "source": "diemthi.tuyensinh247.com",
        "url": "https://diemthi.tuyensinh247.com/diem-chuan/QSK.html",
        "fetched_at": "2026-07-12T10:52:00Z",
    }
}


def test_source_name_with_digits_allowed_as_whole_string():
    check = verify("Theo diemthi.tuyensinh247.com, địa chỉ là Số 669 Quốc lộ 1.",
                   _SRC_LOOKUP, "địa chỉ trường ở đâu")
    assert not any(v["code"] == "UNTRACED_NUMBER" for v in check["violations"]), \
        check["violations"]


def test_standalone_number_from_source_name_blocked():
    # "247" đứng rời không có claim giá trị ấy: phải chặn dù nguồn tên chứa 247
    check = verify("Trường tuyển 247 chỉ tiêu cho ngành này.",
                   _SRC_LOOKUP, "chỉ tiêu ngành")
    assert any(v["code"] == "UNTRACED_NUMBER" and "247" in v["detail"]
               for v in check["violations"]), check["violations"]
