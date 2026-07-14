"""ReqValLive — configuração via ambiente / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MQTT — defaults do laboratório
    mqtt_broker: str = "161.24.23.15"
    mqtt_port: int = 1883
    mqtt_username: str = "marco"
    mqtt_password: str = ""
    mqtt_topic: str = "conceptio/reqval"
    mqtt_client_id: str = "reqvallive"

    # LLM local (OpenAI-compatible: Ollama / Open WebUI)
    llm_base_url: str = "http://161.24.23.15:11434/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen3.6:35b"
    llm_timeout_seconds: float = 120.0

    host: str = "127.0.0.1"
    port: int = 8080


settings = Settings()
