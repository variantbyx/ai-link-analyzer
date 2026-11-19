import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider: 'auto' (cascade: Gemini -> Ollama -> Offline), 'gemini', 'ollama', or 'offline'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

# Google Gemini Settings (Free Tier)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Local Ollama Settings (Zero Cost Local LLM)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# In-memory Caching for Quota Preservation
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() in ("true", "1", "yes")

# Server Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "4000"))
