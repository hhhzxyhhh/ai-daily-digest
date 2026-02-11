from __future__ import annotations

import hashlib
import logging
import math
import re
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from models import NewsItem

logger = logging.getLogger(__name__)


class BaseCollector:
    source_type: str = "base"

    def collect(self) -> list[NewsItem]:
        raise NotImplementedError

    @staticmethod
    def _fingerprint(item: NewsItem) -> str:
        """生成新闻项的唯一指纹"""
        base = f"{item.title}::{item.url}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()


class RSSCollector(BaseCollector):
    source_type = "rss"

    def __init__(self, sources_path: str) -> None:
        self.sources_path = sources_path

    def collect(self) -> list[NewsItem]:
        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                sources = yaml.safe_load(f).get("rss", [])
        except Exception as e:
            logger.error(f"Failed to load RSS sources: {e}")
            return []

        # RSS 来源权威度映射
        source_authority = {
            "arXiv cs.AI": 0.7,
            "arXiv cs.LG": 0.7,
            "MIT Tech Review AI": 0.65,
            "VentureBeat AI": 0.6,
            "Hacker News": 0.55,
            "机器之心": 0.65,  # 国内AI领域权威媒体
        }

        # AI关键词列表（用于Hacker News过滤）
        ai_keywords = [
            "ai", "artificial intelligence", "machine learning", "deep learning",
            "llm", "gpt", "neural network", "transformer", "diffusion", "agent",
            "openai", "anthropic", "chatgpt", "claude", "gemini",
            "pytorch", "tensorflow", "hugging face", "langchain",
            "computer vision", "nlp", "natural language", "reinforcement learning",
        ]
        
        items: list[NewsItem] = []
        for src in sources:
            try:
                feed = feedparser.parse(src["url"])
                for entry in feed.entries[:50]:
                    try:
                        published_at = self._parse_datetime(
                            entry.get("published") or entry.get("updated")
                        )
                        content = entry.get("summary", "") or entry.get("description", "")
                        title = entry.get("title", "").strip()
                        
                        # 对Hacker News进行关键词过滤
                        if src["name"] == "Hacker News":
                            combined_text = f"{title} {content}".lower()
                            if not any(keyword in combined_text for keyword in ai_keywords):
                                continue  # 跳过不包含AI关键词的新闻
                        
                        # 根据来源权威度设置 raw_score
                        raw_score = source_authority.get(src["name"], 0.5)
                        
                        item = NewsItem(
                            title=title,
                            url=entry.get("link", "").strip(),
                            source=src["name"],
                            source_type=self.source_type,
                            content=self._clean_text(content),
                            published_at=published_at,
                            author=entry.get("author"),
                            tags=[t["term"] for t in entry.get("tags", []) if "term" in t],
                            raw_score=raw_score,
                        )
                        item.fingerprint = self._fingerprint(item)
                        items.append(item)
                    except Exception as e:
                        logger.warning(f"Failed to parse RSS entry from {src['name']}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {src['name']}: {e}")
                continue
        return items

    def _parse_datetime(self, raw: str | None) -> datetime:
        if not raw:
            return datetime.now(timezone.utc)
        try:
            return date_parser.parse(raw)
        except Exception:
            return datetime.now(timezone.utc)

    def _clean_text(self, text: str) -> str:
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()


class GitHubCollector(BaseCollector):
    source_type = "github"

    def __init__(self, sources_path: str, github_token: str | None) -> None:
        self.sources_path = sources_path
        self.github_token = github_token

    def collect(self) -> list[NewsItem]:
        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f).get("github", {})
        except Exception as e:
            logger.error(f"Failed to load GitHub config: {e}")
            return []

        items: list[NewsItem] = []
        items.extend(self._collect_trending(cfg))
        if self.github_token:
            items.extend(self._collect_search(cfg))
            items.extend(self._collect_watchlist(cfg))
        return items

    def _collect_trending(self, cfg: dict) -> list[NewsItem]:
        try:
            since = cfg.get("trending", {}).get("since", "daily")
            url = f"https://github.com/trending?since={since}"
            resp = httpx.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            keywords = [k.lower() for k in cfg.get("keywords", [])]

            items: list[NewsItem] = []
            for article in soup.select("article.Box-row"):
                repo = article.select_one("h2 a")
                if not repo:
                    continue
                repo_name = repo.get_text(strip=True).replace(" ", "")
                desc = article.select_one("p")
                desc_text = desc.get_text(strip=True) if desc else ""
                combined = f"{repo_name} {desc_text}".lower()
                if keywords and not any(k in combined for k in keywords):
                    continue

                # 尝试解析 stars today 数据（页面结构可能变化）
                raw_score = 0.6  # trending 默认较高基础分
                try:
                    stars_today_elem = article.select_one("span.d-inline-block.float-sm-right")
                    if stars_today_elem:
                        stars_text = stars_today_elem.get_text(strip=True)
                        # 提取数字，如 "123 stars today"
                        import re
                        match = re.search(r'(\d+)', stars_text)
                        if match:
                            stars_today = int(match.group(1))
                            raw_score = min(0.9, 0.5 + 0.1 * math.log1p(stars_today / 10))
                except Exception:
                    pass

                url = f"https://github.com/{repo_name}"
                item = NewsItem(
                    title=f"GitHub Trending: {repo_name}",
                    url=url,
                    source="GitHub Trending",
                    source_type=self.source_type,
                    content=desc_text,
                    published_at=datetime.now(timezone.utc),
                    raw_score=raw_score,
                )
                item.fingerprint = self._fingerprint(item)
                items.append(item)
            return items
        except Exception as e:
            logger.error(f"Failed to collect GitHub trending: {e}")
            return []

    def _collect_search(self, cfg: dict) -> list[NewsItem]:
        created_days = int(cfg.get("search", {}).get("created_days", 14))
        stars_min = int(cfg.get("search", {}).get("stars_min", 1000))
        created_after = (datetime.now(timezone.utc) - timedelta(days=created_days)).date()
        query = f"topic:ai created:>{created_after} stars:>={stars_min}"

        url = "https://api.github.com/search/repositories"
        headers = {"Authorization": f"Bearer {self.github_token}"}
        resp = httpx.get(url, params={"q": query, "sort": "stars"}, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        items: list[NewsItem] = []
        for repo in data.get("items", [])[:30]:
            # 利用 stars 数动态计算 raw_score
            stars = repo.get("stargazers_count", 0)
            raw_score = min(0.9, 0.3 + 0.2 * math.log1p(stars / 100))
            
            item = NewsItem(
                title=f"New AI Repo: {repo['full_name']}",
                url=repo["html_url"],
                source="GitHub Search",
                source_type=self.source_type,
                content=(repo.get("description") or ""),
                published_at=date_parser.parse(repo.get("created_at")),
                raw_score=raw_score,
            )
            item.fingerprint = self._fingerprint(item)
            items.append(item)
        return items

    def _collect_watchlist(self, cfg: dict) -> list[NewsItem]:
        watch_repos = cfg.get("watch_repos", [])
        if not watch_repos:
            return []
        headers = {"Authorization": f"Bearer {self.github_token}"}

        items: list[NewsItem] = []
        for repo in watch_repos:
            url = f"https://api.github.com/repos/{repo}/releases"
            resp = httpx.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                continue
            releases = resp.json()[:3]
            for rel in releases:
                item = NewsItem(
                    title=f"{repo} 发布新版本 {rel.get('tag_name')}",
                    url=rel.get("html_url", f"https://github.com/{repo}"),
                    source="GitHub Releases",
                    source_type=self.source_type,
                    content=rel.get("name") or rel.get("body", ""),
                    published_at=date_parser.parse(rel.get("published_at")),
                    raw_score=0.6,
                )
                item.fingerprint = self._fingerprint(item)
                items.append(item)
        return items


class NewsAPICollector(BaseCollector):
    source_type = "newsapi"

    def __init__(self, newsapi_key: str | None, sources_path: str) -> None:
        self.newsapi_key = newsapi_key
        self.sources_path = sources_path

    def collect(self) -> list[NewsItem]:
        if not self.newsapi_key:
            return []
        with open(self.sources_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f).get("newsapi", {})
        query = cfg.get("query", "AI OR LLM OR machine learning OR deep learning")
        page_size = int(cfg.get("page_size", 20))
        language = cfg.get("language", "en")

        url = "https://newsapi.org/v2/everything"
        params = {"q": query, "pageSize": page_size, "language": language, "sortBy": "publishedAt"}
        headers = {"X-Api-Key": self.newsapi_key}
        resp = httpx.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        items: list[NewsItem] = []
        for article in data.get("articles", []):
            item = NewsItem(
                title=article.get("title") or "",
                url=article.get("url") or "",
                source=article.get("source", {}).get("name", "NewsAPI"),
                source_type=self.source_type,
                content=article.get("description") or article.get("content") or "",
                published_at=date_parser.parse(article.get("publishedAt") or datetime.now(timezone.utc).isoformat()),
                author=article.get("author"),
                raw_score=0.5,
            )
            item.fingerprint = self._fingerprint(item)
            items.append(item)
        return items


class WebScraperCollector(BaseCollector):
    source_type = "scraper"

    def __init__(self, sources_path: str) -> None:
        self.sources_path = sources_path
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def collect(self) -> list[NewsItem]:
        with open(self.sources_path, "r", encoding="utf-8") as f:
            sites = yaml.safe_load(f).get("websites", [])

        items: list[NewsItem] = []
        for site in sites:
            items.extend(self._collect_from_html(site))
        
        return items
    
    def _extract_publish_time(self, url: str, soup: BeautifulSoup | None) -> datetime:
        """提取文章发布时间"""
        # 方法1：从详情页的 <time> 标签提取
        if soup:
            time_tag = soup.find("time")
            if time_tag:
                # 尝试从 datetime 属性提取
                dt_str = time_tag.get("datetime")
                if dt_str:
                    try:
                        return date_parser.parse(dt_str)
                    except Exception:
                        pass
        
        # 方法2：从 URL 中提取日期（如 /2026/02/378423.html）
        date_pattern = r'/(\d{4})/(\d{2})/(\d{2})'
        match = re.search(date_pattern, url)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
            except Exception:
                pass
        
        # 回退：使用当前时间
        return datetime.now(timezone.utc)
    
    def _collect_from_html(self, site: dict) -> list[NewsItem]:
        """从 HTML 页面爬取文章列表"""
        url = site.get("url")
        selector = site.get("selector")
        site_name = site.get("name", "Unknown")
        
        if not url or not selector:
            logger.warning(f"Site {site_name} missing url or selector")
            return []
        
        items: list[NewsItem] = []
        try:
            resp = httpx.get(url, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch {site_name} ({url}): status {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select(selector)
            
            if not links:
                logger.warning(f"No links found for {site_name} with selector '{selector}'")
                return []
            
            logger.info(f"Found {len(links)} links for {site_name}")
            
            for link in links[:20]:
                href = link.get("href") or ""
                title = link.get_text(strip=True)
                if href.startswith("/"):
                    href = site.get("base_url", url).rstrip("/") + href
                if not href or not title:
                    continue
                
                # 尝试二次抓取正文内容
                content = ""
                try:
                    detail_resp = httpx.get(href, headers=self.headers, timeout=10)
                    if detail_resp.status_code == 200:
                        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                        
                        # 提取段落并过滤样板文本
                        paragraphs = detail_soup.select("p")
                        filtered_paragraphs = []
                        
                        # 样板关键词（用于过滤）
                        boilerplate_keywords = ["扫码", "关注", "二维码", "订阅", "点击", "转发", "分享"]
                        
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            # 过滤：长度太短（<20字符）或包含样板关键词
                            if len(text) < 20:
                                continue
                            if any(keyword in text for keyword in boilerplate_keywords):
                                continue
                            filtered_paragraphs.append(text)
                            # 最多取5段
                            if len(filtered_paragraphs) >= 5:
                                break
                        
                        content = " ".join(filtered_paragraphs)
                        # 限制长度
                        if len(content) > 500:
                            content = content[:500] + "..."
                except Exception as e:
                    logger.debug(f"Failed to fetch content from {href}: {e}")
                    content = ""
                
                # 提取发布时间
                published_at = self._extract_publish_time(href, detail_soup if 'detail_soup' in locals() else None)
                
                item = NewsItem(
                    title=title,
                    url=href,
                    source=site.get("name", "Web"),
                    source_type=self.source_type,
                    content=content,
                    published_at=published_at,
                    raw_score=0.65,
                )
                item.fingerprint = self._fingerprint(item)
                items.append(item)
        except Exception as e:
            logger.error(f"Failed to collect from {site_name}: {e}")
        
        return items


class RedditCollector(BaseCollector):
    source_type = "reddit"

    def __init__(self, sources_path: str) -> None:
        self.sources_path = sources_path

    def collect(self) -> list[NewsItem]:
        with open(self.sources_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f).get("reddit", {})
        subs = cfg.get("subreddits", ["MachineLearning", "artificial", "LocalLLaMA"])
        limit = int(cfg.get("limit", 20))

        items: list[NewsItem] = []
        for sub in subs:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
            resp = httpx.get(url, headers={"User-Agent": "ai-digest-bot/1.0"}, timeout=20)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                
                # 利用社交信号动态计算 raw_score
                upvotes = post.get("score", 0)
                comments = post.get("num_comments", 0)
                # 对数归一化到 0.3-0.9 范围
                raw_score = min(0.9, 0.3 + 0.15 * math.log1p(upvotes / 50) + 0.1 * math.log1p(comments / 10))
                
                item = NewsItem(
                    title=post.get("title") or "",
                    url=f"https://www.reddit.com{post.get('permalink', '')}",
                    source=f"r/{sub}",
                    source_type=self.source_type,
                    content=post.get("selftext") or "",
                    published_at=datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc),
                    author=post.get("author"),
                    raw_score=raw_score,
                )
                item.fingerprint = self._fingerprint(item)
                items.append(item)
        return items


class TwitterCollector(BaseCollector):
    source_type = "twitter"

    def __init__(self, bearer_token: str | None, sources_path: str) -> None:
        self.bearer_token = bearer_token
        self.sources_path = sources_path

    def collect(self) -> list[NewsItem]:
        if not self.bearer_token:
            return []
        with open(self.sources_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f).get("twitter", {})
        query = cfg.get("query", "AI OR LLM OR machine learning lang:en")
        max_results = int(cfg.get("max_results", 20))

        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,author_id",
        }
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        resp = httpx.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return []
        data = resp.json()

        items: list[NewsItem] = []
        for tweet in data.get("data", []):
            item = NewsItem(
                title=tweet.get("text", "")[:80],
                url=f"https://x.com/i/web/status/{tweet.get('id')}",
                source="Twitter/X",
                source_type=self.source_type,
                content=tweet.get("text", ""),
                published_at=date_parser.parse(tweet.get("created_at")),
                raw_score=0.4,
            )
            item.fingerprint = self._fingerprint(item)
            items.append(item)
        return items
