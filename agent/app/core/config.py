import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Ensure repo .env values win, even if OPENAI_API_KEY exists as an empty inherited env var.
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)


class AgentSettings(BaseModel):
    agent_name: str = "STE Execution Agent"
    version: str = "0.1.0"
    openai_api_key: str = ""


settings = AgentSettings(openai_api_key=os.getenv("OPENAI_API_KEY", "").strip())
