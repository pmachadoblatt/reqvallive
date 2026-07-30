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

    # LLM local (OpenAI-compatible: Ollama Conceptio)
    llm_base_url: str = "https://ollama.conceptio.com.br/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen3.6:35b"
    llm_timeout_seconds: float = 180.0

    # Teamwork Cloud / SysML v2 REST (lab CONCEPTIO)
    twc_base_url: str = "https://161.24.23.18:8443"
    twc_sysml_api_prefix: str = "/sysmlv2-api/api"
    twc_auth_login_path: str = "/authentication/api/login"
    twc_username: str = ""
    twc_password: str = ""
    twc_token: str = ""
    twc_verify_ssl: bool = False
    twc_timeout_seconds: float = 30.0

    # SysON local (Docker) — ver deploy/syson/README.md
    syson_base_url: str = "http://127.0.0.1:8081"
    syson_api_prefix: str = "/api/rest"
    syson_timeout_seconds: float = 30.0

    host: str = "127.0.0.1"
    port: int = 8080


settings = Settings()
