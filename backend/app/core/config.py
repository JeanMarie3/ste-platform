import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Ensure repo .env values win, even if OPENAI_API_KEY exists as an empty inherited env var.
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)


class Settings(BaseModel):
    app_name: str = "STE Control Plane"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    base_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = base_dir / "data"
    sqlite_path: Path = data_dir / "ste.db"
    agent_base_url: str = "http://localhost:8010"
    backend_public_base_url: str = ""
    openai_api_key: str = ""
    openai_webhook_secret: str = ""


settings = Settings(
    backend_public_base_url=os.getenv("BACKEND_PUBLIC_BASE_URL", "").strip(),
    openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
    openai_webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET", "").strip(),
)
settings.data_dir.mkdir(parents=True, exist_ok=True)
