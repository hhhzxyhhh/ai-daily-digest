"""测试配置加载"""

from config import Settings


def test_settings_defaults():
    """测试默认配置值"""
    settings = Settings(
        email_sender="test@example.com",
        email_password="test123",
        email_recipients="user@example.com",
    )

    assert settings.llm_strategy == "fallback"
    assert settings.llm_primary_provider == "qwen"
    assert settings.llm_secondary_provider == "zhipu"
    assert settings.schedule_hour == 10
    assert settings.schedule_minute == 0
    assert settings.timezone == "Asia/Shanghai"


def test_settings_custom_values():
    """测试自定义配置"""
    settings = Settings(
        llm_strategy="primary",
        llm_primary_provider="zhipu",
        schedule_hour=8,
        email_sender="test@example.com",
        email_password="test123",
        email_recipients="user@example.com",
    )

    assert settings.llm_strategy == "primary"
    assert settings.llm_primary_provider == "zhipu"
    assert settings.schedule_hour == 8


def test_email_settings():
    """测试邮件配置"""
    settings = Settings(
        email_smtp_host="smtp.test.com",
        email_smtp_port=465,
        email_sender="sender@test.com",
        email_password="pass123",
        email_recipients="user1@test.com,user2@test.com",
    )

    assert settings.email_smtp_host == "smtp.test.com"
    assert settings.email_smtp_port == 465
    assert settings.email_sender == "sender@test.com"
    assert "," in settings.email_recipients
