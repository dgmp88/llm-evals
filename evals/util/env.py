from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).parents[2]

ENV_FILE = PACKAGE_DIR / ".env"


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API key")
    GEMINI_API_KEY: Optional[str] = Field(None, description="Gemini API key")
    TOGETHERAI_API_KEY: Optional[str] = Field(None, description="TogetherAI API key")
    NEON_POSTGRES: str = Field(description="Postgres connection string")

    DEV: bool = Field(default=False, description="Whether to run in dev mode")
    PORT: int = Field(default=10000, description="Port to run the server on")


ENV = Env()  # type: ignore
