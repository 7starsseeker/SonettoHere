"""为现有 providers 添加 model_context_windows 空字典。

此脚本由 PR #220 (feat/context-windows M3) 引入：
- ProviderConfig 新增 model_context_windows (dict[str, int], default empty dict)

升级方式：
  python upgrade.py
  或直接：python scripts/migrations/m2-model-context-windows.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDERS_PATH = PROJECT_ROOT / "config" / "providers.yaml"


def migrate() -> None:
    if not PROVIDERS_PATH.exists():
        print("[migrate] providers.yaml 不存在，跳过")
        return

    import yaml

    with open(PROVIDERS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    providers = data.get("providers", [])
    changed = 0

    for p in providers:
        if "model_context_windows" not in p:
            p["model_context_windows"] = {}
            changed += 1

    if changed:
        with open(PROVIDERS_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        print(f"[migrate] 已更新 {changed} 个 provider(s)")
    else:
        print("[migrate] 幂等，无需变更")


if __name__ == "__main__":
    migrate()
