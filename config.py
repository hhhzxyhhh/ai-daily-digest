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

    # DeepSeek
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Moonshot (Kimi)
    moonshot_api_key: str | None = None
    moonshot_model: str = "moonshot-v1-8k"
    moonshot_base_url: str = "https://api.moonshot.cn/v1"

    # Doubao (字节跳动)
    doubao_api_key: str | None = None
    doubao_model: str = "doubao-pro-4k"
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # Claude (Anthropic)
    claude_api_key: str | None = None
    claude_model: str = "claude-3-5-haiku-20241022"
    claude_base_url: str = "https://api.anthropic.com/v1"

    # Gemini (Google)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

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
