"""Style gate REQ-05/REQ-06. Pure function, không mạng, không LLM, thuần deterministic.

Luật cứng (chặn, bắt viết lại):
- EMDASH    : chứa em-dash hoặc en-dash
- SEMICOLON : dấu chấm phẩy xuất hiện quá một lần
- COMMA_VA  : chuỗi ", và" hoặc ", &"

Luật mềm (cảnh báo):
- REPEAT    : từ nội dung lặp quá hai lần trong một đoạn, sau chuẩn hóa dấu
              và lowercase, bỏ stopwords tiếng Việt. Gợi ý đồng nghĩa từ
              bảng trong constitution.
"""
import re
import unicodedata
from collections import Counter

from .constitution import SYNONYMS

HARD, SOFT = "hard", "soft"

STOPWORDS = {
    "va", "cua", "cac", "la", "co", "cho", "voi", "duoc", "trong", "mot",
    "nhung", "nay", "do", "khi", "da", "dang", "se", "khong", "cung", "nhu",
    "de", "tu", "theo", "ve", "ban", "minh", "thi", "ma", "o", "ra", "nen",
    "hay", "hoac", "nhe", "a", "em", "anh", "chi", "tai", "tren", "duoi",
    "sau", "truoc", "bao", "nhieu", "gi", "nao", "ai", "day", "kia", "roi",
    "van", "chi", "con", "nua", "lai", "rat", "qua", "hon", "nhat", "phai",
    "can", "muon", "biet", "thay", "hoi", "vay", "thoi", "den", "di", "vao",
    "bang", "vi", "neu", "moi", "tung", "hai", "ba", "bon", "nam", "sau",
}


def _norm(s: str) -> str:
    s = s.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def lint(text: str) -> list[dict]:
    violations = []

    dashes = [c for c in text if c in "—–"]
    if dashes:
        violations.append({
            "code": "EMDASH", "severity": HARD,
            "detail": f"chứa {len(dashes)} ký tự em-dash/en-dash, thay bằng dấu phẩy hoặc tách câu"})

    n_semi = text.count(";")
    if n_semi > 1:
        violations.append({
            "code": "SEMICOLON", "severity": HARD,
            "detail": f"dấu chấm phẩy xuất hiện {n_semi} lần, tối đa một lần"})

    if re.search(r",\s*(và\b|&)", text):
        violations.append({
            "code": "COMMA_VA", "severity": HARD,
            "detail": "có dấu phẩy ngay trước \"và\", bỏ dấu phẩy hoặc viết lại vế câu"})

    for para in re.split(r"\n\s*\n|\n(?=- )", text):
        norm_para = _norm(para)
        flagged_phrases = set()
        for phrase, alts in SYNONYMS.items():
            n = len(re.findall(r"\b" + re.escape(_norm(phrase)) + r"\b", norm_para))
            if n > 2:
                flagged_phrases.add(_norm(phrase))
                violations.append({
                    "code": "REPEAT", "severity": SOFT,
                    "detail": f"\"{phrase}\" lặp {n} lần trong một đoạn",
                    "suggestion": f"thay bằng: {', '.join(alts)}"})
        words = re.findall(r"[a-z]{4,}", norm_para)
        for w, n in Counter(words).items():
            if n > 2 and w not in STOPWORDS and not any(
                    w in ph for ph in flagged_phrases):
                violations.append({
                    "code": "REPEAT", "severity": SOFT,
                    "detail": f"từ \"{w}\" lặp {n} lần trong một đoạn",
                    "suggestion": "dùng từ đồng nghĩa hoặc đại từ thay thế"})
    return violations


def hard_violations(violations: list[dict]) -> list[dict]:
    return [v for v in violations if v["severity"] == HARD]
