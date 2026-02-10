from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM routing
    llm_strategy: str = "fallback"  # primary | fallback | round_robin
    llm_primary_provider: str = "qwen"
    llm_secondary_provider: str = "zhipu"

    # Qwen (DashScope)
    qwen_api_key: str | None = None
    qwen_model: str = "qwen-plus"
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Zhipu
    zhipu_api_key: str | None = None
    zhipu_model: str = "glm-4-flash"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"

    # Email
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_sender: str = ""
    email_password: str = ""
    email_recipients: str = ""

    # Schedule
    schedule_hour: int = 10
    schedule_minute: int = 0
    timezone: str = "Asia/Shanghai"

    # API keys (optional)
    github_token: str | None = None
    newsapi_key: str | None = None
    twitter_bearer_token: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None


def load_settings() -> Settings:
    return Settings()
