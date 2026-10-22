"""Read configuration at application creation; importing this module changes nothing."""
import os

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dev_mode: bool = False
    provider: Literal["mock", "ollama"] = "mock"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "exaone3.5:7.8b-instruct-q4_K_M"
    timeout_seconds: float = Field(default=120, gt=0, le=600)
    num_ctx: int = Field(default=8192, ge=2048, le=32768)
    num_predict: int = Field(default=512, ge=64, le=2048)

    @classmethod
    def from_env(cls):
        names = {
            "CHARACTER_CHAT_DEV": "dev_mode", "CHARACTER_CHAT_PROVIDER": "provider", "OLLAMA_BASE_URL": "ollama_url",
            "OLLAMA_MODEL": "ollama_model", "OLLAMA_TIMEOUT_SECONDS": "timeout_seconds",
            "OLLAMA_NUM_CTX": "num_ctx", "OLLAMA_NUM_PREDICT": "num_predict",
        }
        return cls(**{field: os.environ[name] for name, field in names.items() if name in os.environ})
