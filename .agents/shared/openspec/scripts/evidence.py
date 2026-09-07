#!/usr/bin/env python3
"""记录和核验文件基线；不替代真实测试、评审或授权判断。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


IGNORED = {".git", "__pycache__", ".venv", "node_modules"}
RECORD_VERSION = 2
CHECKBOX = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+\[)([ xX])(\])")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class EvidenceError(ValueError):
    """输入或基线不满足校验条件。"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local(root: Path, value: str) -> Path:
    candidate = Path(value)
    candidate = candidate if candidate.is_absolute() else root / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise EvidenceError(f"路径超出指定根：{value}")
    current = candidate
    while current != root and current != current.parent:
        if current.is_symlink():
            raise EvidenceError(f"不接受符号链接输入：{value}")
        current = current.parent
    return resolved


def label(root: Path, value: str) -> str:
    return local(root, value).relative_to(root).as_posix()


def task_lines(data: bytes) -> tuple[bytes, list[bool]]:
    lines = data.decode("utf-8").splitlines(keepends=True)
    normalized: list[str] = []
    states: list[bool] = []
    fence: str | None = None
    for line in lines:
        marker = FENCE.match(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            normalized.append(line)
            continue
        match = CHECKBOX.match(line) if fence is None else None
        if match:
            states.append(match.group(2).lower() == "x")
            line = line[:match.start(2)] + " " + line[match.end(2):]
        normalized.append(line)
    return "".join(normalized).encode("utf-8"), states


def walk_error(error: OSError) -> None:
    raise error


def snapshot(root: Path, inputs: list[str], tasks: str | None = None) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in inputs:
        path = local(root, value)
        if not path.exists():
            raise EvidenceError(f"输入不存在：{value}")
        paths = [path]
        if path.is_dir():
            for base, dirs, files in os.walk(path, followlinks=False, onerror=walk_error):
                dirs[:] = sorted(name for name in dirs if name not in IGNORED)
                paths.extend(Path(base) / name for name in dirs + sorted(files))
        for item in paths:
            item = local(root, str(item))
            key = item.relative_to(root).as_posix()
            if item.is_dir():
                result[key + "/"] = "directory"
            elif item.is_file():
                data = item.read_bytes()
                if key == tasks:
                    data, _ = task_lines(data)
                executable = item.stat().st_mode & 0o111
                result[key] = f"file:exec={executable:03o}:sha256={digest(data)}"
            else:
                raise EvidenceError(f"输入不是普通文件或目录：{key}")
    return dict(sorted(result.items()))


def require_report(root: Path, value: str) -> str:
    path = local(root, value)
    if not path.is_file() or not path.read_bytes().strip():
        raise EvidenceError(f"报告不存在或为空：{value}")
    return path.relative_to(root).as_posix()


def record_path(root: Path, change: str, kind: str) -> Path:
    suffix = "reviews/planning-review.json" if kind == "plan" else "reports/verification.json"
    return local(root, str(Path(change) / suffix))


def load(root: Path, change: str, kind: str, profile: str) -> dict:
    path = record_path(root, change, kind)
    if not path.is_file():
        raise EvidenceError(f"尚无 {kind} 通过记录：{path.relative_to(root)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise EvidenceError("通过记录必须是 JSON 对象")
    if data.get("version") != RECORD_VERSION:
        raise EvidenceError("指纹格式不兼容，请复核后重新记录；不能只修改 version 字段")
    expected = "PASS" if kind == "plan" else "Ready for Archive"
    if (data.get("version"), data.get("kind"), data.get("change"), data.get("profile"), data.get("decision")) != (
        RECORD_VERSION, kind, change, profile, expected
    ):
        raise EvidenceError("记录类型、路径、等级或结论不匹配")
    return data


def equal(actual: dict[str, str], expected: dict[str, str], description: str) -> None:
    if actual != expected:
        changed = sorted(key for key in actual.keys() | expected.keys() if actual.get(key) != expected.get(key))
        raise EvidenceError(f"{description}已变化：{', '.join(changed[:12])}")


def check_plan(root: Path, change: str, profile: str) -> dict:
    data = load(root, change, "plan", profile)
    if profile == "strict" and not data.get("independent"):
        raise EvidenceError("strict 缺少独立规划评审依据")
    equal(snapshot(root, data["inputs"], data["tasks"]), data["snapshot"], "规划或来源")
    equal(snapshot(root, data["reports"]), data["report_snapshot"], "规划评审报告")
    return data


def check_tasks(root: Path, tasks: str) -> None:
    _, states = task_lines(local(root, tasks).read_bytes())
    if not states or not all(states):
        raise EvidenceError(f"必需任务尚未全部完成或清单为空：{sum(states)}/{len(states)}")


def check_verify(root: Path, change: str, profile: str) -> dict:
    plan = check_plan(root, change, profile)
    data = load(root, change, "verify", profile)
    if profile == "strict" and not data.get("independent"):
        raise EvidenceError("strict 缺少独立代码质量评审依据")
    check_tasks(root, plan["tasks"])
    if digest(record_path(root, change, "plan").read_bytes()) != data["plan_record_sha256"]:
        raise EvidenceError("规划评审记录已变化，需要重新核对验收")
    equal(snapshot(root, data["inputs"]), data["snapshot"], "实现、任务或验收证据")
    return data


def write_record(root: Path, change: str, kind: str, data: dict) -> Path:
    path = record_path(root, change, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    data.update(version=RECORD_VERSION, kind=kind, change=change, recorded_at=datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def record(args: argparse.Namespace, root: Path, change: str) -> Path:
    independent = require_report(root, args.independent) if args.independent else None
    if args.profile == "strict" and not independent:
        raise EvidenceError("strict 记录要求 --independent 指向真实独立评审报告")
    report = require_report(root, args.report)
    common = {"profile": args.profile, "independent": independent}
    if args.command == "record-plan":
        tasks = label(root, args.tasks)
        _, states = task_lines(local(root, tasks).read_bytes())
        if not states:
            raise EvidenceError("机器核验需要非空 Markdown checkbox 任务清单；其他格式按共享规则人工核验")
        metadata = label(root, str(Path(change) / ".openspec.yaml"))
        inputs = sorted({label(root, item) for item in args.plan + args.source} | {tasks, metadata})
        reports = sorted({report} | ({independent} if independent else set()))
        destination = record_path(root, change, "plan")
        # 输出不能成为自己的输入，否则记录后基线会立即失效。
        reject_output_input(root, destination, inputs + reports)
        return write_record(root, change, "plan", dict(
            common, decision="PASS", inputs=inputs, tasks=tasks, reports=reports,
            snapshot=snapshot(root, inputs, tasks), report_snapshot=snapshot(root, reports),
        ))
    plan = check_plan(root, change, args.profile)
    check_tasks(root, plan["tasks"])
    for item in args.evidence:
        require_report(root, item)
    inputs = sorted({label(root, item) for item in args.code + args.evidence} | {report, plan["tasks"]}
                    | ({independent} if independent else set()))
    destination = record_path(root, change, "verify")
    reject_output_input(root, destination, inputs)
    return write_record(root, change, "verify", dict(
        common, decision="Ready for Archive", inputs=inputs, snapshot=snapshot(root, inputs),
        plan_record_sha256=digest(record_path(root, change, "plan").read_bytes()),
    ))


def reject_output_input(root: Path, output: Path, inputs: list[str]) -> None:
    for item in inputs:
        path = local(root, item)
        if output == path or (path.is_dir() and output.is_relative_to(path)):
            raise EvidenceError(f"输入范围包含即将写入的记录，请缩小范围：{item}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("record-plan", "check-plan", "record-verify", "check-verify"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True, help="获准访问的项目根")
        command.add_argument("--change", required=True, help="根内实际变更路径")
        command.add_argument("--profile", required=True, choices=("fast", "standard", "strict"))
        if name.startswith("record"):
            command.add_argument("--report", required=True, help="已经完成的通过报告")
            command.add_argument("--independent", help="真实独立评审依据")
        if name == "record-plan":
            command.add_argument("--tasks", required=True, help="CLI 确定的任务文件")
            command.add_argument("--plan", action="append", required=True, help="规划输入文件或目录，可重复")
            command.add_argument("--source", action="append", default=[], help="已登记来源或约束，可重复")
        if name == "record-verify":
            command.add_argument("--code", action="append", required=True, help="相关实现、测试或配置，可重复")
            command.add_argument("--evidence", action="append", required=True, help="非空原始证据文件，可重复")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        root = Path(args.root).resolve(strict=True)
        change = label(root, args.change)
        if args.command.startswith("record"):
            path = record(args, root, change)
            output = {"valid": True, "record": path.relative_to(root).as_posix(), "说明": "仅记录当前文件基线，不证明测试或评审语义。"}
        else:
            check = check_plan if args.command == "check-plan" else check_verify
            check(root, change, args.profile)
            output = {"valid": True, "change": change, "profile": args.profile}
        print(json.dumps(output, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"valid": False, "原因": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
