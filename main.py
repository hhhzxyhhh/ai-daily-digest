from __future__ import annotations

import argparse
import logging
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from collectors import (
    GitHubCollector,
    NewsAPICollector,
    RedditCollector,
    RSSCollector,
    TwitterCollector,
    WebScraperCollector,
)
from config import load_settings
from delivery import send_email
from llm import LLMRouter
from models import NewsItem
from processing import (
    classify_with_llm,
    deduplicate,
    deduplicate_fuzzy,
    filter_ai_relevance_llm,
    filter_relevance_keyword,
    score,
    select_diverse_items,
)
from report import build_report

SUMMARY_PROMPT = """
你是一位专业的 AI 领域新闻编辑。请对以下新闻进行摘要：

标题：{title}
来源：{source}
原文：{content}

要求：
1. 用中文输出 2-3 句话的摘要
2. 突出技术要点和行业影响
3. 保持客观中立的语气
4. 如有关键数据/指标，务必保留
"""


OVERVIEW_PROMPT = """
你是一位专业的 AI 领域新闻编辑。以下是今天的新闻摘要列表，请写一段 80-120 字的中文总体概览：

{summaries}
"""


def run_once() -> None:
    settings = load_settings()

    router = LLMRouter(settings, "llm_providers.yaml")
    collectors = [
        RSSCollector("sources.yaml"),
        GitHubCollector("sources.yaml", settings.github_token),
        NewsAPICollector(settings.newsapi_key, "sources.yaml"),
        WebScraperCollector("sources.yaml"),
        RedditCollector("sources.yaml"),
        TwitterCollector(settings.twitter_bearer_token, "sources.yaml"),
    ]

    items: list[NewsItem] = []
    # 并行采集，提高效率
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(c.collect): c for c in collectors}
        for future in as_completed(futures):
            collector = futures[future]
            try:
                collected = future.result(timeout=60)
                items.extend(collected)
                logging.info(f"{collector.__class__.__name__} collected {len(collected)} items")
            except Exception as e:
                logging.error(f"{collector.__class__.__name__} failed: {e}")

    # 去重处理
    items = deduplicate(items)
    items = deduplicate_fuzzy(items, threshold=0.75)
    logging.info(f"Total items after dedup: {len(items)}")

    # 统计各数据源贡献
    source_stats = Counter(item.source_type for item in items)
    logging.info(f"Source distribution: {dict(source_stats)}")

    # ========== 三层过滤机制 ==========
    # 第一层：关键词预过滤（黑名单+白名单）
    whitelist_items, greyzone_items, blacklist_items = filter_relevance_keyword(items)
    logging.info(
        f"Filter Layer 1 - Keyword: whitelist={len(whitelist_items)}, greyzone={len(greyzone_items)}, blacklist={len(blacklist_items)}"
    )

    # 第二层：LLM精准判断（仅对灰色地带）
    llm_approved_items = filter_ai_relevance_llm(greyzone_items, router)
    logging.info(
        f"Filter Layer 2 - LLM relevance: {len(llm_approved_items)} approved out of {len(greyzone_items)} greyzone items"
    )

    # 合并通过的新闻
    items = whitelist_items + llm_approved_items
    logging.info(f"Total items after relevance filtering: {len(items)}")

    # 第三层：LLM智能分类
    classify_with_llm(items, router)
    logging.info("Filter Layer 3 - LLM classification completed")

    # 评分
    for item in items:
        item.score = score(item)

    items.sort(key=lambda x: x.score, reverse=True)
    # 使用多样性选择器,确保来源均衡
    items = select_diverse_items(items, max_count=10)

    # 统计最终选择的来源分布
    final_stats = Counter(item.source_type for item in items)
    logging.info(f"Final selection source distribution: {dict(final_stats)}")

    for item in items:
        try:
            item.summary = router.complete(
                SUMMARY_PROMPT.format(title=item.title, source=item.source, content=item.content)
            )
        except Exception as e:
            logging.warning(f"Failed to generate summary for '{item.title}': {e}")
            item.summary = "摘要生成失败"

    summaries = "\n".join([f"- {i.title}: {i.summary}" for i in items[:10]])
    overview = router.complete(OVERVIEW_PROMPT.format(summaries=summaries))
    report_text, report_html = build_report(items, overview)

    recipients = [e.strip() for e in settings.email_recipients.split(",") if e.strip()]
    subject = f"AI 日报 - {datetime.now().strftime('%Y-%m-%d')}"
    try:
        send_email(
            smtp_host=settings.email_smtp_host,
            smtp_port=settings.email_smtp_port,
            sender=settings.email_sender,
            password=settings.email_password,
            recipients=recipients,
            subject=subject,
            text_body=report_text,
            html_body=report_html,
        )
        logging.info(f"Email sent successfully to {len(recipients)} recipient(s)")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        raise

    archive_dir = "archive"
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{datetime.now().strftime('%Y-%m-%d')}.md")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(report_text)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="AI Daily Digest Agent")
    parser.add_argument("--run-once", action="store_true", help="立即执行一次")
    args = parser.parse_args()

    if args.run_once:
        run_once()
        return

    settings = load_settings()
    scheduler = BlockingScheduler(timezone=settings.timezone)
    scheduler.add_job(
        run_once,
        "cron",
        hour=settings.schedule_hour,
        minute=settings.schedule_minute,
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
