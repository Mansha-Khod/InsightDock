from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

REPORTS_DIR = DATA_DIR / "reports"
PROCESSED_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

MODELS_DIR = BASE_DIR / "models"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")