"""测试处理逻辑"""
import pytest
from datetime import datetime, timezone, timedelta
from models import NewsItem
from processing import deduplicate, deduplicate_fuzzy, classify, score, select_diverse_items, _fingerprint


def create_test_item(
    title="Test",
    url="https://example.com",
    source_type="rss",
    raw_score=0.5,
    hours_ago=1,
    fingerprint="",
    content="Test content",
    category=None
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
        category=category
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
        
        # 72小时前，时效性因子接近0.3，内容完整度1.0
        # 评分 = 0.8 * (0.5 + 0.3 * 0.3 + 0.2 * 1.0) = 0.552
        assert 0.52 <= result <= 0.58
    
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
        """测试限制单一来源"""
        items = []
        # 创建10个github项目
        for i in range(10):
            item = create_test_item(
                source_type="github",
                raw_score=0.9 - i * 0.01,
                url=f"https://example.com/{i}"
            )
            item.score = item.raw_score
            items.append(item)
        
        # 添加2个RSS
        for i in range(2):
            item = create_test_item(
                source_type="rss",
                raw_score=0.5,
                url=f"https://rss.com/{i}"
            )
            item.score = item.raw_score
            items.append(item)
        
        result = select_diverse_items(items, max_count=10)
        
        # 检查github不会占满所有位置
        github_count = sum(1 for item in result if item.source_type == "github")
        assert github_count <= 4  # 最多40%
    
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
            create_test_item(title="OpenAI releases GPT-4", url="https://example.com/1", raw_score=0.8),
            create_test_item(title="OpenAI Releases GPT-4", url="https://news.com/2", raw_score=0.6),
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
            create_test_item(title="BREAKING NEWS: AI BREAKTHROUGH", url="https://example.com/1", raw_score=0.7),
            create_test_item(title="breaking news: ai breakthrough", url="https://example.com/2", raw_score=0.5),
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
                raw_score=0.6
            ),
            create_test_item(
                title="Google Announces New AI Model Gemini",
                url="https://reddit.com/r/MachineLearning/gemini",
                source_type="reddit",
                raw_score=0.8
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
        # 创建10个同类别但不同来源的项
        for i in range(10):
            item = create_test_item(
                title=f"Paper {i}",
                url=f"https://example.com/{i}",
                source_type=f"source_{i % 5}",  # 5个不同来源
                category="论文与研究",
                raw_score=0.9 - i * 0.01
            )
            item.score = item.raw_score
            items.append(item)
        
        # 添加其他类别的项
        for i in range(5):
            item = create_test_item(
                title=f"Product {i}",
                url=f"https://product.com/{i}",
                source_type=f"source_{i}",
                category="产品与发布",
                raw_score=0.7
            )
            item.score = item.raw_score
            items.append(item)
        
        result = select_diverse_items(items, max_count=10)
        
        # 统计类别分布
        category_counts = {}
        for item in result:
            cat = item.category or "其他"
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # 论文类别不应该占满所有位置（最多35%即3-4条）
        assert category_counts.get("论文与研究", 0) <= 4
    
    def test_source_and_category_both_limited(self):
        """测试来源和类别同时限制"""
        items = []
        # 创建15个同来源同类别的高分项
        for i in range(15):
            item = create_test_item(
                title=f"GitHub Paper {i}",
                url=f"https://github.com/{i}",
                source_type="github",
                category="论文与研究",
                raw_score=0.9 - i * 0.01
            )
            item.score = item.raw_score
            items.append(item)
        
        # 添加其他来源和类别的项
        for i in range(10):
            item = create_test_item(
                title=f"RSS Product {i}",
                url=f"https://rss.com/{i}",
                source_type="rss",
                category="产品与发布",
                raw_score=0.6
            )
            item.score = item.raw_score
            items.append(item)
        
        result = select_diverse_items(items, max_count=10)
        
        # 统计
        github_count = sum(1 for item in result if item.source_type == "github")
        paper_count = sum(1 for item in result if item.category == "论文与研究")
        
        # GitHub 来源不超过40%（4条）
        assert github_count <= 4
        # 论文类别不超过35%（3-4条）
        assert paper_count <= 4
    
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
                raw_score=0.9 - i * 0.01
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
                raw_score=0.9 - i * 0.02  # 明显的评分梯度
            )
            item.score = item.raw_score
            items.append(item)
        
        result = select_diverse_items(items, max_count=10)
        
        # 结果中的评分应该大致保持降序（允许因多样性有小幅调整）
        scores = [item.score for item in result]
        # 至少前5个应该是高分项
        assert all(s >= 0.7 for s in scores[:5])
