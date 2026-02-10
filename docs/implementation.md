# AI Daily Digest 实现说明

> 本文档详细说明新闻收集、筛选、评分的内部实现逻辑。

## 📊 整体流程

```
数据源收集 → 去重 → 分类 → 评分 → 排序 → 多样性筛选 → LLM摘要 → 邮件发送
```

---

## 🔍 收集阶段

### 1. 数据源列表 (main.py)

6种数据源并行收集：

| 数据源 | 采集内容 | 是否需要API Key |
|--------|---------|---------------|
| **RSSCollector** | RSS订阅源（arXiv、MIT Tech Review等） | ❌ 否 |
| **GitHubCollector** | GitHub热门项目、新仓库、发布动态 | ⚠️ 推荐（GitHub Token） |
| **NewsAPICollector** | 英文科技新闻（NewsAPI） | ⚠️ 可选（100次/天免费） |
| **WebScraperCollector** | 网页抓取（机器之心、量子位） | ❌ 否 |
| **RedditCollector** | Reddit热门帖子 | ❌ 目前只读 |
| **TwitterCollector** | Twitter推文 | ⚠️ 可选 |

### 2. 采集数量限制

- **RSS**: 每个 RSS 源最多50条
- **GitHub**: 趋势项目+搜索结果+发布动态
- **NewsAPI**: 20条
- **WebScraper**: 每个网站最多20条
- **Reddit**: 每个子版块20条
- **Twitter**: 最多20条

**理论上最多收集**: 50×5 + 30×3 + 20×2 + 20 = 400+ 条

---

## 🔄 筛选流程

### 阶段1: 去重 (processing.py)

**指纹算法**:
```python
fingerprint = SHA256(title + "::" + url)
```

- 相同标题+URL的内容会被合并
- 每个数据源独立去重

---

### 阶段2: 分类 (processing.py)

**关键词匹配规则**:

| 分类 | 关键词 | 触发条件 |
|------|--------|---------|
| **论文与研究** | `paper`, `arxiv`, `论文`, `research` | 学术论文 |
| **产品与发布** | `release`, `发布`, `v1`, `v2`, `model` | 产品发布/版本更新 |
| **行业动态** | `funding`, `融资`, `acquisition`, `并购`, `policy` | 融资、并购、政策 |
| **教程与观点** | `tutorial`, `guide`, `教程`, `观点` | 教程、文章 |
| **开源项目** | `github`, `repo`, `open-source`, `开源` | 开源项目 |
| **其他** | 未匹配 | 其他类型 |

---

### 阶段3: 评分 (processing.py)

**综合评分公式**:

```python
score = raw_score * (0.6 + 0.4 * recency_factor)
```

#### A. 原始评分 (raw_score)

来自数据源（collectors.py中设置）:

| 数据源 | raw_score | 原因 |
|--------|----------|------|
| RSS | 0.2 | 标准RSS内容 |
| GitHub Trending | 0.6 | GitHub热门项目 |
| GitHub Search | 0.7 | GitHub搜索结果 |
| GitHub Releases | 0.8 | 仓库发布 |
| NewsAPI | 0.5 | 第三方新闻API |
| WebScraper | 0.4 | 网页抓取 |
| Reddit | 0.5 | Reddit帖子 |
| Twitter | 0.4 | 推文 |

#### B. 时效性因子 (recency_factor)

```python
recency_factor = max(0.3, 1.0 - (age_hours / 72))
```

- **1小时前**: age_hours = 1 → factor ≈ 0.99
- **12小时前**: age_hours = 12 → factor ≈ 0.83
- **24小时前**: age_hours = 24 → factor ≈ 0.67
- **48小时前**: age_hours = 48 → factor ≈ 0.33
- **72小时前**: age_hours = 72 → factor = 0.3（下限）

#### C. 最终公式示例

**案例1**: GitHub发布（raw=0.8，刚发布1小时）
```
score = 0.8 × (0.6 + 0.4 × 0.99) ≈ 0.8
```

**案例2**: RSS（raw=0.2，刚发布1小时）
```
score = 0.2 × (0.6 + 0.4 × 0.99) ≈ 0.2
```

**案例3**: Reddit（raw=0.5，发布48小时）
```
score = 0.5 × (0.6 + 0.4 × 0.33) ≈ 0.37
```

**注**: 当前版本已移除来源权重（source_weight），所有来源按统一公式评分。

---

### 阶段4: 排序和多样性筛选 (processing.py)

```python
items.sort(key=lambda x: x.score, reverse=True)
items = select_diverse_items(items, max_count=10)
```

**多样性选择策略** (select_diverse_items):
- 确保不同数据源的内容均衡分布
- 每个来源类型最多占 40% 配额（至少2条）
- 避免单一来源占据所有位置
- 在保证质量的前提下增加内容多样性

**最终输出**: 默认10条新闻（可通过 max_count 参数调整）

---

### 阶段5: LLM摘要 (main.py)

**每个新闻生成中文摘要**（2-3句话）：
- 使用 LLM 路由器（支持主备切换）
- 自动总结技术要点
- 保留关键数据

---

## 📈 筛选逻辑总结

### 优先级排序因素

1. **内容类型** (raw_score)
   - 发布动态（0.8）
   - 搜索结果（0.7）
   - 趋势项目（0.6）
   - 其他（0.2-0.5）

2. **时效性** (recency_factor)
   - 72小时内平滑衰减
   - 影响最终评分的40%

3. **多样性**
   - 单一来源最多占40%
   - 确保内容来源均衡

### 筛选阈值

- **默认保留**: 10条
- **可调整范围**: 1-50条（通过 max_count 参数）

---

## ⚠️ 已知限制

### 1. Reddit/NewsAPI未配置时静默失败
- 如果不配置这些数据源的API，会被跳过
- 用户可能以为系统在运行，实际上某些数据源没数据

### 2. 分类算法基于关键词
- 仅靠关键词匹配，可能不够精确
- 例如："AI model release" → 产品与发布 ✅
- 但 "Model validation framework" → 可能被误分类

### 3. 去重依赖URL+标题
- 同一URL的不同标题可能被重复收集
- 两个不同数据源的同一条新闻理论上可能重复

### 4. GitHub Token不配置时功能减弱
- 无法搜索新仓库
- 无法监控仓库发布
- 只能获取GitHub Trending

---

## 💡 优化建议

### 可能的改进方向

1. **增强分类准确性**
   - 考虑使用 LLM 进行更准确的分类
   - 而不仅仅是关键词匹配

2. **改进去重算法**
   - 使用内容相似度检测
   - 而不只是 URL+标题

3. **配置验证与通知**
   - 数据源失败时发送告警
   - 让用户知道哪些功能未启用

4. **评分权重可调**
   - 允许用户自定义时效性权重
   - 允许用户自定义来源权重

---

## 📝 维护说明

- 本文档应与代码实现保持同步
- 修改评分、筛选逻辑时，需同步更新本文档
- 相关代码文件：`processing.py`, `main.py`, `collectors.py`
