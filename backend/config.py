from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    embedding_model: str = "all-MiniLM-L6-v2"
    sqlite_path: Path = BACKEND_DIR / "data" / "app.db"
    chroma_path: Path = BACKEND_DIR / "chroma_data"
    chunk_size: int = 700
    chunk_overlap: int = 100
    default_top_k: int = 5
    max_top_k: int = 8
    max_content_chars: int = 20_000
    url_timeout_seconds: float = 15.0
    url_max_bytes: int = 200_000
    min_chunk_score: float = 0.15

settings = Settings()
