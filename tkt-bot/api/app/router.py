"""Router intent: factual | interpretive | oos | smalltalk.
Một lệnh gọi nhỏ few-shot trả JSON. Không có API key thì dùng heuristic offline
(cùng nhãn, phục vụ dev/test), đường nào cũng trả về một trong bốn intent.
"""
import json
import re

from .config import ANTHROPIC_API_KEY, ROUTER_MODEL
from .retrieval import norm

INTENTS = ("factual", "interpretive", "oos", "smalltalk")

FEW_SHOT = [
    ("điểm chuẩn phân tích dữ liệu 2025 bao nhiêu", "factual"),
    ("trưởng khoa là ai", "factual"),
    ("học phí chương trình tiếng anh", "factual"),
    ("học ngành này ra trường làm gì", "interpretive"),
    ("con gái học toán kinh tế có hợp không", "interpretive"),
    ("nên đầu tư coin nào bây giờ", "oos"),
    ("làm hộ bài tập xác suất thống kê", "oos"),
    ("chào bạn", "smalltalk"),
    ("cảm ơn nhé", "smalltalk"),
]

_SMALLTALK = r"^(chao|xin chao|hello|hi|cam on|thanks|tam biet|bye|ok|okay)\b|^(ban la ai|ban ten gi)"
_OOS = (r"dau tu|coin|crypto|chung khoan|co phieu|vay tien|ca do|lo de|"
        r"lam ho bai|giai ho bai|bai tap|chinh tri|ton giao|người yêu|nguoi yeu")
_FACTUAL = (r"diem chuan|diem trung tuyen|hoc phi|chi tieu|ma tuyen sinh|ma nganh|"
            r"truong khoa|pho truong khoa|thu ky|truong bo mon|giang vien|tin chi|hoc ky|"
            r"dia chi|email|dien thoai|thanh lap|bo mon|chuyen nganh|la ai|bao nhieu|nam nao|o dau")


def _heuristic(question: str) -> str:
    q = norm(question)
    if re.search(_SMALLTALK, q):
        return "smalltalk"
    if re.search(_OOS, q):
        return "oos"
    if re.search(_FACTUAL, q):
        return "factual"
    return "interpretive"


def classify(question: str) -> str:
    if not ANTHROPIC_API_KEY:
        return _heuristic(question)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        examples = "\n".join(f'- "{q}" -> {i}' for q, i in FEW_SHOT)
        msg = client.messages.create(
            model=ROUTER_MODEL,
            max_tokens=50,
            system=("Phân loại câu hỏi gửi tới bot tuyển sinh Khoa Toán Kinh tế UEL. "
                    "Trả về JSON duy nhất {\"intent\": \"factual|interpretive|oos|smalltalk\"}.\n"
                    "factual: hỏi con số, tên riêng, thông tin tra cứu được.\n"
                    "interpretive: hỏi nhận định, định hướng, trải nghiệm học tập.\n"
                    "oos: ngoài phạm vi tuyển sinh và thông tin Khoa.\n"
                    "smalltalk: chào hỏi, cảm ơn, xã giao.\n"
                    f"Ví dụ:\n{examples}"),
            messages=[{"role": "user", "content": question}],
        )
        from . import telemetry
        telemetry.incr_counter("llm_calls_router")
        telemetry.incr_counter("llm_tokens_in_router", msg.usage.input_tokens)
        telemetry.incr_counter("llm_tokens_out_router", msg.usage.output_tokens)
        print(f"[router] model={msg.model} in={msg.usage.input_tokens} out={msg.usage.output_tokens}")
        intent = json.loads(msg.content[0].text.strip()).get("intent", "")
        return intent if intent in INTENTS else _heuristic(question)
    except Exception:
        return _heuristic(question)
