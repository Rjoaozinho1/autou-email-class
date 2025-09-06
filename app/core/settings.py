import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

# Paths
APP_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Groq / LLM settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
CLASSIFICATION_TEMPERATURE = 0.0

