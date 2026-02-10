import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import load_settings
from llm import LLMRouter

settings = load_settings()
print("=== Debug Load Providers ===")

print(f"llm_primary_provider: {settings.llm_primary_provider}")
print(f"llm_secondary_provider: {settings.llm_secondary_provider}")
print(f"qwen_api_key: {'已配置 ✅' if settings.qwen_api_key else '未配置 ❌'}")
print(f"zhipu_api_key: {'已配置 ✅' if settings.zhipu_api_key else '未配置 ❌'}")

print("\n--- Testing environment variables ---")
print(f"QWEN_API_KEY in env: {'QWEN_API_KEY' in os.environ}")
print(f"QWEN_API_KEY: {'已设置 ✅' if os.getenv('QWEN_API_KEY') else '未设置 ❌'}")
print(f"ZHIPU_API_KEY in env: {'ZHIPU_API_KEY' in os.environ}")
print(f"ZHIPU_API_KEY: {'已设置 ✅' if os.getenv('ZHIPU_API_KEY') else '未设置 ❌'}")

print("\n--- Trying to load providers manually ---")
router = LLMRouter(settings, "llm_providers.yaml")
print(f"Success! Loaded {len(router.providers)} providers")
for i, provider in enumerate(router.providers):
    print(f"Provider {i+1}: {provider.name} - {provider.model}")
