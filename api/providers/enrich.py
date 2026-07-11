"""模型元数据并发检测入口。

每新增/更新提供商时，并发执行已注册的所有 enrichment 函数。
通过 register() 扩展，核心代码无需修改（开放/封闭原则）。
"""

import asyncio
from collections.abc import Callable

from api.providers import ProviderConfig
from api.providers.model_context_windows import fill_missing_context_windows
from api.providers.vision import detect_vision_if_available

_registry: list[Callable[[ProviderConfig], object]] = []


def register(func: Callable[[ProviderConfig], object]) -> None:
    """注册一个 enrichment 函数，入参为 ProviderConfig，原地修改。"""
    _registry.append(func)


# 注册内置 enrichment
register(detect_vision_if_available)
register(fill_missing_context_windows)


async def enrich_provider_config(config: ProviderConfig) -> None:
    """并发执行所有已注册的 enrichment 函数。"""
    await asyncio.gather(*(f(config) for f in _registry))