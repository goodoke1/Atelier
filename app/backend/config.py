"""Central configuration, read from environment variables."""
import os
from dotenv import load_dotenv

# Automatically load the .env file if it exists
load_dotenv()

# Storage locations (overridable for tests / docker volumes)
DB_PATH = os.environ.get("FASHION_AI_DB", os.path.join(os.path.dirname(__file__), "data", "fashion_ai.db"))
UPLOAD_DIR = os.environ.get("FASHION_AI_UPLOADS", os.path.join(os.path.dirname(__file__), "uploads"))

# AI provider selection
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "claude").lower()

# Claude
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Ollama (Defaults to localhost since Docker hasn't been built yet!)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llava")

# When no API key is configured, the app runs in a graceful "stub" mode so the
# UI and tests still work end-to-end without external calls.
STUB_MODE = os.environ.get("FASHION_AI_STUB", "").lower() in ("1", "true", "yes")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
