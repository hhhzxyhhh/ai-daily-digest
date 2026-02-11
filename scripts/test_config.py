import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - imports after path modification
from config import load_settings  # noqa: E402

settings = load_settings()

print("=== Settings Debug Info ===")
print(f"qwen_api_key: {'已配置 ✅' if settings.qwen_api_key else '未配置 ❌'}")
print(f"zhipu_api_key: {'已配置 ✅' if settings.zhipu_api_key else '未配置 ❌'}")
print(f"llm_primary_provider: {settings.llm_primary_provider}")
print(f"llm_secondary_provider: {settings.llm_secondary_provider}")
print(f"llm_strategy: {settings.llm_strategy}")

# 安全提示：仅显示配置状态，不输出完整密钥
if settings.qwen_api_key:
    print(f"\n✅ Qwen API Key 已配置 (前8位: {settings.qwen_api_key[:8]}...)")
else:
    print("\n❌ Qwen API Key 未配置")

if settings.zhipu_api_key:
    print(f"✅ Zhipu API Key 已配置 (前8位: {settings.zhipu_api_key[:8]}...)")
else:
    print("❌ Zhipu API Key 未配置")
