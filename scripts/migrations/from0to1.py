"""配置迁移 v0 → v1：为现有 providers 添加 is_default_provider 和 default_model 字段。

此脚本由 PR #218 (feat/default-provider-model M1) 引入：
- ProviderConfig 新增 is_default_provider (bool, default False)
- ProviderConfig 新增 default_model (str | None, default None)

升级方式：
  python upgrade.py
  或直接：python scripts/migrations/from0to1.py
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDERS_PATH = PROJECT_ROOT / "config" / "providers.yaml"


def migrate() -> None:
    if not PROVIDERS_PATH.exists():
        print("[migrate v0→v1] providers.yaml 不存在，跳过")
        return

    import yaml

    with open(PROVIDERS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    providers = data.get("providers", [])
    changed = 0

    for p in providers:
        dirty = False
        if "is_default_provider" not in p:
            p["is_default_provider"] = False
            dirty = True
        if "default_model" not in p:
            p["default_model"] = None
            # default_model=None 会被 to_dict() omit，但仍显式写入确保 schema 一致
            dirty = True
        if dirty:
            changed += 1

    if changed:
        with open(PROVIDERS_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        print(f"[migrate v0→v1] 已更新 {changed} 个 provider(s)")
    else:
        print("[migrate v0→v1] 幂等，无需变更")


if __name__ == "__main__":
    migrate()
