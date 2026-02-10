"""测试数据模型"""
import pytest
from datetime import datetime, timezone
from models import NewsItem


def test_newsitem_creation():
    """测试 NewsItem 基本创建"""
    item = NewsItem(
        title="Test News",
        url="https://example.com/news",
        source="Test Source",
        source_type="rss",
        content="Test content",
        published_at=datetime.now(timezone.utc)
    )
    
    assert item.title == "Test News"
    assert item.url == "https://example.com/news"
    assert item.source_type == "rss"
    assert item.raw_score == 0.0
    assert item.score == 0.0
    assert item.tags == []


def test_newsitem_with_optional_fields():
    """测试 NewsItem 可选字段"""
    item = NewsItem(
        title="Test",
        url="https://example.com",
        source="Source",
        source_type="github",
        content="Content",
        published_at=datetime.now(timezone.utc),
        author="John Doe",
        tags=["ai", "ml"],
        raw_score=0.8,
        category="论文与研究"
    )
    
    assert item.author == "John Doe"
    assert len(item.tags) == 2
    assert "ai" in item.tags
    assert item.raw_score == 0.8
    assert item.category == "论文与研究"


def test_newsitem_fingerprint():
    """测试指纹字段"""
    item = NewsItem(
        title="Test",
        url="https://example.com",
        source="Source",
        source_type="rss",
        content="Content",
        published_at=datetime.now(timezone.utc),
        fingerprint="abc123"
    )
    
    assert item.fingerprint == "abc123"
