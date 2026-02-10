from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Iterable

from models import NewsItem


def deduplicate(items: Iterable[NewsItem]) -> list[NewsItem]:
    """精确去重：基于 fingerprint"""
    seen = set()
    unique: list[NewsItem] = []
    for item in items:
        if not item.fingerprint:
            item.fingerprint = _fingerprint(item)
        if item.fingerprint in seen:
            continue
        seen.add(item.fingerprint)
        unique.append(item)
    return unique


def deduplicate_fuzzy(items: list[NewsItem], threshold: float = 0.75) -> list[NewsItem]:
    """
    模糊去重：基于标题相似度
    用于去除跨来源的重复新闻（标题相似但 URL 不同）
    """
    unique: list[NewsItem] = []
    for item in items:
        is_dup = False
        for existing in unique:
            ratio = SequenceMatcher(None, item.title.lower(), existing.title.lower()).ratio()
            if ratio >= threshold:
                # 保留 raw_score 更高的那个
                if item.raw_score > existing.raw_score:
                    unique.remove(existing)
                    unique.append(item)
                is_dup = True
                break
        if not is_dup:
            unique.append(item)
    return unique


def classify(item: NewsItem) -> str:
    """增强版分类器,使用更丰富的关键词"""
    text = f"{item.title} {item.content}".lower()
    
    # 论文与研究 - 添加更多学术关键词
    if any(k in text for k in ["paper", "arxiv", "论文", "research", "study", 
                                "icml", "neurips", "iclr", "cvpr", "emnlp", "acl"]):
        return "论文与研究"
    
    # 产品与发布
    if any(k in text for k in ["release", "发布", "launch", "announce", 
                                "v1.", "v2.", "v3.", "版本", "新版"]):
        return "产品与发布"
    
    # 行业动态
    if any(k in text for k in ["funding", "融资", "acquisition", "并购", 
                                "policy", "regulation", "投资", "收购", "估值"]):
        return "行业动态"
    
    # 教程与观点
    if any(k in text for k in ["tutorial", "guide", "教程", "how to", 
                                "入门", "实战", "blog", "观点", "分析"]):
        return "教程与观点"
    
    # 开源项目
    if any(k in text for k in ["github", "repo", "open-source", "开源", 
                                "star", "fork", "trending"]):
        return "开源项目"
    
    return "其他"


def score(item: NewsItem) -> float:
    """
    多维度评分算法:
    - raw_score: 基础质量分（来源权威度或社交热度）
    - recency_factor: 时效性因子
    - content_factor: 内容完整度因子
    """
    now = datetime.now(timezone.utc)
    
    # 处理无时区信息的时间
    if item.published_at.tzinfo is None:
        published = item.published_at.replace(tzinfo=timezone.utc)
    else:
        published = item.published_at
    
    age_hours = max((now - published).total_seconds() / 3600, 1)
    
    # 时效性因子: 72小时内平滑衰减 (1.0 -> 0.3)
    recency_factor = max(0.3, 1.0 - (age_hours / 72))
    
    # 内容完整度因子: 有实际内容 > 只有标题
    content_factor = 1.0 if len(item.content) > 100 else 0.7
    
    # 多维度综合评分
    final_score = item.raw_score * (
        0.5                           # 基础权重
        + 0.3 * recency_factor        # 时效性权重（降低了影响）
        + 0.2 * content_factor        # 内容完整度权重
    )
    
    return round(final_score, 3)


def select_diverse_items(items: list[NewsItem], max_count: int = 10) -> list[NewsItem]:
    """
    双维度多样性选择器: 
    - 确保每个来源类型最多占 40% 配额
    - 确保每个内容类别最多占 35% 配额
    避免单一来源或单一类别主导结果
    """
    # 按评分排序
    sorted_items = sorted(items, key=lambda x: x.score, reverse=True)
    
    # 每个来源类型和类别的最大配额
    max_per_source = max(2, int(max_count * 0.4))
    max_per_category = max(2, int(max_count * 0.35))
    
    source_counts: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)
    selected: list[NewsItem] = []
    
    for item in sorted_items:
        if len(selected) >= max_count:
            break
        
        source_ok = source_counts[item.source_type] < max_per_source
        category_ok = category_counts[item.category or "其他"] < max_per_category
        
        if source_ok and category_ok:
            selected.append(item)
            source_counts[item.source_type] += 1
            category_counts[item.category or "其他"] += 1
    
    # 如果因限制太严导致不够，放宽限制再补充
    if len(selected) < max_count:
        for item in sorted_items:
            if item not in selected and len(selected) < max_count:
                selected.append(item)
    
    return selected


def _fingerprint(item: NewsItem) -> str:
    base = f"{item.title}::{item.url}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

