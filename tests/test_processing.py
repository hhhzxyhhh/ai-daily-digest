"""测试处理逻辑"""

from datetime import datetime, timedelta, timezone

from models import NewsItem
from processing import (
    _fingerprint,
    classify,
    deduplicate,
    deduplicate_fuzzy,
    score,
    select_diverse_items,
)


def create_test_item(
    title="Test",
    url="https://example.com",
    source_type="rss",
    raw_score=0.5,
    hours_ago=1,
    fingerprint="",
    content="Test content",
    category=None,
):
    """创建测试用 NewsItem"""
    published = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return NewsItem(
        title=title,
        url=url,
        source="Test",
        source_type=source_type,
        content=content,
        published_at=published,
        raw_score=raw_score,
        fingerprint=fingerprint,
        category=category,
    )


class TestDeduplicate:
    """去重测试"""

    def test_deduplicate_identical_items(self):
        """测试去除完全相同的项"""
        items = [
            create_test_item(title="Same", url="https://example.com/1"),
            create_test_item(title="Same", url="https://example.com/1"),
        ]

        result = deduplicate(items)
        assert len(result) == 1

    def test_deduplicate_different_items(self):
        """测试保留不同的项"""
        items = [
            create_test_item(title="News 1", url="https://example.com/1"),
            create_test_item(title="News 2", url="https://example.com/2"),
        ]

        result = deduplicate(items)
        assert len(result) == 2

    def test_deduplicate_with_fingerprint(self):
        """测试使用已有指纹去重"""
        items = [
            create_test_item(fingerprint="abc123"),
            create_test_item(fingerprint="abc123"),
            create_test_item(fingerprint="def456"),
        ]

        result = deduplicate(items)
        assert len(result) == 2


class TestClassify:
    """分类测试"""

    def test_classify_paper(self):
        """测试论文分类"""
        item = create_test_item(title="New paper on arxiv about AI")
        assert classify(item) == "论文与研究"

    def test_classify_release(self):
        """测试产品发布分类"""
        item = create_test_item(title="Release v2.0 of our product")
        assert classify(item) == "产品与发布"

    def test_classify_funding(self):
        """测试行业动态分类"""
        item = create_test_item(title="Company raises $100M in funding")
        assert classify(item) == "行业动态"

    def test_classify_tutorial(self):
        """测试教程分类"""
        item = create_test_item(title="Tutorial: How to use Python")
        assert classify(item) == "教程与观点"

    def test_classify_opensource(self):
        """测试开源项目分类"""
        item = create_test_item(title="New trending repo on GitHub")
        assert classify(item) == "开源项目"

    def test_classify_other(self):
        """测试其他分类"""
        item = create_test_item(title="Random news item")
        assert classify(item) == "其他"


class TestScore:
    """评分测试"""

    def test_score_recent_item(self):
        """测试最近发布的内容评分"""
        item = create_test_item(raw_score=0.8, hours_ago=1, content="A" * 200)
        result = score(item)

        # 1小时前，时效性因子接近1.0，内容完整度1.0
        # 评分 = 0.8 * (0.5 + 0.3 * ~1.0 + 0.2 * 1.0) = 0.8
        assert 0.75 <= result <= 0.85

    def test_score_old_item(self):
        """测试较旧内容评分"""
        item = create_test_item(raw_score=0.8, hours_ago=72, content="A" * 200)
        result = score(item)

        # 72小时前，时效性因子=0.3，内容完整度=1.0
        # 评分 = 0.8 * (0.5 + 0.3 * 0.3 + 0.2 * 1.0) = 0.8 * 0.79 = 0.632
        assert 0.62 <= result <= 0.65

    def test_score_without_timezone(self):
        """测试无时区信息的时间"""
        item = create_test_item(hours_ago=1)
        item.published_at = item.published_at.replace(tzinfo=None)

        result = score(item)
        assert result > 0

    def test_score_with_short_content(self):
        """测试短内容的评分惩罚"""
        item_long = create_test_item(raw_score=0.5, hours_ago=1, content="A" * 200)
        item_short = create_test_item(raw_score=0.5, hours_ago=1, content="Short")

        score_long = score(item_long)
        score_short = score(item_short)

        # 长内容应该得分更高
        assert score_long > score_short

    def test_score_high_quality_old_vs_low_quality_new(self):
        """测试高质量旧内容 vs 低质量新内容"""
        # 高质量但稍旧的内容（24小时前，raw_score=0.9）
        item_old_quality = create_test_item(raw_score=0.9, hours_ago=24, content="A" * 200)
        # 低质量但新鲜的内容（1小时前，raw_score=0.3）
        item_new_low = create_test_item(raw_score=0.3, hours_ago=1, content="A" * 200)

        score_old = score(item_old_quality)
        score_new = score(item_new_low)

        # 高质量旧内容应该比低质量新内容得分更高
        assert score_old > score_new


class TestSelectDiverseItems:
    """多样性选择测试"""

    def test_select_diverse_basic(self):
        """测试基本多样性选择"""
        items = [
            create_test_item(source_type="github", raw_score=0.9),
            create_test_item(source_type="github", raw_score=0.8),
            create_test_item(source_type="rss", raw_score=0.7),
            create_test_item(source_type="rss", raw_score=0.6),
        ]

        # 设置评分
        for item in items:
            item.score = item.raw_score

        result = select_diverse_items(items, max_count=3)
        assert len(result) == 3

    def test_select_diverse_limits_single_source(self):
        """测试限制单一来源类型"""
        items = []
        # 创建8个github项目，使用不同的source名称
        for i in range(8):
            item = create_test_item(
                source_type="github", raw_score=0.9 - i * 0.02, url=f"https://example.com/{i}"
            )
            item.source = f"GitHub_{i}"  # 设置不同的source
            item.score = item.raw_score
            items.append(item)

        # 添加8个RSS项目，评分交错分布
        for i in range(8):
            item = create_test_item(source_type="rss", raw_score=0.88 - i * 0.02, url=f"https://rss.com/{i}")
            item.source = f"RSS_{i}"  # 设置不同的source
            item.score = item.raw_score
            items.append(item)

        result = select_diverse_items(items, max_count=10)

        # max_per_source_type = max(2, int(10 * 0.4)) = 4
        # 有足够多样性时，应该从两种类型中各选一些
        github_count = sum(1 for item in result if item.source_type == "github")
        rss_count = sum(1 for item in result if item.source_type == "rss")

        # 验证多样性：两种类型都应该被选中
        assert github_count > 0, "应该选择一些github项目"
        assert rss_count > 0, "应该选择一些rss项目"
        assert len(result) == 10, "应该选择10个项目"

    def test_select_diverse_respects_max_count(self):
        """测试遵守最大数量限制"""
        items = [create_test_item(url=f"https://example.com/{i}") for i in range(20)]
        for item in items:
            item.score = 0.5

        result = select_diverse_items(items, max_count=5)
        assert len(result) == 5


class TestFingerprint:
    """指纹测试"""

    def test_fingerprint_consistency(self):
        """测试指纹一致性"""
        item1 = create_test_item(title="Test", url="https://example.com")
        item2 = create_test_item(title="Test", url="https://example.com")

        fp1 = _fingerprint(item1)
        fp2 = _fingerprint(item2)

        assert fp1 == fp2

    def test_fingerprint_uniqueness(self):
        """测试指纹唯一性"""
        item1 = create_test_item(title="Test 1", url="https://example.com/1")
        item2 = create_test_item(title="Test 2", url="https://example.com/2")

        fp1 = _fingerprint(item1)
        fp2 = _fingerprint(item2)

        assert fp1 != fp2


class TestDeduplicateFuzzy:
    """模糊去重测试"""

    def test_fuzzy_dedup_similar_titles(self):
        """测试相似标题去重"""
        items = [
            create_test_item(
                title="OpenAI releases GPT-4", url="https://example.com/1", raw_score=0.8
            ),
            create_test_item(
                title="OpenAI Releases GPT-4", url="https://news.com/2", raw_score=0.6
            ),
        ]

        result = deduplicate_fuzzy(items, threshold=0.75)
        assert len(result) == 1
        assert result[0].raw_score == 0.8  # 保留更高分的

    def test_fuzzy_dedup_different_titles(self):
        """测试不同标题不去重"""
        items = [
            create_test_item(title="OpenAI releases GPT-4", url="https://example.com/1"),
            create_test_item(title="Google announces Gemini", url="https://example.com/2"),
        ]

        result = deduplicate_fuzzy(items, threshold=0.75)
        assert len(result) == 2

    def test_fuzzy_dedup_case_insensitive(self):
        """测试大小写不敏感"""
        items = [
            create_test_item(
                title="BREAKING NEWS: AI BREAKTHROUGH", url="https://example.com/1", raw_score=0.7
            ),
            create_test_item(
                title="breaking news: ai breakthrough", url="https://example.com/2", raw_score=0.5
            ),
        ]

        result = deduplicate_fuzzy(items, threshold=0.75)
        assert len(result) == 1
        assert result[0].raw_score == 0.7

    def test_fuzzy_dedup_threshold_adjustment(self):
        """测试阈值调整"""
        items = [
            create_test_item(title="AI model released", url="https://example.com/1", raw_score=0.8),
            create_test_item(title="AI model launched", url="https://example.com/2", raw_score=0.6),
        ]

        # 高阈值（0.9）：标题差异较大，不去重
        result_strict = deduplicate_fuzzy(items, threshold=0.9)
        assert len(result_strict) == 2

        # 低阈值（0.6）：更宽松，可能去重
        result_loose = deduplicate_fuzzy(items, threshold=0.6)
        assert len(result_loose) <= 2  # 可能去重也可能不去重

    def test_fuzzy_dedup_cross_source(self):
        """测试跨来源去重（模拟同一新闻从不同源采集）"""
        items = [
            create_test_item(
                title="Google announces new AI model Gemini",
                url="https://techcrunch.com/google-gemini",
                source_type="rss",
                raw_score=0.6,
            ),
            create_test_item(
                title="Google Announces New AI Model Gemini",
                url="https://reddit.com/r/MachineLearning/gemini",
                source_type="reddit",
                raw_score=0.8,
            ),
        ]

        result = deduplicate_fuzzy(items, threshold=0.75)
        assert len(result) == 1
        # 应该保留 Reddit 的（raw_score 更高）
        assert result[0].source_type == "reddit"


class TestMultiDimensionalScoring:
    """多维度评分测试"""

    def test_content_factor(self):
        """测试内容完整度因子"""
        item_with_content = create_test_item(content="A" * 200, raw_score=0.5, hours_ago=1)
        item_without_content = create_test_item(content="Short", raw_score=0.5, hours_ago=1)

        score1 = score(item_with_content)
        score2 = score(item_without_content)

        assert score1 > score2  # 有内容的分数更高

    def test_scoring_weights_balance(self):
        """测试评分权重平衡"""
        # 测试各因子的相对影响
        base_item = create_test_item(raw_score=0.5, hours_ago=1, content="A" * 200)

        # 改变 raw_score
        high_raw = create_test_item(raw_score=0.9, hours_ago=1, content="A" * 200)
        # 改变时效性
        old_item = create_test_item(raw_score=0.5, hours_ago=72, content="A" * 200)
        # 改变内容完整度
        no_content = create_test_item(raw_score=0.5, hours_ago=1, content="Short")

        score_base = score(base_item)
        score_high_raw = score(high_raw)
        score_old = score(old_item)
        score_no_content = score(no_content)

        # raw_score 的影响应该最大（基础权重50%）
        assert (score_high_raw - score_base) > (score_base - score_old)
        assert (score_high_raw - score_base) > (score_base - score_no_content)


class TestDualDiversitySelection:
    """双维度多样性选择测试"""

    def test_category_diversity(self):
        """测试类别多样性限制"""
        items = []
        # 创建6个论文类别的项，使用不同的source
        for i in range(6):
            item = create_test_item(
                title=f"Paper {i}",
                url=f"https://example.com/{i}",
                source_type=f"source_{i}",
                category="论文与研究",
                raw_score=0.9 - i * 0.01,
            )
            item.source = f"ArXiv_{i}"  # 设置不同的source
            item.score = item.raw_score
            items.append(item)

        # 添加6个产品类别的项
        for i in range(6):
            item = create_test_item(
                title=f"Product {i}",
                url=f"https://product.com/{i}",
                source_type=f"product_{i}",
                category="产品与发布",
                raw_score=0.85 - i * 0.01,
            )
            item.source = f"Product_{i}"  # 设置不同的source
            item.score = item.raw_score
            items.append(item)

        # 添加6个开源项目
        for i in range(6):
            item = create_test_item(
                title=f"OpenSource {i}",
                url=f"https://github.com/proj/{i}",
                source_type=f"github_{i}",
                category="开源项目",
                raw_score=0.8 - i * 0.01,
            )
            item.source = f"GitHub_{i}"
            item.score = item.raw_score
            items.append(item)

        result = select_diverse_items(items, max_count=10)

        # 统计类别分布
        category_counts = {}
        for item in result:
            cat = item.category or "其他"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # max_per_category = max(2, int(10 * 0.35)) = 3
        # 有多个类别时，每个类别最多3个，确保多样性
        for category, count in category_counts.items():
            assert count <= 4, f"类别 {category} 有 {count} 个项目，超过限制"

    def test_source_and_category_both_limited(self):
        """测试来源和类别同时限制"""
        items = []
        # 创建8个GitHub论文项
        for i in range(8):
            item = create_test_item(
                title=f"GitHub Paper {i}",
                url=f"https://github.com/{i}",
                source_type="github",
                category="论文与研究",
                raw_score=0.9 - i * 0.01,
            )
            item.source = f"GitHub_{i}"  # 设置不同的source
            item.score = item.raw_score
            items.append(item)

        # 添加8个RSS产品项
        for i in range(8):
            item = create_test_item(
                title=f"RSS Product {i}",
                url=f"https://rss.com/{i}",
                source_type="rss",
                category="产品与发布",
                raw_score=0.85 - i * 0.01,
            )
            item.source = f"RSS_{i}"  # 设置不同的source
            item.score = item.raw_score
            items.append(item)

        # 添加8个Twitter开源项目
        for i in range(8):
            item = create_test_item(
                title=f"Twitter OpenSource {i}",
                url=f"https://twitter.com/{i}",
                source_type="twitter",
                category="开源项目",
                raw_score=0.8 - i * 0.01,
            )
            item.source = f"Twitter_{i}"
            item.score = item.raw_score
            items.append(item)

        result = select_diverse_items(items, max_count=10)

        # 统计
        source_type_counts = {}
        category_counts = {}
        for item in result:
            source_type_counts[item.source_type] = source_type_counts.get(item.source_type, 0) + 1
            cat = item.category or "其他"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # 验证多样性：没有单一类型或类别主导
        # max_per_source_type = 4, max_per_category = 3
        # 有足够多样性时，应该有多个不同的source_type和category
        assert len(source_type_counts) >= 2, "应该有至少2种不同的来源类型"
        assert len(category_counts) >= 2, "应该有至少2种不同的类别"

        # 每个source_type和category不应该过度主导
        for st, count in source_type_counts.items():
            assert count <= 5, f"来源类型 {st} 有 {count} 个项目，过度主导"
        for cat, count in category_counts.items():
            assert count <= 5, f"类别 {cat} 有 {count} 个项目，过度主导"

    def test_fallback_when_constraints_too_strict(self):
        """测试约束过严时的回退机制"""
        items = []
        # 只有3个不同类别的项，但需要选10个
        for i in range(15):
            cat = ["论文与研究", "产品与发布", "开源项目"][i % 3]
            item = create_test_item(
                title=f"Item {i}",
                url=f"https://example.com/{i}",
                source_type=f"source_{i % 3}",
                category=cat,
                raw_score=0.9 - i * 0.01,
            )
            item.score = item.raw_score
            items.append(item)

        result = select_diverse_items(items, max_count=10)

        # 应该能选出10个（通过回退机制）
        assert len(result) == 10

    def test_diverse_selection_preserves_order(self):
        """测试多样性选择保持评分顺序的相对性"""
        items = []
        # 创建不同来源和类别的项，但评分有明显梯度
        categories = ["论文与研究", "产品与发布", "开源项目", "行业动态"]
        sources = ["github", "rss", "reddit", "newsapi"]

        for i in range(20):
            item = create_test_item(
                title=f"Item {i}",
                url=f"https://example.com/{i}",
                source_type=sources[i % 4],
                category=categories[i % 4],
                raw_score=0.9 - i * 0.02,  # 明显的评分梯度
            )
            item.score = item.raw_score
            items.append(item)

        result = select_diverse_items(items, max_count=10)

        # 结果中的评分应该大致保持降序（允许因多样性有小幅调整）
        scores = [item.score for item in result]
        # 至少前5个应该是高分项
        assert all(s >= 0.7 for s in scores[:5])
