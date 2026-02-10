from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from jinja2 import Template

from models import NewsItem


REPORT_TEXT_TEMPLATE = Template(
    """
AI 日报 - {{ date }}

今日概览:
{{ overview }}

TOP 5 重要新闻:
{% for item in top_items %}
- {{ item.title }}
  {{ item.summary }}
  {{ item.url }}
{% endfor %}

分类新闻:
{% for category, items in grouped.items() %}
{{ category }}:
{% for item in items %}
- {{ item.title }}
  {{ item.summary }}
  {{ item.url }}
{% endfor %}
{% endfor %}

统计:
- 今日采集 {{ total }} 条
- 筛选输出 {{ selected }} 条
"""
)


REPORT_HTML_TEMPLATE = Template(
    """
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>AI 日报 - {{ date }}</h2>
    <h3>今日概览</h3>
    <p>{{ overview }}</p>

    <h3>TOP 5 重要新闻</h3>
    <ol>
      {% for item in top_items %}
      <li>
        <strong>{{ item.title }}</strong><br/>
        {{ item.summary }}<br/>
        <a href="{{ item.url }}">{{ item.url }}</a>
      </li>
      {% endfor %}
    </ol>

    <h3>分类新闻</h3>
    {% for category, items in grouped.items() %}
      <h4>{{ category }}</h4>
      <ul>
        {% for item in items %}
        <li>
          <strong>{{ item.title }}</strong><br/>
          {{ item.summary }}<br/>
          <a href="{{ item.url }}">{{ item.url }}</a>
        </li>
        {% endfor %}
      </ul>
    {% endfor %}

    <h3>统计</h3>
    <ul>
      <li>今日采集 {{ total }} 条</li>
      <li>筛选输出 {{ selected }} 条</li>
    </ul>
  </body>
</html>
"""
)


def build_report(items: list[NewsItem], overview: str) -> tuple[str, str]:
    date = datetime.now().strftime("%Y-%m-%d")
    top_items = items[:5]
    grouped: dict[str, list[NewsItem]] = defaultdict(list)
    for item in items:
        grouped[item.category or "其他"].append(item)
    text = REPORT_TEXT_TEMPLATE.render(
        date=date,
        overview=overview,
        top_items=top_items,
        grouped=grouped,
        total=len(items),
        selected=len(items),
    ).strip()
    html = REPORT_HTML_TEMPLATE.render(
        date=date,
        overview=overview,
        top_items=top_items,
        grouped=grouped,
        total=len(items),
        selected=len(items),
    ).strip()
    return text, html
