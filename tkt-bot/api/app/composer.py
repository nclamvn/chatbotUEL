"""Composer: dựng câu trả lời theo JSON contract từ context retrieval.

Hai đường:
- LLM: Claude API (COMPOSER_MODEL), system prompt là Domain Constitution.
- Fallback deterministic: không LLM, template an toàn từ ô registry. Dùng khi
  thiếu API key, khi LLM lỗi, hoặc khi verifier bác quá hai vòng (REQ-06).
Mọi citation được server dựng lại từ DB, không tin metadata do LLM sinh.
"""
import json

from .config import ANTHROPIC_API_KEY, COMPOSER_MODEL, CONTACT_EMAIL, CONTACT_PHONE
from .constitution import system_prompt

FIELD_LABELS = {
    "diem_thpt_2025_A00_A01": "điểm chuẩn THPT 2025 tổ hợp A00, A01",
    "diem_thpt_2025_D01_D07_X25_X26": "điểm chuẩn THPT 2025 tổ hợp D01, D07, X25, X26",
    "diem_dgnl_2025": "điểm chuẩn đánh giá năng lực 2025",
    "diem_utxtt_2025": "điểm ưu tiên xét tuyển thẳng 2025",
    "chi_tieu_2025": "chỉ tiêu 2025",
    "hoc_phi_tieng_viet_2025_2026": "học phí chương trình tiếng Việt năm học 2025-2026",
    "hoc_phi_tieng_anh_2025_2026": "học phí chương trình tiếng Anh năm học 2025-2026",
    "ma_tuyen_sinh": "mã tuyển sinh",
    "ma_truong": "mã trường",
    "tin_chi": "số tín chỉ",
    "so_hoc_ky": "số học kỳ",
    "so_giang_vien_co_huu": "số giảng viên cơ hữu",
    "co_cau_hoc_vi": "cơ cấu học vị",
    "bo_mon_truc_thuoc": "các bộ môn trực thuộc",
    "chuc_vu": "chức vụ",
    "hoc_ham_hoc_vi": "học hàm học vị",
    "chuyen_mon": "chuyên môn",
    "dia_chi": "địa chỉ",
    "email": "email",
    "dien_thoai": "điện thoại",
    "nam_thanh_lap": "năm thành lập",
    "nam_thanh_lap_bo_mon": "năm thành lập bộ môn",
    "nam_len_khoa": "năm nâng cấp thành khoa",
    "nam_mo_nganh": "năm mở ngành",
    "chuyen_nganh_2025": "các chuyên ngành tuyển sinh 2025",
    "truc_thuoc": "trực thuộc",
    "dinh_huong_nghien_cuu": "định hướng nghiên cứu",
    "triet_ly_giao_duc": "triết lý giáo dục",
    "tam_nhin": "tầm nhìn",
    "ten_day_du": "tên đầy đủ",
}

OOS_ANSWER = (f"Câu này nằm ngoài phạm vi mình hỗ trợ. Mình chỉ trả lời về tuyển sinh"
              f" cùng thông tin của Khoa Toán Kinh tế UEL. Bạn cần trao đổi sâu hơn thì"
              f" liên hệ văn phòng Khoa qua email {CONTACT_EMAIL} hoặc điện thoại {CONTACT_PHONE} nhé.")

NULL_ANSWER = (f"Mình chưa có dữ liệu được kiểm chứng cho câu này nên không đoán."
               f" Bạn hỏi trực tiếp văn phòng Khoa qua email {CONTACT_EMAIL}"
               f" hoặc điện thoại {CONTACT_PHONE} để có thông tin chính thức nhé.")

SMALLTALK_ANSWER = ("Chào bạn, mình là trợ lý của Khoa Toán Kinh tế UEL."
                    " Bạn muốn hỏi về mức trúng tuyển, học phí, chuyên ngành"
                    " hay đội ngũ giảng viên của Khoa?")

DEFAULT_FOLLOWUPS = ["Điểm chuẩn 2025 của từng chuyên ngành?",
                     "Học phí năm học 2025-2026?",
                     "Khoa có những chuyên ngành nào?"]


def build_context(retrieved: dict) -> tuple[str, dict]:
    """Trả về (khối CONTEXT cho LLM, bảng tra id -> bản ghi để dựng citation)."""
    lookup, lines = {}, []
    for cell in retrieved.get("cells", []):
        label = FIELD_LABELS.get(cell["field"], cell["field"])
        lines.append(f"[Ô registry] {cell['entity']} · {label} · trạng thái {cell['status']}")
        for c in cell["claims"]:
            lookup[c["claim_id"]] = {"kind": "claim", **c}
            lines.append(
                f"  ({c['claim_id']}) giá trị: {c['value']} · tier {c['tier']}"
                f" · nguồn {c['source']} · trích: \"{c['evidence_span']}\"")
    for ch in retrieved.get("chunks", []):
        lookup[ch["chunk_id"]] = {"kind": "chunk", **ch}
        lines.append(f"({ch['chunk_id']}) [đoạn văn · tier {ch['tier']} · {ch['snapshot']}]"
                     f" {ch['text'][:500]}")
    return "\n".join(lines), lookup


def _citation_of(rec: dict) -> dict:
    if rec["kind"] == "claim":
        return {"claim_id": rec["claim_id"], "source": rec["source"], "tier": rec["tier"],
                "fetched_at": rec["fetched_at"],
                "evidence_span": rec["evidence_span"], "url": rec["url"]}
    return {"claim_id": rec["chunk_id"], "source": rec["snapshot"], "tier": rec["tier"],
            "fetched_at": rec["fetched_at"],
            "evidence_span": rec["text"][:280], "url": rec["url"]}


def _disputed_ids(retrieved: dict) -> set:
    out = set()
    for cell in retrieved.get("cells", []):
        if cell["status"] == "disputed":
            out.update(str(x) for x in cell["claim_ids"])
    return out


def finalize(raw: dict, lookup: dict, retrieved: dict, intent: str = None) -> dict:
    """Ép contract server-side: citation dựng từ DB, status sửa theo luật cứng."""
    ids = [i for i in raw.get("citation_ids", []) if i in lookup]
    citations = [_citation_of(lookup[i]) for i in ids]
    status = raw.get("status", "null")

    disputed = _disputed_ids(retrieved)
    if any(i in disputed for i in ids):
        status = "disputed"
    # smalltalk là lời chào không chứa fact, được grounded rỗng citation
    if status == "grounded" and not citations and intent != "smalltalk":
        status = "null"
        raw["answer_markdown"] = NULL_ANSWER
    if status in ("null", "oos"):
        citations = []

    return {"answer_markdown": raw.get("answer_markdown", NULL_ANSWER),
            "status": status, "citations": citations,
            "followups": (raw.get("followups") or DEFAULT_FOLLOWUPS)[:3]}


# ── đường fallback deterministic ─────────────────────────────────────

def _fmt_value(v) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    # giá trị liệt kê chứa chấm phẩy: render bullet để không vướng luật văn phong
    if ";" in s:
        items = [x.strip() for x in s.split(";") if x.strip()]
        return "\n" + "\n".join(f"- {x}" for x in items)
    return s


def compose_fallback(question: str, intent: str, retrieved: dict) -> dict:
    if intent == "oos":
        return {"answer_markdown": OOS_ANSWER, "status": "oos", "citation_ids": [],
                "followups": DEFAULT_FOLLOWUPS}
    if intent == "smalltalk":
        return {"answer_markdown": SMALLTALK_ANSWER, "status": "grounded", "citation_ids": [],
                "followups": DEFAULT_FOLLOWUPS}

    cells = retrieved.get("cells", [])
    if not cells:
        return {"answer_markdown": NULL_ANSWER, "status": "null", "citation_ids": [],
                "followups": DEFAULT_FOLLOWUPS}

    lines, ids, any_disputed = [], [], False
    for cell in cells:
        label = FIELD_LABELS.get(cell["field"], cell["field"])
        if cell["status"] == "disputed":
            any_disputed = True
            versions = ", còn ".join(
                f"nguồn {c['source']} (tier {c['tier']}) ghi {_fmt_value(c['value'])}"
                for c in cell["claims"])
            lines.append(f"Về {label} của {cell['entity']}, hai bản ghi đang lệch nhau: {versions}."
                         f" Mình hiển thị cả hai để bạn đối chiếu.")
        else:
            lines.append(f"{cell['entity']}: {label} là {_fmt_value(cell['value_json'])}.")
        ids.extend(c["claim_id"] for c in cell["claims"])

    return {"answer_markdown": "\n\n".join(lines),
            "status": "disputed" if any_disputed else "grounded",
            "citation_ids": ids, "followups": DEFAULT_FOLLOWUPS}


# ── đường LLM ────────────────────────────────────────────────────────

def compose_llm(question: str, intent: str, retrieved: dict, feedback: str = None) -> dict:
    import anthropic
    context, _ = build_context(retrieved)
    user = f"CONTEXT:\n{context or '(trống, không có dữ liệu)'}\n\nINTENT: {intent}\nCÂU HỎI: {question}"
    if feedback:
        user += f"\n\nLẦN TRƯỚC BỊ BÁC, VIẾT LẠI THEO GÓP Ý SAU:\n{feedback}"
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=COMPOSER_MODEL, max_tokens=1200,
        system=system_prompt(),
        messages=[{"role": "user", "content": user}])
    from . import telemetry
    telemetry.incr_counter("llm_calls_composer")
    telemetry.incr_counter("llm_tokens_in_composer", msg.usage.input_tokens)
    telemetry.incr_counter("llm_tokens_out_composer", msg.usage.output_tokens)
    print(f"[composer] model={msg.model} in={msg.usage.input_tokens} out={msg.usage.output_tokens}")
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def compose(question: str, intent: str, retrieved: dict, feedback: str = None) -> tuple[dict, dict]:
    """Trả về (raw contract từ composer, lookup để dựng citation)."""
    _, lookup = build_context(retrieved)
    if ANTHROPIC_API_KEY:
        try:
            return compose_llm(question, intent, retrieved, feedback), lookup
        except Exception as e:
            print(f"[composer] LLM lỗi, dùng fallback: {e}")
    return compose_fallback(question, intent, retrieved), lookup
