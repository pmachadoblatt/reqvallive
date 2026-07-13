"""ReqValLive — configuração via ambiente / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mqtt_broker: str = "127.0.0.1"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic: str = "conceptio/reqval"
    mqtt_client_id: str = "reqvallive"

    host: str = "127.0.0.1"
    port: int = 8080


settings = Settings()
