import os

APP_VERSION = "0.1.0"
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://tkt:tkt@localhost:5433/tktbot")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
COMPOSER_MODEL = os.environ.get("COMPOSER_MODEL", "claude-sonnet-4-6")
ROUTER_MODEL = os.environ.get("ROUTER_MODEL", "claude-haiku-4-5-20251001")
# hash: embedder tất định offline cho dev/test · e5: multilingual-e5-small qua fastembed
EMBEDDINGS = os.environ.get("EMBEDDINGS", "hash")
EMBEDDING_DIM = 384
BOT_NAME = os.environ.get("BOT_NAME", "Trợ lý Khoa Toán Kinh tế")
CONTACT_EMAIL = "khoatkt@uel.edu.vn"
CONTACT_PHONE = "(028) 3724 4555 (6601)"
