
import os
from pathlib import Path
from typing import List, Dict, Any

WORKSPACE_ROOT = Path("workspace").resolve()

def ensure_workspace() -> Path:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    return WORKSPACE_ROOT

def resolve_safe_path(relative_path: str) -> Path:
    base = ensure_workspace()
    target = (base / relative_path).resolve()
    if not str(target).startswith(str(base)):
        raise PermissionError(f"Access denied outside workspace: {relative_path}")
    return target

def write_file(relative_path: str, content: str) -> Dict[str, Any]:
    target = resolve_safe_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"status": "written", "path": str(target), "bytes": len(content.encode("utf-8"))}

def read_file(relative_path: str) -> str:
    target = resolve_safe_path(relative_path)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")
    return target.read_text(encoding="utf-8")

def list_files() -> List[str]:
    base = ensure_workspace()
    return [str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()]


