#!/usr/bin/env python3
"""核对结构化验收清单的覆盖关系；不解析测试日志语义。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class ManifestError(ValueError):
    pass


def local(root: Path, value: str) -> Path:
    candidate = Path(value)
    candidate = candidate if candidate.is_absolute() else root / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ManifestError(f"路径超出根目录：{value}")
    current = candidate
    while current != root and current != current.parent:
        if current.is_symlink():
            raise ManifestError(f"不接受符号链接输入：{value}")
        current = current.parent
    return resolved


def nonempty_list(item: dict, key: str, index: int) -> list[str]:
    value = item.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise ManifestError(f"requirements[{index}].{key} 必须是非空字符串数组")
    return value


def check(root: Path, manifest_path: str) -> dict:
    path = local(root, manifest_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    requirements = data.get("requirements")
    commands = data.get("commands")
    if not isinstance(requirements, list) or not requirements:
        raise ManifestError("requirements 必须是非空数组")
    if not isinstance(commands, list):
        raise ManifestError("commands 必须是数组")
    for index, item in enumerate(requirements):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ManifestError(f"requirements[{index}].id 缺失")
        for key in ("implementation", "tests", "evidence"):
            for value in nonempty_list(item, key, index):
                if not local(root, value).exists():
                    raise ManifestError(f"requirements[{index}] 引用不存在：{value}")
        if item.get("status") != "verified":
            raise ManifestError(f"requirements[{index}] 必须明确 status=verified")
    for index, item in enumerate(commands):
        if not isinstance(item, dict) or not isinstance(item.get("command"), str) or not item["command"]:
            raise ManifestError(f"commands[{index}].command 缺失")
        if not isinstance(item.get("cwd"), str) or not local(root, item["cwd"]).is_dir():
            raise ManifestError(f"commands[{index}].cwd 必须是根内目录")
        if not isinstance(item.get("exit_code"), int):
            raise ManifestError(f"commands[{index}].exit_code 必须是整数")
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not local(root, evidence).is_file():
            raise ManifestError(f"commands[{index}].evidence 必须是根内文件")
    return {"valid": True, "requirements": len(requirements), "commands": len(commands)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--manifest", required=True)
    try:
        root = Path(p.parse_args().root).resolve(strict=True)
        print(json.dumps(check(root, p.parse_args().manifest), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"valid": False, "原因": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
