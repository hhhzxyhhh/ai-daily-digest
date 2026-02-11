from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from models import NewsItem

if TYPE_CHECKING:
    from llm import LLMRouter

logger = logging.getLogger(__name__)


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


def filter_relevance_keyword(
    items: list[NewsItem],
) -> tuple[list[NewsItem], list[NewsItem], list[NewsItem]]:
    """
    第一层：关键词预过滤（黑名单+白名单）
    返回: (白名单通过, 灰色地带, 黑名单过滤)
    """
    # 黑名单：明显不相关的关键词（体育、娱乐、政治等）
    BLACKLIST = [
        # 体育
        "superbowl",
        "super bowl",
        "nfl",
        "nba",
        "nhl",
        "mlb",
        "fifa",
        "world cup",
        "football",
        "soccer",
        "basketball",
        "baseball",
        "hockey",
        "olympics",
        "playoff",
        "championship",
        "tournament",
        "athlete",
        "coach",
        "player stats",
        # 娱乐
        "celebrity",
        "movie",
        "film",
        "actor",
        "actress",
        "oscar",
        "grammy",
        "music album",
        "concert",
        "box office",
        "hollywood",
        "netflix show",
        # 政治（除非与AI政策相关）
        "election results",
        "president elect",
        "senate vote",
        "congress bill",
        "political campaign",
        "democrat",
        "republican",
        # 其他
        "weather",
        "traffic",
        "crime",
        "accident",
        "obituary",
        "real estate",
        "stock market crash",
        "cryptocurrency price",
    ]

    # 白名单：明确与AI相关的关键词
    WHITELIST = [
        # 核心AI术语
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "llm",
        "large language model",
        "gpt",
        "transformer",
        "diffusion model",
        "generative ai",
        "genai",
        "foundation model",
        "multimodal",
        # 中文AI术语（扩充）
        "人工智能",
        "机器学习",
        "深度学习",
        "神经网络",
        "大模型",
        "生成式",
        "大语言模型",
        "智能体",
        "多模态",
        "具身智能",
        "扩散模型",
        "开源模型",
        "算力",
        "推理",
        "训练",
        "微调",
        "预训练",
        "提示词",
        "提示工程",
        "向量数据库",
        "检索增强",
        "知识图谱",
        "强化学习",
        "迁移学习",
        "自然语言处理",
        "计算机视觉",
        "语音识别",
        "图像生成",
        "文本生成",
        # 学术来源
        "arxiv",
        "neurips",
        "icml",
        "iclr",
        "cvpr",
        "acl",
        "emnlp",
        # 知名AI项目/公司
        "openai",
        "anthropic",
        "deepmind",
        "hugging face",
        "langchain",
        "pytorch",
        "tensorflow",
        "stable diffusion",
        "midjourney",
        # AI应用领域
        "computer vision",
        "natural language processing",
        "nlp",
        "speech recognition",
        "reinforcement learning",
        "autonomous",
        "chatbot",
        "ai agent",
    ]

    whitelist_pass: list[NewsItem] = []
    greyzone: list[NewsItem] = []
    blacklist_filtered: list[NewsItem] = []

    for item in items:
        text = f"{item.title} {item.content}".lower()

        # 检查黑名单
        if any(keyword in text for keyword in BLACKLIST):
            blacklist_filtered.append(item)
            continue

        # 检查白名单
        if any(keyword in text for keyword in WHITELIST):
            whitelist_pass.append(item)
        else:
            # 灰色地带：既不在黑名单也不在白名单
            greyzone.append(item)

    logger.info(
        f"Keyword filter: {len(whitelist_pass)} whitelist, {len(greyzone)} greyzone, {len(blacklist_filtered)} blacklist"
    )
    return whitelist_pass, greyzone, blacklist_filtered


def filter_ai_relevance_llm(items: list[NewsItem], router: LLMRouter) -> list[NewsItem]:
    """
    第二层：LLM精准判断（仅用于灰色地带）
    批量处理以减少API调用
    """
    if not items:
        return []

    # 批量处理，每批10条
    batch_size = 10
    relevant_items: list[NewsItem] = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]

        # 构建批量判断的prompt
        news_list = "\n".join(
            [
                f"{idx}. 标题: {item.title}\n   内容: {item.content[:200]}"
                for idx, item in enumerate(batch)
            ]
        )

        prompt = f"""判断以下新闻是否与人工智能/机器学习/深度学习/大语言模型相关。

评判标准：
- 相关：新闻主题是AI技术、AI应用、AI研究、AI产品、AI行业动态
- 不相关：只是偶然提到AI，但主题是其他领域（如体育、娱乐、传统科技等）

请只返回JSON数组，格式: [{{"index": 0, "relevant": true}}, {{"index": 1, "relevant": false}}, ...]

新闻列表:
{news_list}

只返回JSON数组，不要其他内容。"""

        try:
            response = router.complete(prompt)
            # 尝试解析JSON响应
            # 清理可能的markdown代码块标记
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            results = json.loads(response)

            for result in results:
                idx = result.get("index", -1)
                is_relevant = result.get("relevant", False)
                if 0 <= idx < len(batch) and is_relevant:
                    relevant_items.append(batch[idx])

            logger.info(
                f"LLM relevance filter: batch {i // batch_size + 1}, {len([r for r in results if r.get('relevant')])} relevant out of {len(batch)}"
            )

        except Exception as e:
            logger.warning(f"LLM relevance filter failed for batch {i // batch_size + 1}: {e}")
            # 失败时保守处理：保留所有
            relevant_items.extend(batch)

    return relevant_items


def classify_with_llm(items: list[NewsItem], router: LLMRouter) -> None:
    """
    第三层：LLM智能分类
    批量处理并直接修改items的category属性
    """
    if not items:
        return

    # 批量处理，每批8条
    batch_size = 8

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]

        # 构建批量分类的prompt
        news_list = "\n".join(
            [
                f"{idx}. 标题: {item.title}\n   内容: {item.content[:300]}"
                for idx, item in enumerate(batch)
            ]
        )

        prompt = f"""对以下AI新闻进行分类。

类别定义：
- 论文与研究：学术论文、研究成果、技术突破
- 产品与发布：产品发布、版本更新、新功能上线
- 行业动态：融资、并购、政策法规、市场分析
- 教程与观点：技术教程、博客文章、观点分析、最佳实践
- 开源项目：GitHub项目、开源工具、代码库
- 应用案例：实际应用、案例研究、落地场景

请只返回JSON数组，格式: [{{"index": 0, "category": "论文与研究"}}, {{"index": 1, "category": "产品与发布"}}, ...]

新闻列表:
{news_list}

只返回JSON数组，不要其他内容。"""

        try:
            response = router.complete(prompt)
            # 清理可能的markdown代码块标记
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            results = json.loads(response)

            for result in results:
                idx = result.get("index", -1)
                category = result.get("category", "其他")
                if 0 <= idx < len(batch):
                    batch[idx].category = category

            logger.info(f"LLM classification: batch {i // batch_size + 1} completed")

        except Exception as e:
            logger.warning(f"LLM classification failed for batch {i // batch_size + 1}: {e}")
            # 失败时回退到关键词分类
            for item in batch:
                if not item.category:
                    item.category = classify(item)


def classify(item: NewsItem) -> str:
    """增强版分类器,使用更丰富的关键词"""
    text = f"{item.title} {item.content}".lower()

    # 论文与研究 - 添加更多学术关键词
    if any(
        k in text
        for k in [
            "paper",
            "arxiv",
            "论文",
            "research",
            "study",
            "icml",
            "neurips",
            "iclr",
            "cvpr",
            "emnlp",
            "acl",
        ]
    ):
        return "论文与研究"

    # 产品与发布
    if any(
        k in text
        for k in ["release", "发布", "launch", "announce", "v1.", "v2.", "v3.", "版本", "新版"]
    ):
        return "产品与发布"

    # 行业动态
    if any(
        k in text
        for k in [
            "funding",
            "融资",
            "acquisition",
            "并购",
            "policy",
            "regulation",
            "投资",
            "收购",
            "估值",
        ]
    ):
        return "行业动态"

    # 教程与观点
    if any(
        k in text
        for k in ["tutorial", "guide", "教程", "how to", "入门", "实战", "blog", "观点", "分析"]
    ):
        return "教程与观点"

    # 开源项目
    if any(
        k in text for k in ["github", "repo", "open-source", "开源", "star", "fork", "trending"]
    ):
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
        0.5  # 基础权重
        + 0.3 * recency_factor  # 时效性权重（降低了影响）
        + 0.2 * content_factor  # 内容完整度权重
    )

    return round(final_score, 3)


def select_diverse_items(items: list[NewsItem], max_count: int = 10) -> list[NewsItem]:
    """
    三维度多样性选择器:
    - 确保每个来源类型最多占 40% 配额
    - 确保每个具体来源最多占 3 条（防止单一来源霸榜）
    - 确保每个内容类别最多占 35% 配额
    避免单一来源或单一类别主导结果
    """
    # 按评分排序
    sorted_items = sorted(items, key=lambda x: x.score, reverse=True)

    # 每个来源类型、具体来源和类别的最大配额
    max_per_source_type = max(2, int(max_count * 0.4))
    max_per_source = 3  # 每个具体来源最多3条
    max_per_category = max(2, int(max_count * 0.35))

    source_type_counts: dict[str, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)
    selected: list[NewsItem] = []

    for item in sorted_items:
        if len(selected) >= max_count:
            break

        source_type_ok = source_type_counts[item.source_type] < max_per_source_type
        source_ok = source_counts[item.source] < max_per_source
        category_ok = category_counts[item.category or "其他"] < max_per_category

        if source_type_ok and source_ok and category_ok:
            selected.append(item)
            source_type_counts[item.source_type] += 1
            source_counts[item.source] += 1
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
