import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "codekisaan-dev-secret-key-agri-seva-2026")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    
    # Database configuration (SQLite for MVP, ready for MySQL migration)
    DB_PATH = BASE_DIR / "codekisaan.db"
    DATABASE_URI = f"sqlite:///{DB_PATH}"
    
    # File Upload Security Settings
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
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

# Ensure upload directory exists
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
