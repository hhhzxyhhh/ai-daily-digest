import os
from datetime import datetime
from jinja2 import Template
from models import NewsItem
from report import (
    REPORT_HTML_TEMPLATE,
    CATEGORY_ICONS,
    SOURCE_COLORS,
    SOURCE_COLORS_LIGHT,
    TOP5_COLOR_THEMES,
)
from collections import defaultdict

# 1. 创建模拟数据
mock_items = [
    NewsItem(
        title="GPT-5 预览版发布：推理能力大幅提升，支持实时语音交互",
        url="https://openai.com/blog/gpt-5-preview",
        source="OpenAI Blog",
        source_type="rss",
        content="OpenAI 刚刚发布了 GPT-5 的预览版本。新模型在数学推理和代码生成方面表现出色，测试集准确率提升了 30%。同时引入了原生多模态支持。",
        summary="OpenAI 发布 GPT-5 预览版，模型在数学推理和代码生成任务上准确率提升 30%，并引入原生多模态支持，实现实时语音交互功能。",
        published_at=datetime.now(),
        category="产品发布",
        tags=["GPT-5", "LLM", "Multimodal"],
        raw_score=0.95,
        score=0.98,
    ),
    NewsItem(
        title="DeepSeek-Coder-V2 开源：超越 GPT-4 Turbo 的代码能力",
        url="https://github.com/deepseek-ai/DeepSeek-Coder-V2",
        source="GitHub Trending",
        source_type="github",
        content="DeepSeek 开源了第二代代码大模型，在 HumanEval 和 MBPP 榜单上刷新了开源模型的记录，甚至在部分指标上超越了闭源的 GPT-4 Turbo。",
        summary="DeepSeek 开源第二代代码模型 DeepSeek-Coder-V2，在 HumanEval 和 MBPP 榜单刷新纪录，部分指标超越 GPT-4 Turbo，成为最强开源代码模型。",
        published_at=datetime.now(),
        category="开源项目",
        tags=["Open Source", "Coding", "SOTA"],
        raw_score=0.92,
        score=0.95,
    ),
    NewsItem(
        title="谷歌 DeepMind 新论文：利用强化学习解决千禧年数学难题",
        url="https://arxiv.org/abs/2402.12345",
        source="arXiv cs.AI",
        source_type="rss",
        content="DeepMind 团队发表最新论文，通过 AlphaGeometry 系统证明了复杂的几何定理，展示了 AI 在纯数学领域的推理潜力。",
        summary="DeepMind 发表论文介绍 AlphaGeometry 系统，利用强化学习成功证明复杂几何定理，展示了 AI 在解决纯数学难题方面的突破性进展。",
        published_at=datetime.now(),
        category="论文研究",
        tags=["Reinforcement Learning", "Math", "DeepMind"],
        raw_score=0.88,
        score=0.90,
    ),
    NewsItem(
        title="英伟达 H200 芯片全面出货，AI 算力竞赛进入新阶段",
        url="https://www.venturebeat.com/ai/nvidia-h200-shipping",
        source="VentureBeat",
        source_type="newsapi",
        content="英伟达宣布 H200 GPU 开始向各大云厂商供货。新芯片配备 141GB HBM3e 显存，推理速度比 H100 快 2 倍。",
        summary="英伟达 H200 GPU 开始全面供货，配备 141GB HBM3e 显存，推理速度较 H100 提升 2 倍，标志着 AI 算力竞赛进入新阶段。",
        published_at=datetime.now(),
        category="行业动态",
        tags=["Hardware", "NVIDIA", "GPU"],
        raw_score=0.85,
        score=0.88,
    ),
    NewsItem(
        title="LangChain v0.2 发布：更稳定的架构与流式支持",
        url="https://twitter.com/LangChainAI/status/123456789",
        source="Twitter/X",
        source_type="twitter",
        content="LangChain 正式发布 0.2 版本，重构了核心组件，分离了 langgraph，提供了更好的流式输出支持和事件回调机制。",
        summary="LangChain 发布 0.2 版本，重构核心组件并分离 langgraph，显著增强流式输出支持与事件回调机制，提升框架稳定性。",
        published_at=datetime.now(),
        category="开源项目",
        tags=["LangChain", "Framework", "Python"],
        raw_score=0.82,
        score=0.85,
    ),
    # --- Top 5 之后的新闻 ---
    NewsItem(
        title="Meta 推出 Llama 4 早期预览，参数规模达 1T",
        url="https://ai.meta.com/blog/llama-4-preview",
        source="Meta AI",
        source_type="rss",
        content="Meta 悄然放出了 Llama 4 的预览信息...",
        summary="Meta 发布 Llama 4 早期预览信息，模型参数规模达 1T，预计将进一步推动开源大模型的发展。",
        published_at=datetime.now(),
        category="产品发布",
        tags=["Llama", "Meta", "Open Source"],
        raw_score=0.75,
        score=0.80,
    ),
     NewsItem(
        title="如何构建高效的 RAG 系统：从入门到进阶",
        url="https://medium.com/ai-tutorial",
        source="Medium",
        source_type="scraper",
        content="这是一篇详细的教程...",
        summary="详细教程解析如何构建高效 RAG 系统，涵盖从基础概念到进阶优化的全过程，适合 AI 开发者参考。",
        published_at=datetime.now(),
        category="教程观点",
        tags=["RAG", "Tutorial", "Engineering"],
        raw_score=0.70,
        score=0.75,
    ),
]

# 2. 准备渲染上下文
top_items = mock_items[:5]
rest_items = mock_items[5:]
grouped = defaultdict(list)
for item in rest_items:
    grouped[item.category or "其他"].append(item)

from datetime import date

# 计算 Top 5 配色主题（与 report.py 中的逻辑一致）
theme_index = date.today().toordinal() % 7
today_theme = TOP5_COLOR_THEMES[theme_index]

context = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "overview": "今日 AI 领域迎来多项重大突破：OpenAI 发布 GPT-5 预览版，推理能力大幅提升；DeepSeek 开源最强代码模型；DeepMind 在数学推理领域取得新进展。硬件方面，英伟达 H200 开始出货。开源社区 LangChain 迎来重要版本更新。",
    "top_items": top_items,
    "grouped": grouped,
    "total": 156,  # 模拟原始采集总数
    "selected": len(mock_items),
    "category_icons": CATEGORY_ICONS,
    "source_colors": SOURCE_COLORS,
    "source_colors_light": SOURCE_COLORS_LIGHT,
    "top5_bg_color": today_theme["bg"],
    "top5_title_color": today_theme["title"],
    "top5_number_color": today_theme["number"],
}

# 3. 渲染并保存
templates = {
    "preview_fresh.html": REPORT_HTML_TEMPLATE,
}

print("正在生成预览文件...")
for filename, template in templates.items():
    html_content = template.render(**context)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"- 已生成: {os.path.abspath(filename)}")

print("\n生成完毕！请在文件管理器中双击上述 HTML 文件查看效果。")
