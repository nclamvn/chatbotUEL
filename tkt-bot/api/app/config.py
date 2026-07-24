import os

APP_VERSION = "0.1.0"
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://tkt:tkt@localhost:5433/tktbot")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
# COMPOSER_MODEL được giữ làm alias tương thích với cấu hình cũ.
ANTHROPIC_MODEL = os.environ.get(
    "ANTHROPIC_MODEL", os.environ.get("COMPOSER_MODEL", "claude-sonnet-4-6"))
# hash: embedder tất định offline cho dev/test · e5: multilingual-e5-small qua fastembed
EMBEDDINGS = os.environ.get("EMBEDDINGS", "hash")
EMBEDDING_DIM = 384
BOT_NAME = os.environ.get("BOT_NAME", "Trợ lý Khoa Toán Kinh tế")
CONTACT_EMAIL = "khoatkt@uel.edu.vn"
CONTACT_PHONE = "(028) 3724 4555 (6601)"

# Giới hạn độ dài câu hỏi (TIP-11.1), quá thì 422 kèm gợi ý rút gọn
MAX_QUESTION_LEN = int(os.environ.get("MAX_QUESTION_LEN", "500"))

SITE_ADDRESS = os.environ.get("SITE_ADDRESS", "")


def _derive_cors_origins() -> list[str]:
    """CORS_ORIGINS liệt kê tường minh; bỏ trống thì suy từ SITE_ADDRESS.
    Mặc định rỗng nghĩa là cấm mọi cross-origin, an toàn vì web và api chung
    origin sau Caddy. Dev gọi API cross-origin thì khai CORS_ORIGINS."""
    explicit = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
    if explicit:
        return explicit
    site = SITE_ADDRESS.strip()
    if site and not site.startswith(":"):
        host = site.split()[0]  # Caddy site address có thể kèm tùy chọn
        return [f"https://{host}"]
    return []


CORS_ORIGINS = _derive_cors_origins()

# TIP-13 staging: MODE tường minh. "template" = đường fallback, KHÔNG bao giờ tự
# bật LLM ở staging kể cả khi có key (đổi mode là việc của TIP-08 có bằng chứng).
MODE = os.environ.get("MODE", "template")

# Cờ AUTHORITATIVE: LLM chỉ chạy khi có ít nhất một provider VÀ mode khác
# template. Thứ tự provider được cố định OpenAI -> Anthropic -> template.
LLM_ENABLED = bool(OPENAI_API_KEY or ANTHROPIC_API_KEY) and MODE != "template"

# Basic auth cho trang admin telemetry (tách riêng với gate mời của web)
ADMIN_USER = os.environ.get("ADMIN_USER", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")
