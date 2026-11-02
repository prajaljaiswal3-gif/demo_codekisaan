import os
import shutil
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "codekisaan-dev-secret-key-agri-seva-2026")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    
    # Detect Vercel / AWS Lambda Serverless execution environment
    IS_SERVERLESS = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    # Database configuration (SQLite for MVP, ready for MySQL migration)
    if IS_SERVERLESS:
        TMP_DIR = Path(tempfile.gettempdir())
        DB_PATH = TMP_DIR / "codekisaan.db"
        bundled_db = BASE_DIR / "codekisaan.db"
        if not DB_PATH.exists() and bundled_db.exists():
            try:
                shutil.copy(bundled_db, DB_PATH)
            except Exception:
                pass
        UPLOAD_FOLDER = TMP_DIR / "uploads"
    else:
        DB_PATH = BASE_DIR / "codekisaan.db"
        UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"

    DATABASE_URI = f"sqlite:///{DB_PATH}"
    
    # File Upload Security Settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 Megabytes limit
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # External Weather Service Keys
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "").strip()
    DEFAULT_DISTRICT = os.getenv("DEFAULT_DISTRICT", "Pune")
    
    # Trilingual Language Support
    LANGUAGES = {
        "en": "English",
        "hi": "हिन्दी (Hindi)",
        "mr": "मराठी (Marathi)"
    }
    DEFAULT_LANGUAGE = "mr"  # Default to Marathi for Maharashtra rural farmers

# Ensure upload directory exists safely
try:
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
