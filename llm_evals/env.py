from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PARENT_DIR = Path(__file__).parent.parent

ENV_FILE = PARENT_DIR / ".env"


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    OPENAI_API_KEY: Optional[str] = Field(description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(description="Anthropic API key")
    GEMINI_API_KEY: Optional[str] = Field(description="Gemini API key")
    TOGETHERAI_API_KEY: Optional[str] = Field(description="TogetherAI API key")
    NEON_POSTGRES: str = Field(description="Postgres connection string")


ENV = Env()  # type: ignore
