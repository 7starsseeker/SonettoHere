"""模型元数据并发检测入口。

新增/更新提供商时，并发执行视觉能力检测和上下文窗口填充，
确保 model_vision 和 model_context_windows 在创建时同步就绪。
"""

from api.providers import ProviderConfig
from api.providers.model_context_windows import ensure_openrouter_cache, lookup_context_window
from api.providers.vision import detect_vision_if_available


async def enrich_provider_config(
    config: ProviderConfig,
) -> None:
    """并发检测视觉能力和填充上下文窗口，直接原地修改 config。

    Args:
        config: 待补充元数据的 ProviderConfig（原地修改）。
    """
    import asyncio

    async def _detect_vision():
        config.model_vision = await detect_vision_if_available(config)

    async def _fill_context_windows():
        or_data = ensure_openrouter_cache()
        if or_data:
            for model in config.models:
                if model not in config.model_context_windows:
                    ctx = lookup_context_window(model, or_data)
                    if ctx:
                        config.model_context_windows[model] = ctx

    await asyncio.gather(_detect_vision(), _fill_context_windows())
