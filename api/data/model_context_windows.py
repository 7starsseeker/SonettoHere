"""知名模型的上下文窗口默认值。

优先级（高 → 低）：
1. config/model_context_windows.yaml（用户自定义覆盖）
2. OpenRouter /api/v1/models（启动时动态拉取，精确模型名匹配）
3. 本文件的 MODEL_CONTEXT_WINDOWS（硬编码保底表，子串匹配）
4. DEFAULT_WINDOW（通用兜底值）

get_context_window() — 按模型名匹配，支持子串匹配。
"""
from pathlib import Path
import json
import urllib.request
import urllib.error

# 硬编码保底映射表（按匹配优先级从高到低排列）
# key 是模型名的小写子串，value 是上下文窗口 token 数
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # ── OpenAI ──
    "gpt-4.1": 1_047_576,
    "gpt-4o": 128_000,
    "gpt-4": 128_000,
    "o3": 200_000,
    "o4-mini": 200_000,
    "o1": 200_000,
    # ── Anthropic ──
    "claude": 200_000,
    # ── DeepSeek ──
    "deepseek-v4": 1_000_000,
    "deepseek-v3": 128_000,
    "deepseek-r1": 128_000,
    "deepseek": 128_000,
    # ── Google ──
    "gemini-2.5-pro": 1_048_576,
    "gemini-2.5-flash": 1_048_576,
    "gemini-2.0": 1_048_576,
    "gemini-1.5": 2_000_000,
    "gemini": 1_048_576,
    # ── Meta ──
    "llama-4-scout": 10_000_000,
    "llama-4": 1_000_000,
    "llama-3": 128_000,
    "llama": 128_000,
    # ── Mistral ──
    "mistral-large": 128_000,
    "mistral-small": 128_000,
    "mistral": 128_000,
    # ── Qwen ──
    "qwen": 128_000,
    # ── Cohere ──
    "command-a": 256_000,
    "command-r": 128_000,
    "command": 128_000,
    # ── xAI ──
    "grok": 200_000,
}

# 通用兜底值（没有任何匹配时使用）
DEFAULT_WINDOW: int = 128_000

# 用户自定义覆盖文件的路径
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "model_context_windows.yaml"

# OpenRouter 缓存（惰性加载）
_OPENROUTER_CACHE: dict[str, int] | None = None
_OPENROUTER_FETCHED = False

# OpenRouter API 地址（无需 API Key）
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"


def _load_overrides() -> dict[str, int]:
    """从 YAML 配置文件加载用户自定义覆盖。"""
    import yaml
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        overrides = data.get("overrides", {})
        return {k: int(v) for k, v in overrides.items()}
    except Exception:
        return {}


def fetch_openrouter_models() -> dict[str, int]:
    """从 OpenRouter API 拉取模型上下文窗口数据。

    Returns:
        {模型ID: context_length, ...} 的字典。
        失败时返回空字典。
    """
    try:
        req = urllib.request.Request(
            OPENROUTER_API_URL,
            headers={"User-Agent": "SonettoHere/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        models = data.get("data", [])
        result: dict[str, int] = {}
        for m in models:
            ctx = m.get("context_length")
            if ctx and isinstance(ctx, (int, float)):
                result[m["id"].lower()] = int(ctx)
        return result
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            OSError, TimeoutError):
        return {}


def _ensure_openrouter_cache() -> dict[str, int]:
    """确保 OpenRouter 缓存已初始化（惰性加载）。"""
    global _OPENROUTER_CACHE, _OPENROUTER_FETCHED
    if not _OPENROUTER_FETCHED:
        _OPENROUTER_FETCHED = True
        data = fetch_openrouter_models()
        if data:
            _OPENROUTER_CACHE = data
            print(f"[context-window] loaded {len(data)} model(s) from OpenRouter")
    return _OPENROUTER_CACHE or {}


def get_context_window(model_name: str) -> int:
    """按模型名查找上下文窗口。

    匹配优先级：
    1. YAML 配置文件中的精确模型名匹配
    2. OpenRouter 动态数据中的精确模型名匹配
    3. 硬编码表中的子串匹配（如 "gpt-4o" 匹配 "gpt-4o"）
    4. 通用兜底值
    """
    model_lower = model_name.lower()

    # 1. 精确匹配（YAML 配置优先）
    overrides = _load_overrides()
    if model_lower in overrides:
        return overrides[model_lower]

    # 2. 精确匹配（OpenRouter 动态数据）
    or_data = _ensure_openrouter_cache()
    if model_lower in or_data:
        return or_data[model_lower]

    # 3. 子串匹配（硬编码保底表）
    for key, value in MODEL_CONTEXT_WINDOWS.items():
        if key in model_lower:
            return value

    # 4. 兜底
    return DEFAULT_WINDOW


def preload_openrouter() -> None:
    """预加载 OpenRouter 数据（用于启动时主动触发，而非等待首次调用）。"""
    _ensure_openrouter_cache()
