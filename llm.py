from __future__ import annotations

import itertools
import os
from dataclasses import dataclass

import yaml
from openai import OpenAI

from config import Settings


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    model: str
    base_url: str


class LLMRouter:
    def __init__(self, settings: Settings, providers_path: str) -> None:
        self.settings = settings
        self.providers = self._load_providers(providers_path)
        self._rr_cycle = itertools.cycle(self.providers)

    def _load_providers(self, providers_path: str) -> list[ProviderConfig]:
        with open(providers_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        providers = data.get("providers", {})

        def resolve(provider_key: str) -> ProviderConfig | None:
            cfg = providers.get(provider_key)
            if not cfg:
                return None
            # 将环境变量名转换为 Settings 属性名 (大写转小写下划线)
            # 例如: "QWEN_API_KEY" -> "qwen_api_key"
            api_key_attr = cfg["env_key"].lower()
            model_attr = cfg["env_model"].lower()
            base_url_attr = cfg["env_base_url"].lower()
            
            api_key = getattr(self.settings, api_key_attr, None)
            model = getattr(self.settings, model_attr, None) or cfg.get("default_model", "")
            base_url = getattr(self.settings, base_url_attr, None) or cfg.get("default_base_url", "")
            
            if not api_key:
                return None
            return ProviderConfig(
                name=cfg["name"],
                api_key=api_key,
                model=model,
                base_url=base_url,
            )

        primary = resolve(self.settings.llm_primary_provider)
        secondary = resolve(self.settings.llm_secondary_provider)
        resolved = [p for p in [primary, secondary] if p]
        if not resolved:
            raise ValueError("未配置可用的 LLM API Key")
        return resolved

    def _client(self, provider: ProviderConfig) -> OpenAI:
        return OpenAI(api_key=provider.api_key, base_url=provider.base_url)

    def complete(self, prompt: str) -> str:
        strategy = self.settings.llm_strategy
        if strategy == "round_robin":
            provider = next(self._rr_cycle)
            return self._call(provider, prompt)
        if strategy == "primary":
            return self._call(self.providers[0], prompt)
        if strategy == "fallback" and len(self.providers) >= 2:
            try:
                return self._call(self.providers[0], prompt)
            except Exception:
                return self._call(self.providers[1], prompt)
        return self._call(self.providers[0], prompt)

    def _call(self, provider: ProviderConfig, prompt: str) -> str:
        client = self._client(provider)
        resp = client.chat.completions.create(
            model=provider.model,
            messages=[
                {"role": "system", "content": "你是一位专业的 AI 新闻编辑。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
