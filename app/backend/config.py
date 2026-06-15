"""Central configuration, read from environment variables."""
import os

# Storage locations
DB_PATH = os.environ.get("FASHION_AI_DB", os.path.join(os.path.dirname(__file__), "data", "fashion_ai.db"))
UPLOAD_DIR = os.environ.get("FASHION_AI_UPLOADS", os.path.join(os.path.dirname(__file__), "uploads"))

# AI provider selection
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "stub").lower()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
