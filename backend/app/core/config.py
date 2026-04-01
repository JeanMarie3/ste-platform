import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Ensure repo .env values win, even if OPENAI_API_KEY exists as an empty inherited env var.
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)

_DEFAULT_BASE_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_DIR = _DEFAULT_BASE_DIR / "data"
_DEFAULT_SQLITE_PATH = _DEFAULT_DATA_DIR / "ste.db"


class Settings(BaseModel):
    app_name: str = "STE Control Plane"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    base_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = base_dir / "data"
    sqlite_path: Path = data_dir / "ste.db"
    database_url: str = f"sqlite:///{(data_dir / 'ste.db').as_posix()}"
    agent_base_url: str = "http://localhost:8010"
    backend_public_base_url: str = ""
    openai_api_key: str = ""
    openai_webhook_secret: str = ""


settings = Settings(
    database_url=os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE_PATH.as_posix()}").strip(),
    agent_base_url=os.getenv("AGENT_BASE_URL", "http://localhost:8010").strip(),
    backend_public_base_url=os.getenv("BACKEND_PUBLIC_BASE_URL", "").strip(),
    openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
    openai_webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET", "").strip(),
)
settings.data_dir.mkdir(parents=True, exist_ok=True)
