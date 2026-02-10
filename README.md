# AI Daily Digest Agent

<div align="center">

**一个全自动的 AI 新闻聚合 Agent,每日从多个信息源采集 AI 领域资讯,利用 LLM 进行智能筛选、分类和摘要,生成精美的日报邮件。**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## ✨ 核心特性

- 🔍 **多源采集**: 自动从 RSS、GitHub、NewsAPI、Reddit、Twitter、网页爬虫等多个渠道采集 AI 资讯
- 🤖 **智能摘要**: 使用通义千问/智谱 GLM 等国产大模型自动生成中文摘要
- 📊 **智能分类**: 自动将新闻分为论文研究、产品发布、行业动态、教程观点、开源项目等类别
- 🎯 **重要性评分**: 综合考量来源权威度、社交热度、时效性等因素智能排序
- 📧 **邮件推送**: 每日定时生成精美的 HTML 邮件报告并自动发送
- 🔄 **灵活部署**: 支持 GitHub Actions 零成本自动化部署、本地定时任务等多种方式
- 🛡️ **容错设计**: 完善的错误处理机制,单个数据源失败不影响整体运行

## 📋 目录

- [快速开始](#-快速开始)
- [配置指南](#-配置指南)
- [使用方法](#-使用方法)
- [部署方案](#-部署方案)
- [项目结构](#-项目结构)
- [常见问题](#-常见问题)
- [扩展开发](#-扩展开发)

## 🚀 快速开始

### 环境要求

- Python 3.11 或更高版本
- 至少一个 LLM API Key (通义千问或智谱 GLM)
- 邮箱账号 (支持 SMTP)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <your-repo-url>
   cd ai-daily-digest
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 复制配置模板
   cp .env.example .env
   
   # 编辑 .env 文件,填写必需的配置
   # 至少需要配置: LLM API Key + 邮件配置
   ```

4. **测试运行**
   ```bash
   python main.py --run-once
   ```

如果一切正常,您将在几分钟内收到第一封 AI 日报邮件! 📬

## ⚙️ 配置指南

### 必需配置

#### 1. LLM API 配置

项目支持通义千问和智谱 GLM,**至少需要配置其中一个**:

**通义千问 (推荐)**
- 获取地址: https://dashscope.console.aliyun.com/apiKey
- 免费额度: 新用户赠送 100 万 tokens
- 配置示例:
  ```env
  QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  QWEN_MODEL=qwen-plus
  ```

**智谱 GLM**
- 获取地址: https://open.bigmodel.cn/usercenter/apikeys
- 免费模型: `glm-4-flash` 完全免费
- 配置示例:
  ```env
  ZHIPU_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxx
  ZHIPU_MODEL=glm-4-flash
  ```

**模型切换策略**
```env
LLM_STRATEGY=fallback  # primary: 只用主模型 | fallback: 失败切换 | round_robin: 轮流使用
LLM_PRIMARY_PROVIDER=qwen  # 主模型: qwen 或 zhipu
```

#### 2. 邮件配置

**Gmail 配置 (推荐)**

1. 访问 https://myaccount.google.com/apppasswords
2. 生成应用专用密码 (16位)
3. 配置 `.env`:
   ```env
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SENDER=your-email@gmail.com
   EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # 应用专用密码
   EMAIL_RECIPIENTS=recipient@example.com
   ```

**其他邮箱配置**

| 邮箱服务 | SMTP 地址 | 端口 | 备注 |
|---------|----------|------|------|
| Outlook | smtp.office365.com | 587 | - |
| QQ 邮箱 | smtp.qq.com | 587 | 需开启 SMTP 并使用授权码 |
| 163 邮箱 | smtp.163.com | 465 | 需开启 SMTP 并使用授权码 |

### 可选配置

#### GitHub Token (强烈推荐)

用于采集 GitHub 热门项目和仓库动态:

- 获取地址: https://github.com/settings/tokens
- 权限: 勾选 `public_repo`
- 免费额度: 5000 次/小时
- 配置:
  ```env
  GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

#### NewsAPI (可选)

用于采集英文科技新闻:

- 获取地址: https://newsapi.org/register
- 免费额度: 100 次/天
- 配置:
  ```env
  NEWSAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

#### Twitter/Reddit (可选)

如需采集社交媒体内容,可配置:
```env
TWITTER_BEARER_TOKEN=xxxxx
REDDIT_CLIENT_ID=xxxxx
REDDIT_CLIENT_SECRET=xxxxx
```

### 数据源配置

编辑 `sources.yaml` 可自定义数据源:

```yaml
rss:
  - name: "arXiv cs.AI"
    url: "https://export.arxiv.org/rss/cs.AI"

github:
  watch_repos:
    - "langchain-ai/langchain"
    - "vllm-project/vllm"
```

## 📖 使用方法

### 本地运行

**立即执行一次**
```bash
python main.py --run-once
```

**启动定时调度** (每日 10:00 自动执行)
```bash
python main.py
```

修改执行时间:
```env
SCHEDULE_HOUR=8      # 改为每日 8:00
SCHEDULE_MINUTE=30   # 改为每日 8:30
```

### 查看历史报告

所有生成的报告会保存在 `archive/` 目录:
```
archive/
  2026-02-09.md
  2026-02-10.md
  ...
```

## 🚢 部署方案

### 方案 1: GitHub Actions (推荐,零成本)

**优点**: 完全免费、无需服务器、自动运行、稳定可靠

**步骤**:

1. **Fork 本项目到你的 GitHub 账号**

2. **配置 GitHub Secrets**
   
   进入仓库 Settings → Secrets and variables → Actions,添加以下 Secrets:
   
   | Secret 名称 | 说明 | 示例 |
   |------------|------|------|
   | `QWEN_API_KEY` | 通义千问 API Key | sk-xxx |
   | `ZHIPU_API_KEY` | 智谱 API Key | xxx.xxx |
   | `EMAIL_SENDER` | 发件邮箱 | your@gmail.com |
   | `EMAIL_PASSWORD` | 邮箱密码/授权码 | xxxx xxxx xxxx xxxx |
   | `EMAIL_RECIPIENTS` | 收件人 | recipient@example.com |
   | `GH_TOKEN` | GitHub Token (可选) | ghp_xxx |
   
   其他配置使用默认值即可。

3. **启用 GitHub Actions**
   
   进入仓库 Actions 页面,点击 "I understand my workflows, go ahead and enable them"

4. **测试运行**
   
   Actions → AI Daily Digest → Run workflow → Run workflow

5. **自动执行**
   
   工作流会在每天 UTC 02:00 (北京时间 10:00) 自动运行

**修改执行时间**:

编辑 `.github/workflows/daily-digest.yml`:
```yaml
schedule:
  - cron: '0 2 * * *'  # UTC 02:00 = 北京时间 10:00
```

### 方案 2: Windows 计划任务

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 每天 10:00
4. 操作: 启动程序
   - 程序: `python.exe` 的完整路径
   - 参数: `main.py --run-once`
   - 起始于: 项目目录路径

### 方案 3: Linux Cron

编辑 crontab:
```bash
crontab -e
```

添加:
```cron
0 10 * * * cd /path/to/ai-daily-digest && /usr/bin/python3 main.py --run-once
```

### 方案 4: 云服务器

使用最低配云服务器 (1核1G,月费约 30-50 元):
- 腾讯云轻量应用服务器
- 阿里云 ECS
- AWS EC2 (t2.micro 免费层)

配合 systemd timer 或 cron 定时执行。

## 📁 项目结构

```
ai-daily-digest/
├── main.py                # 主程序入口
├── config.py              # Pydantic 配置管理
├── models.py              # 数据模型定义
├── collectors.py          # 数据采集器 (RSS/GitHub/NewsAPI/Reddit/Twitter/Scraper)
├── processing.py          # 数据处理 (去重/分类/评分/多样性选择)
├── llm.py                 # LLM 路由和调用
├── report.py              # 报告生成 (文本/HTML)
├── delivery.py            # 邮件发送
├── requirements.txt       # Python 依赖
├── requirements-dev.txt   # 开发依赖 (pytest, ruff)
├── pyproject.toml         # 项目配置 (ruff, pytest)
├── .env.example           # 环境变量模板
├── sources.yaml           # 数据源配置
├── llm_providers.yaml     # LLM 供应商配置
├── LICENSE                # MIT 许可证
├── DEPLOY.md              # 详细部署指南
├── .github/
│   └── workflows/
│       ├── daily-digest.yml  # 每日定时任务
│       └── ci.yml            # PR 质量检查 (测试/lint)
├── tests/                 # 单元测试
│   ├── test_config.py
│   ├── test_models.py
│   └── test_processing.py
├── docs/                  # 技术文档
│   ├── README.md          # 文档索引
│   └── implementation.md  # 实现细节说明
├── scripts/               # 开发调试脚本
│   ├── README.md          # 脚本说明
│   ├── test_config.py     # 配置测试
│   ├── debug_llm.py       # LLM 调试
│   └── setup_git.ps1      # Git 初始化 (Windows)
└── archive/               # 历史报告归档 (自动生成)
```

## ❓ 常见问题

### Q1: 收不到邮件怎么办?

**检查清单**:
1. 确认邮箱配置正确 (SMTP 地址、端口、密码)
2. Gmail 用户必须使用应用专用密码,不能用账号密码
3. 检查垃圾邮件箱
4. 查看程序日志是否有错误信息

### Q2: LLM 调用失败怎么办?

**常见原因**:
1. API Key 错误或过期 → 重新获取
2. 余额不足 → 充值或使用免费模型 (glm-4-flash)
3. 网络问题 → 检查网络连接
4. 配置错误 → 检查 `.env` 中的 `QWEN_API_KEY` 等配置

**解决方案**:
- 配置 `LLM_STRATEGY=fallback` 启用备用模型
- 同时配置千问和智谱,互为备份

### Q3: GitHub Actions 运行失败?

**检查**:
1. 确认所有必需的 Secrets 都已配置
2. 查看 Actions 日志定位具体错误
3. 确认 `.github/workflows/daily-digest.yml` 文件存在

### Q4: 如何添加新的数据源?

编辑 `sources.yaml`:

```yaml
rss:
  - name: "新数据源名称"
    url: "https://example.com/feed.xml"

websites:
  - name: "新网站"
    url: "https://example.com"
    selector: "a.article-link"  # CSS 选择器
```

### Q5: 如何更换 LLM 模型?

**方法 1: 切换已支持的模型**
```env
LLM_PRIMARY_PROVIDER=zhipu  # 从千问切换到智谱
```

**方法 2: 添加新模型 (如 DeepSeek)**

1. 编辑 `llm_providers.yaml`:
   ```yaml
   providers:
     deepseek:
       name: "DeepSeek"
       env_key: "DEEPSEEK_API_KEY"
       env_model: "DEEPSEEK_MODEL"
       env_base_url: "DEEPSEEK_BASE_URL"
       default_model: "deepseek-chat"
       default_base_url: "https://api.deepseek.com/v1"
   ```

2. 在 `.env` 中添加:
   ```env
   DEEPSEEK_API_KEY=sk-xxx
   DEEPSEEK_MODEL=deepseek-chat
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
   LLM_PRIMARY_PROVIDER=deepseek
   ```

### Q6: 如何调整新闻数量?

编辑 `main.py` 第 84 行的 `max_count` 参数:
```python
items = select_diverse_items(items, max_count=10)  # 改为你想要的数量,如 20
```

## 🔧 扩展开发

### 添加新的数据采集器

1. 在 `collectors.py` 中创建新类:
   ```python
   class MyCollector(BaseCollector):
       source_type = "my_source"
       
       def collect(self) -> list[NewsItem]:
           # 实现采集逻辑
           return items
   ```

2. 在 `main.py` 中注册:
   ```python
   collectors = [
       # ...
       MyCollector("sources.yaml"),
   ]
   ```

### 自定义邮件模板

编辑 `report.py` 中的 `REPORT_HTML_TEMPLATE` 变量,使用 Jinja2 语法自定义样式。

### 添加 Webhook 推送

在 `delivery.py` 中添加新函数,支持推送到 Slack、Discord、钉钉等平台。

## 📚 更多文档

- **[实现细节说明](docs/implementation.md)**: 深入了解数据采集、评分、筛选算法
- **[开发调试脚本](scripts/README.md)**: 配置测试、LLM 调试等辅助工具
- **[部署指南](DEPLOY.md)**: 无 Git 环境下的手动部署步骤

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

本项目使用了以下优秀的开源项目:
- [feedparser](https://github.com/kurtmckee/feedparser) - RSS 解析
- [httpx](https://github.com/encode/httpx) - HTTP 客户端
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析
- [OpenAI Python SDK](https://github.com/openai/openai-python) - LLM 调用
- [APScheduler](https://github.com/agronholm/apscheduler) - 任务调度

---

<div align="center">

**如果这个项目对你有帮助,欢迎 Star ⭐️**

Made with ❤️ by AI Daily Digest Team

</div>
