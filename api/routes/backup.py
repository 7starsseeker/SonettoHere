"""REST API — 配置导出/导入备份。"""

import base64
import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router = APIRouter()

BACKUP_VERSION = "1.0"

# 项目根目录（由本文件位置向上推 2 级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 需要备份的文件/目录（相对 _PROJECT_ROOT 的路径）
_BACKUP_PATHS = [
    ".env",
    "providers.yaml",
    "config/personas/USER.md",
    "config/personas/SOUL.md",
    "config/personas/AGENTS.md",
    "config/personas/memory.yaml",
    "api/data/path_whitelist.yaml",
    "api/data/sonetto_blocker.yaml",
    "api/data/const-sessions/",
    "anthropic_skills/",
    "tools/bilibili/cookie.txt",
]


def _collect_files() -> dict[str, str]:
    """扫描所有备份路径，返回 {相对路径: base64 内容}。"""
    files: dict[str, str] = {}
    for rel in _BACKUP_PATHS:
        full = _PROJECT_ROOT / rel
        if not full.exists():
            continue
        if full.is_dir():
            for fpath in sorted(full.rglob("*")):
                if fpath.is_file():
                    _add_file(files, fpath)
        else:
            _add_file(files, full)
    return files


def _add_file(files: dict[str, str], fpath: Path):
    """将单个文件 base64 编码后加入 dict。"""
    try:
        rel = str(fpath.relative_to(_PROJECT_ROOT))
        raw = fpath.read_bytes()
        files[rel] = base64.b64encode(raw).decode("ascii")
    except Exception:
        pass


def _restore_files(files: dict[str, str]) -> list[str]:
    """将 base64 编码的文件内容写回磁盘。返回恢复的文件路径列表。"""
    restored: list[str] = []
    for rel_path, b64_content in files.items():
        try:
            full = _PROJECT_ROOT / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            raw = base64.b64decode(b64_content)
            full.write_bytes(raw)
            restored.append(rel_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"还原文件失败 {rel_path}: {e}",
            )
    return restored


@router.get("/backup/export")
async def export_backup(request: Request):
    """导出全部配置为 JSON 文件下载。"""
    files = _collect_files()
    data = {
        "backup_version": BACKUP_VERSION,
        "exported_at": time.time(),
        "files": files,
    }
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="sonetto-backup-{int(time.time())}.json"',
        },
    )


@router.post("/backup/import")
async def import_backup(request: Request):
    """上传 JSON 备份文件并还原配置。"""
    try:
        body = await request.body()
        data = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="无法解析备份文件，请确保上传的是有效的 JSON")

    version = data.get("backup_version", "")
    files = data.get("files")
    if not isinstance(files, dict):
        raise HTTPException(status_code=400, detail="备份文件格式错误：缺少 files 字段")

    restored = _restore_files(files)
    return {
        "status": "ok",
        "restored_count": len(restored),
        "restored_files": restored,
        "backup_version": version,
    }
