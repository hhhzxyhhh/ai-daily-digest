from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from jinja2 import Template

from models import NewsItem

# 1. Add Mappings
CATEGORY_ICONS = {
    "Research": "🔬",
    "Application": "🚀",
    "Industry": "🏢",
    "Policy": "⚖️",
    "Other": "📰",
}

SOURCE_COLORS = {
    "HackerNews": "#d94600",
    "Twitter": "#0c85d0",
    "Arxiv": "#991b1b",
    "HuggingFace": "#d97706",
    "Other": "#4b5563",
}

SOURCE_COLORS_LIGHT = {
    "HackerNews": "#fff7ed",
    "Twitter": "#f0f9ff",
    "Arxiv": "#fef2f2",
    "HuggingFace": "#fffbeb",
    "Other": "#f3f4f6",
    "rss": "#fff7ed",
    "github": "#f9fafb",
    "newsapi": "#f0fdf4",
    "scraper": "#fefce8",
}

# Top 5 配色主题库（7组联动配色：背景/标题/序号）
TOP5_COLOR_THEMES = [
    {"bg": "#f0f9ff", "title": "#1e3a8a", "number": "#bfdbfe"},  # 浅蓝系 (Sky)
    {"bg": "#fefce8", "title": "#92400e", "number": "#fde68a"},  # 浅黄系 (Lemon)
    {"bg": "#f0fdf4", "title": "#065f46", "number": "#a7f3d0"},  # 浅绿系 (Mint)
    {"bg": "#faf5ff", "title": "#6b21a8", "number": "#e9d5ff"},  # 浅紫系 (Lavender)
    {"bg": "#fff7ed", "title": "#9a3412", "number": "#fed7aa"},  # 浅橙系 (Peach)
    {"bg": "#fdf4ff", "title": "#9f1239", "number": "#fbcfe8"},  # 浅粉系 (Rose)
    {"bg": "#f1f5f9", "title": "#1e293b", "number": "#cbd5e1"},  # 浅灰系 (Slate)
]

# 2. Update Text Template
REPORT_TEXT_TEMPLATE = Template(
    """
AI 日报 - {{ date }}

今日概览:
{{ overview }}

TOP 5 重要新闻:
{% for item in top_items %}
- {{ category_icons.get(item.category, '📰') }} [{{ item.category }}] {{ item.title }}
  来源: {{ item.source }} | 时间: {{ item.publish_time }}
  {{ item.summary }}
  {{ item.url }}
{% endfor %}

分类新闻:
{% for category, items in grouped.items() %}
{{ category_icons.get(category, '📰') }} {{ category }}:
{% for item in items %}
- {{ item.title }}
  来源: {{ item.source }} | 时间: {{ item.publish_time }}
  {{ item.summary }}
  {{ item.url }}
{% endfor %}
{% endfor %}

统计:
- 今日采集 {{ total }} 条
- 筛选输出 {{ selected }} 条
"""
)

# 3. HTML Email Template - Fresh Card Style
HTML_TEMPLATE_FRESH = Template(
    """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1f2937;">
    <div style="max-width: 640px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header & Overview Block -->
        <div style="background-color: #f8fafc; padding: 24px 20px 24px; margin-bottom: 20px; border-bottom: 1px solid #eef2f6;">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #111827; letter-spacing: -0.025em;">AI Daily Digest</h1>
                <div style="font-size: 14px; color: #64748b; font-weight: 500;">{{ date }}</div>
            </div>

            <!-- Overview -->
            <div style="color: #475569; font-size: 15px; line-height: 1.6;">
                {{ overview }}
            </div>
        </div>

        <!-- Top 5 Section -->
        <div style="background-color: {{ top5_bg_color }}; padding: 24px 20px; margin-top: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                 <span style="font-size: 18px; margin-right: 8px;">🤍</span>
                 <h2 style="margin: 0; font-size: 18px; font-weight: 700; color: {{ top5_title_color }};">Today's Highlights</h2>
            </div>

            {% for item in top_items %}
            <div style="background-color: #ffffff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); border: 1px solid #eef2f6; position: relative; overflow: hidden;">
                <!-- Decorative Number -->
                <div style="position: absolute; top: -10px; right: -5px; font-size: 80px; font-weight: 900; color: {{ top5_number_color }}; z-index: 0; pointer-events: none; opacity: 0.5;">{{ loop.index }}</div>

                <div style="position: relative; z-index: 1;">
                    <div style="margin-bottom: 8px;">
                         <span style="background-color: {{ source_colors_light.get(item.source_type, source_colors_light['Other']) }}; color: {{ source_colors.get(item.source, source_colors['Other']) }}; padding: 4px 10px; border-radius: 100px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">{{ item.source }}</span>
                    </div>
                    <h3 style="margin: 0 0 10px; font-size: 18px; font-weight: 700; line-height: 1.4;">
                        <a href="{{ item.url }}" style="color: #111827; text-decoration: none;">{{ item.title }}</a>
                    </h3>
                    <p style="margin: 0 0 16px; font-size: 15px; color: #4b5563; line-height: 1.6;">{{ item.summary }}</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px; color: #9ca3af;">
                        <span>{{ item.publish_time }}</span>
                        {% if item.tags %}
                            <span>•</span>
                            {% for tag in item.tags %}
                            <span style="font-family: monospace; color: #6b7280;">#{{ tag }}</span>
                            {% endfor %}
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Category Items -->
        <div style="padding: 24px 20px;">
            {% for category, items in grouped.items() %}
            <div style="margin-bottom: 32px;">
                <h2 style="margin: 0 0 16px; font-size: 18px; font-weight: 700; color: #1f2937; padding-bottom: 8px; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center;">
                    <span style="margin-right: 8px;">{{ category_icons.get(category, '📰') }}</span>
                    {{ category }}
                </h2>
                {% for item in items %}
                <div style="background-color: #fafafa; border: 1px solid #f3f4f6; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <h3 style="margin: 0 0 8px; font-size: 16px; font-weight: 600; line-height: 1.4;">
                        <a href="{{ item.url }}" style="color: #1f2937; text-decoration: none;">{{ item.title }}</a>
                    </h3>
                    <p style="margin: 0 0 12px; font-size: 14px; color: #4b5563; line-height: 1.5;">{{ item.summary }}</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px;">
                        <span style="background-color: {{ source_colors_light.get(item.source_type, source_colors_light['Other']) }}; color: {{ source_colors.get(item.source, source_colors['Other']) }}; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{{ item.source }}</span>
                        <span style="color: #d1d5db;">•</span>
                        <span style="color: #6b7280;">{{ item.publish_time }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>

        <!-- Footer -->
        <div style="text-align: center; padding: 20px; border-top: 1px solid #e5e7eb; margin-top: 20px;">
            <p style="margin: 0; color: #9ca3af; font-size: 12px;">Generated by AI Daily Digest • {{ selected }} items selected from {{ total }} collected</p>
        </div>
    </div>
</body>
</html>
    """
)

# Set Default Template
REPORT_HTML_TEMPLATE = HTML_TEMPLATE_FRESH


def build_report(items: list[NewsItem], overview: str, total_collected: int) -> tuple[str, str]:
    report_date = datetime.now().strftime("%Y-%m-%d")
    top_items = items[:5]
    rest_items = items[5:]
    grouped: dict[str, list[NewsItem]] = defaultdict(list)
    for item in rest_items:
        grouped[item.category or "Other"].append(item)

    # 计算 Top 5 配色主题（每天轮换）
    theme_index = date.today().toordinal() % 7
    today_theme = TOP5_COLOR_THEMES[theme_index]

    # 4. Pass category_icons and source_colors to context
    context = {
        "date": report_date,
        "overview": overview,
        "top_items": top_items,
        "grouped": grouped,
        "total": total_collected,
        "selected": len(items),
        "category_icons": CATEGORY_ICONS,
        "source_colors": SOURCE_COLORS,
        "source_colors_light": SOURCE_COLORS_LIGHT,
        "top5_bg_color": today_theme["bg"],
        "top5_title_color": today_theme["title"],
        "top5_number_color": today_theme["number"],
    }

    text = REPORT_TEXT_TEMPLATE.render(**context).strip()
    html = REPORT_HTML_TEMPLATE.render(**context).strip()
    return text, html
