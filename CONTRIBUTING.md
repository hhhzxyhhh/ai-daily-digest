# 贡献指南

感谢您对 AI Daily Digest 项目的关注！

## 开发环境设置

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd ai-daily-digest
```

### 2. 安装依赖

```bash
# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 3. 配置环境

```bash
cp .env.example .env
# 编辑 .env 填写必要配置
```

## 开发工作流

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_processing.py

# 查看测试覆盖率
pytest --cov=. --cov-report=html
```

### 代码质量检查

```bash
# 运行 ruff 检查
ruff check .

# 自动修复可修复的问题
ruff check --fix .

# 格式化代码
ruff format .
```

### 调试工具

```bash
# 测试配置加载
python scripts/test_config.py

# 调试 LLM 提供商
python scripts/debug_llm.py
```

### 本地运行

```bash
# 单次执行
python main.py --run-once

# 定时执行（每日 10:00）
python main.py
```

## 提交代码

### 提交前检查清单

- [ ] 运行 `pytest` 确保所有测试通过
- [ ] 运行 `ruff check .` 确保代码符合规范
- [ ] 运行 `ruff format .` 格式化代码
- [ ] 更新相关文档（如修改了实现逻辑）
- [ ] 添加必要的测试用例

### 提交信息规范

使用清晰的提交信息：

```
feat: 添加新的数据源采集器
fix: 修复邮件发送失败的问题
docs: 更新 README 配置说明
test: 添加 processing 模块的单元测试
refactor: 重构评分算法
```

### Pull Request 流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 代码规范

### Python 风格

- 遵循 PEP 8
- 使用 ruff 进行代码检查和格式化
- 使用类型注解（Type Hints）
- 函数和类添加文档字符串

### 测试规范

- 为新功能添加单元测试
- 测试覆盖率应保持在合理水平
- 使用描述性的测试函数名

### 文档规范

- 修改代码时同步更新相关文档
- 重要功能添加使用示例
- API 变更需在 README 中说明

## 项目结构说明

```
ai-daily-digest/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── models.py            # 数据模型
├── collectors.py        # 数据采集
├── processing.py        # 数据处理
├── llm.py              # LLM 调用
├── report.py           # 报告生成
├── delivery.py         # 邮件发送
├── tests/              # 单元测试
├── docs/               # 技术文档
└── scripts/            # 开发工具
```

## 常见问题

### Q: 如何添加新的数据源？

1. 在 `collectors.py` 中创建新的采集器类
2. 继承 `BaseCollector` 并实现 `collect()` 方法
3. 在 `main.py` 中注册新采集器
4. 添加相应的单元测试

### Q: 如何修改评分算法？

1. 编辑 `processing.py` 中的 `score()` 函数
2. 更新 `docs/implementation.md` 中的算法说明
3. 添加或更新测试用例

### Q: 测试失败怎么办？

1. 查看测试输出的错误信息
2. 确保 `.env` 配置正确（测试不需要真实 API Key）
3. 检查是否有依赖未安装

## 获取帮助

- 提交 Issue: 描述问题、期望行为、实际行为
- 讨论功能: 在 Discussions 中发起讨论
- 安全问题: 请私下联系维护者

---

再次感谢您的贡献！🎉
