from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    source_type: str
    content: str
    published_at: datetime
    author: str | None = None
    tags: list[str] = field(default_factory=list)
    raw_score: float = 0.0
    fingerprint: str = ""
    category: str | None = None
    score: float = 0.0
    summary: str = ""
