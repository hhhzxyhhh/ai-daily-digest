# LLM 配置与使用指南

本项目支持多种主流大模型（LLM）API，您可以根据需求灵活切换或组合使用。

## 支持的模型列表

| 提供商 | 环境变量前缀 | 默认模型 | 官网/API Key |
|--------|------------|----------|--------------|
| **通义千问** | `QWEN_` | `qwen-plus` | [阿里云 DashScope](https://dashscope.console.aliyun.com/apiKey) |
| **智谱 GLM** | `ZHIPU_` | `glm-4-flash` | [智谱 AI](https://open.bigmodel.cn/usercenter/apikeys) |
| **DeepSeek** | `DEEPSEEK_` | `deepseek-chat` | [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) |
| **Moonshot** | `MOONSHOT_` | `moonshot-v1-8k` | [Kimi 开放平台](https://platform.moonshot.cn/console/api-keys) |
| **豆包** | `DOUBAO_` | `doubao-pro-4k` | [火山引擎](https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint) |
| **OpenAI** | `OPENAI_` | `gpt-4o-mini` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Claude** | `CLAUDE_` | `claude-3-5-haiku` | [Anthropic Console](https://console.anthropic.com/settings/keys) |
| **Gemini** | `GEMINI_` | `gemini-2.0-flash` | [Google AI Studio](https://aistudio.google.com/app/apikey) |

## 配置方法

1. 复制 `.env.example` 为 `.env`。
2. 找到您想使用的模型部分，填入 API Key。
3. 修改 `LLM_PRIMARY_PROVIDER` 为您选择的提供商标识（如 `deepseek`, `openai` 等）。

### 示例：使用 DeepSeek 作为主力模型

```env
# 策略配置
LLM_STRATEGY=fallback
LLM_PRIMARY_PROVIDER=deepseek    # 设置为主模型
LLM_SECONDARY_PROVIDER=qwen      # 设置为备用模型（当策略为 fallback 时生效）

# DeepSeek 配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

## 调度策略

系统支持三种 LLM 调用策略，通过 `LLM_STRATEGY` 环境变量控制：

1.  **primary** (默认)
    *   **描述**: 仅使用 `LLM_PRIMARY_PROVIDER` 指定的模型。
    *   **场景**: 只有单一 API Key，或希望固定使用某一个模型。

2.  **fallback** (推荐)
    *   **描述**: 优先使用主模型，如果调用失败（如网络超时、配额耗尽），自动切换到 `LLM_SECONDARY_PROVIDER` 指定的备用模型。
    *   **场景**: 生产环境，需要高可用性保障。

3.  **round_robin**
    *   **描述**: 在支持的所有已配置模型之间轮询使用。
    *   **场景**: 多个 Key 额度较少，希望分摊负载；或者希望生成结果具有多样性。
    *   **注意**: 此模式会循环使用所有在 `llm_providers.yaml` 中定义且在 `.env` 中配置了 API Key 的模型。

## 常见问题

### 1. 豆包 (Doubao) 配置说明
火山引擎（豆包）的 API 调用方式与其他 OpenAI 兼容接口略有不同，重点在于 `model` 参数。
在火山引擎控制台创建推理接入点后，您会获得一个 `ep-` 开头的端点 ID（Endpoint ID）。
**请务必将 `DOUBAO_MODEL` 设置为这个 Endpoint ID**，而不是模型名称。

```env
DOUBAO_MODEL=ep-20240604xxxxxx-xxxxx
```

### 2. Gemini 访问问题
Gemini API (`generativelanguage.googleapis.com`) 在国内通常无法直接访问，需要配置代理或部署在海外服务器环境。如果您的网络环境受限，建议优先使用国内模型（DeepSeek、智谱、通义千问等）。

### 3. OpenAI 模型选择
推荐使用 `gpt-4o-mini`，它在性能和价格之间取得了很好的平衡，非常适合新闻摘要任务。如果追求极致质量，可使用 `gpt-4o`。

### 4. 如何添加自定义模型（如本地 Ollama）？
您可以利用 `openai` 兼容配置来连接本地模型：

1. 编辑 `.env` 中的 OpenAI 部分：
```env
LLM_PRIMARY_PROVIDER=openai
OPENAI_API_KEY=any-string-is-ok
OPENAI_MODEL=llama3
OPENAI_BASE_URL=http://localhost:11434/v1
```
这样就可以通过 OpenAI 协议连接到本地运行的 Ollama 服务。
