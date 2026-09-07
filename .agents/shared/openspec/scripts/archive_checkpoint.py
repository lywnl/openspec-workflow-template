#!/usr/bin/env python3
"""记录和核对规范同步检查点；不执行同步、迁移、提交或移动。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
IGNORED = {".git", "__pycache__", ".venv", "node_modules"}


class CheckpointError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inside(root: Path, value: str) -> Path:
    candidate = Path(value)
    candidate = candidate if candidate.is_absolute() else root / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise CheckpointError(f"路径超出根目录：{value}")
    current = candidate
    while current != root and current != current.parent:
        if current.is_symlink():
            raise CheckpointError(f"不接受符号链接输入：{value}")
        current = current.parent
    return resolved


def rel(root: Path, value: str) -> str:
    return inside(root, value).relative_to(root).as_posix()


def snapshot(root: Path, values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        path = inside(root, value)
        if not path.exists():
            result[rel(root, value)] = "missing"
            continue
        paths = [path]
        if path.is_dir():
            for base, dirs, files in os.walk(path, followlinks=False):
                dirs[:] = sorted(d for d in dirs if d not in IGNORED)
                paths.extend(Path(base) / d for d in dirs)
                paths.extend(Path(base) / f for f in sorted(files))
        for item in paths:
            item = inside(root, str(item))
            key = item.relative_to(root).as_posix()
            if item.is_dir():
                result[key + "/"] = "directory"
            elif item.is_file():
                mode = stat.S_IMODE(item.stat().st_mode)
                result[key] = f"file:mode={mode:04o}:sha256={digest(item.read_bytes())}"
            else:
                raise CheckpointError(f"输入不是普通文件或目录：{key}")
    return dict(sorted(result.items()))


def journal_path(root: Path, change: str) -> Path:
    return inside(root, str(Path(change) / "reports/archive-checkpoint/journal.json"))


def load(root: Path, change: str) -> dict:
    path = journal_path(root, change)
    if not path.is_file():
        raise CheckpointError(f"检查点不存在：{path.relative_to(root)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    valid_paths = {change, data.get("change"), data.get("archived_change_path")}
    if data.get("version") != VERSION or change not in valid_paths:
        raise CheckpointError("检查点版本或变更路径不匹配")
    return data


def equal(actual: dict[str, str], expected: dict[str, str], label: str) -> None:
    if actual != expected:
        keys = sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
        raise CheckpointError(f"{label}已变化：{', '.join(keys[:12])}")


def command(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve(strict=True)
    change = rel(root, args.change)
    journal = journal_path(root, change)
    if args.action == "prepare":
        if journal.exists():
            raise CheckpointError("检查点已存在，不能覆盖")
        if not args.archive or not args.profile or not args.mode:
            raise CheckpointError("prepare 必须提供 --profile、--mode 和 --archive")
        if inside(root, args.archive).exists():
            raise CheckpointError("归档目标已存在，不能覆盖")
        targets = sorted({rel(root, x) for x in args.target})
        frozen = sorted({rel(root, x) for x in args.frozen})
        if not targets:
            raise CheckpointError("prepare 至少需要一个规范同步目标")
        data = {
            "version": VERSION, "change": change, "profile": args.profile,
            "verification_mode": args.mode, "active_change_path": change,
            "archived_change_path": args.archive, "stage": "prepared",
            "targets": targets, "frozen_inputs": frozen,
            "before": snapshot(root, targets), "frozen_snapshot": snapshot(root, frozen),
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        }
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"valid": True, "stage": "prepared", "journal": journal.relative_to(root).as_posix()}
    data = load(root, change)
    targets = data["targets"]
    current = snapshot(root, targets)
    if args.action == "check":
        allowed = set(data["before"])
        allowed.update(data.get("expected", {}))
        if data["stage"] == "synced":
            allowed = set(data.get("expected", {}))
        for key, value in current.items():
            if key not in allowed:
                raise CheckpointError(f"同步目标出现未登记状态：{key}")
            if data["stage"] == "synced" and value != data.get("expected", {}).get(key):
                raise CheckpointError(f"synced 阶段目标已回退：{key}")
            if data["stage"] == "prepared" and value not in (data["before"].get(key), data.get("expected", {}).get(key)):
                raise CheckpointError(f"同步目标出现未登记状态：{key}")
        equal(snapshot(root, data["frozen_inputs"]), data["frozen_snapshot"], "非同步输入")
        return {"valid": True, "stage": data["stage"]}
    if args.action == "synced":
        if data["stage"] != "prepared":
            raise CheckpointError("只有 prepared 检查点可以标记 synced")
        expected = snapshot(root, targets)
        equal(snapshot(root, data["frozen_inputs"]), data["frozen_snapshot"], "非同步输入")
        data["expected"] = expected
        data["stage"] = "synced"
        data["validation"] = {"command": args.validation_command, "exit_code": args.exit_code}
    elif args.action == "archived":
        if data["stage"] != "synced":
            raise CheckpointError("只有 synced 检查点可以标记 archived")
        equal(current, data["expected"], "规范同步结果")
        if inside(root, data["active_change_path"]).exists():
            raise CheckpointError("活动变更目录仍存在，不能标记 archived")
        if inside(root, data["archived_change_path"]).exists() is False:
            raise CheckpointError("归档目录不存在")
        data["stage"] = "archived"
        data["post_archive_check"] = {"command": args.validation_command, "exit_code": args.exit_code}
    else:
        raise CheckpointError(f"未知操作：{args.action}")
    journal.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"valid": True, "stage": data["stage"]}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "check", "synced", "archived"))
    p.add_argument("--root", required=True)
    p.add_argument("--change", required=True)
    p.add_argument("--profile", choices=("fast", "standard", "strict"))
    p.add_argument("--mode", choices=("machine", "manual"))
    p.add_argument("--archive")
    p.add_argument("--target", action="append", default=[])
    p.add_argument("--frozen", action="append", default=[])
    p.add_argument("--validation-command", default="")
    p.add_argument("--exit-code", type=int, default=0)
    return p


def main() -> int:
    try:
        print(json.dumps(command(parser().parse_args()), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"valid": False, "原因": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
