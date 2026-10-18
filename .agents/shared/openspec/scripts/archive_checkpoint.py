#!/usr/bin/env python3
"""核验机器归档检查点并运行只读 OpenSpec 校验；不执行规范写入或目录移动。"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import archive_links
import evidence
import evidence_manifest

VERSION = 1
CHECKPOINT = "reports/archive-checkpoint"
ARCHIVE_REPORT = "reports/archive-record.md"


class CheckpointError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encoded(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".checkpoint-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def within(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent + "/")


def mapped(path: str, active: str, current: str) -> str:
    return current + path[len(active):] if within(path, active) else path


def journal_path(root: Path, change: str) -> Path:
    return evidence.local(root, f"{change}/{CHECKPOINT}/journal.json")


def scopes_snapshot(root: Path, inputs: list[str], active: str, current: str) -> dict:
    """使用原证据快照语义，映射历史路径，仅排除工具自己的归档输出。"""
    result = {}
    managed = (f"{current}/{CHECKPOINT}", f"{current}/{ARCHIVE_REPORT}")
    for name in inputs:
        actual = mapped(name, active, current)
        path = evidence.local(root, actual)
        if not path.exists():
            result[name] = "missing"
            continue
        snapshot = evidence.snapshot(root, [actual])
        for key, value in snapshot.items():
            if any(within(key.rstrip("/"), item) for item in managed):
                continue
            result[mapped(key.rstrip("/"), current, active)] = value
    return dict(sorted(result.items()))


def file_image(root: Path, name: str) -> dict:
    path = evidence.local(root, name)
    if not path.exists():
        return {"fingerprint": "missing", "content_base64": None}
    if not path.is_file():
        raise CheckpointError(f"归档目标或预期内容必须是普通文件：{name}")
    content = path.read_bytes()
    executable = path.stat().st_mode & 0o111
    return content_image(content, executable)


def content_image(content: bytes, executable: int) -> dict:
    content.decode("utf-8")
    return {"fingerprint": f"file:exec={executable:03o}:sha256={evidence.digest(content)}",
            "content_base64": base64.b64encode(content).decode("ascii")}


def targets_from_plan(root: Path, sync_plan: str, spec_root: str) -> dict:
    payload = json.loads(evidence.local(root, sync_plan).read_text(encoding="utf-8"))
    entries = payload.get("targets")
    if not isinstance(entries, list) or not entries:
        raise CheckpointError("同步计划 targets 必须是非空数组")
    targets = {}
    for entry in entries:
        path = evidence.label(root, entry["path"])
        if path == spec_root or not within(path, spec_root) or path in targets:
            raise CheckpointError(f"目标重复或不属于正式规范根：{path}")
        if "after" not in entry:
            raise CheckpointError(f"目标缺少 after，删除必须显式使用 null：{path}")
        before = file_image(root, path)
        after = ({"fingerprint": "missing", "content_base64": None} if entry["after"] is None
                 else file_image(root, evidence.label(root, entry["after"])))
        if entry["after"] is not None and after["fingerprint"] == "missing":
            raise CheckpointError(f"预期内容文件不存在：{entry['after']}")
        if before == after:
            raise CheckpointError(f"同步目标没有内容或可执行位变化：{path}")
        targets[path] = {"before": before, "expected": after}
    return targets


def referenced_inputs(root: Path, change: str, profile: str) -> tuple[list[str], dict]:
    verify = evidence.check_verify(root, change, profile)
    plan = evidence.check_plan(root, change, profile)
    records = [evidence.record_path(root, change, kind) for kind in ("plan", "verify")]
    inputs = set(plan["inputs"] + plan["reports"] + verify["inputs"] + [change])
    hashes = {path.relative_to(root).as_posix(): evidence.digest(path.read_bytes()) for path in records}
    inputs.update(hashes)
    manifest = f"{change}/reports/verification-manifest.json"
    if evidence.local(root, manifest).exists():
        evidence_manifest.check(root, manifest)
        inputs.add(manifest)
        data = json.loads(evidence.local(root, manifest).read_text(encoding="utf-8"))
        for item in data["requirements"]:
            for key in ("implementation", "tests", "evidence"):
                inputs.update(evidence.label(root, name) for name in item[key])
        inputs.update(evidence.label(root, item["evidence"]) for item in data["commands"])
    elif profile != "fast":
        raise CheckpointError("standard/strict 归档缺少结构化验收清单")
    return sorted(inputs), hashes


def protected_navigation(root: Path, change: str, active: str) -> set[str]:
    """评审、验收、原始证据保留原字节；普通规划/来源/实现文档允许精确导航更新。"""
    plan = json.loads(evidence.record_path(root, change, "plan").read_text(encoding="utf-8"))
    verify = json.loads(evidence.record_path(root, change, "verify").read_text(encoding="utf-8"))
    protected = set(plan["reports"]) | (set(verify["inputs"]) - set(verify["code_inputs"]) - {plan["tasks"]})
    protected.update((f"{active}/reviews", f"{active}/reports", ".codex"))
    manifest = evidence.local(root, f"{change}/reports/verification-manifest.json")
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for item in data["requirements"]:
            protected.update(item["evidence"])
        protected.update(item["evidence"] for item in data["commands"])
    return protected


def navigation_plan(root: Path, change: str, archive: str, files: list[str]) -> dict:
    names = {name for name in evidence.snapshot(root, [change])
             if name.lower().endswith(".md") and not within(name, f"{change}/{CHECKPOINT}")
             and name != f"{change}/{ARCHIVE_REPORT}"}
    if evidence.local(root, "README.md").exists():
        names.add("README.md")
    names.update(evidence.label(root, name) for name in files)
    protected = protected_navigation(root, change, change)
    navigation = {"files": sorted(names), "targets": {}, "references": [], "preserved_links": []}
    for name in sorted(names):
        path = evidence.local(root, name)
        if not name.lower().endswith(".md") or not path.is_file():
            raise CheckpointError(f"导航输入必须是普通 Markdown 文件：{name}")
        if within(name, Path(change).parent.as_posix() + "/archive"):
            raise CheckpointError(f"不能借本次归档改写已有历史归档：{name}")
        before = file_image(root, name)
        original = base64.b64decode(before["content_base64"]).decode("utf-8")
        try:
            updated, references = archive_links.rewrite(original, name, change, archive)
        except archive_links.LinkError as error:
            raise CheckpointError(f"{name}：{error}") from error
        navigation["references"].extend(references)
        if updated == original:
            continue
        if any(within(name, parent) for parent in protected):
            navigation["preserved_links"].extend(item for item in references
                                                if item["destination"] != item["updated_destination"])
        else:
            navigation["targets"][name] = {"before": before,
                "expected": content_image(updated.encode("utf-8"), path.stat().st_mode & 0o111)}
    return navigation


def all_targets(data: dict) -> dict:
    return {**data["targets"], **data.get("navigation", {}).get("targets", {})}


def check_link_targets(root: Path, change: str, data: dict, require_synced: bool = False) -> None:
    for item in data.get("navigation", {}).get("references", []):
        target = item["target"]
        planned = data["targets"].get(target)
        if planned and planned["expected"]["fingerprint"] == "missing":
            raise CheckpointError(f"链接指向待删除的规范：{item['source']}:{item['line']} -> {target}")
        path = evidence.local(root, mapped(target, data["active_change_path"], change))
        if not path.exists() and (not planned or require_synced):
            raise CheckpointError(f"本地链接目标不存在：{item['source']}:{item['line']} -> {target}")
        if path.exists() and not (path.is_file() or path.is_dir()):
            raise CheckpointError(f"链接目标不是普通文件或目录：{target}")


def prepare(root: Path, change: str, args: argparse.Namespace) -> dict:
    if not args.archive or not args.profile:
        raise CheckpointError("prepare 必须提供 --archive 和 --profile；有规范同步时提供 --sync-plan")
    if args.mode != "machine":
        raise CheckpointError("此工具只处理 machine；manual 按共享规则保留人工核验记录")
    archive = evidence.label(root, args.archive)
    spec_root = evidence.label(root, args.spec_root)
    if change == "." or archive == "." or spec_root == ".":
        raise CheckpointError("变更、归档和规范根不能是项目根")
    if any(within(a, b) or within(b, a) for a, b in
           ((change, archive), (change, spec_root), (archive, spec_root))):
        raise CheckpointError("活动变更、归档目标和规范根不能重叠")
    if not evidence.local(root, change).is_dir():
        raise CheckpointError("活动变更目录不存在")
    if evidence.local(root, archive).exists():
        raise CheckpointError("归档目标已存在，不能覆盖")
    if evidence.local(root, f"{change}/{CHECKPOINT}").exists():
        raise CheckpointError("检查点目录已存在，不能覆盖；应核对现有记录或说明中断")
    if evidence.local(root, f"{change}/{ARCHIVE_REPORT}").exists():
        raise CheckpointError("已有归档报告，不能覆盖；请先核对其历史状态")
    targets = targets_from_plan(root, args.sync_plan, spec_root) if args.sync_plan else {}
    if not targets and any(name.endswith("/spec.md") for name in evidence.snapshot(root, [change])
                           if within(name, f"{change}/specs")):
        raise CheckpointError("实际包含规格增量，不能省略 --sync-plan 只更新导航")
    inputs, hashes = referenced_inputs(root, change, args.profile)
    navigation = navigation_plan(root, change, archive, getattr(args, "link_file", []))
    if not targets and not navigation["targets"] and not navigation["preserved_links"]:
        raise CheckpointError("无规范同步或导航变化，无需创建空检查点；按无同步路径归档")
    if set(targets) & set(navigation["targets"]):
        raise CheckpointError("同一文件不能同时是规范同步和导航目标；请在规范合并内容中处理链接")
    inputs = sorted(set(inputs + [spec_root] + navigation["files"]))
    for name in inputs:
        if name == "." or (name != change and within(change, name)) or within(archive, name):
            raise CheckpointError(f"输入包含归档父目录，请缩小证据范围后重新核验：{name}")
    data = {
        "version": VERSION, "stage": "prepared", "profile": args.profile,
        "verification_mode": "machine", "active_change_path": change,
        "archived_change_path": archive, "spec_root": spec_root,
        "prepared_at": now(), "targets": targets, "inputs": inputs,
        "navigation": navigation,
        "records_sha256": hashes, "baseline": scopes_snapshot(root, inputs, change, change),
        "verification_before_archive": {"valid": True, "method": "evidence.check_verify"},
        "commands": [],
    }
    check_link_targets(root, change, data)
    atomic_write(journal_path(root, change), encoded(data))
    return data


def load(root: Path, change: str) -> dict:
    data = json.loads(journal_path(root, change).read_text(encoding="utf-8"))
    if data.get("version") != VERSION:
        raise CheckpointError("检查点格式不受支持，停止读取")
    if data.get("stage") not in ("prepared", "synced", "archived"):
        raise CheckpointError("未知检查点阶段")
    active, archive = data["active_change_path"], data["archived_change_path"]
    if change not in (active, archive):
        raise CheckpointError("检查点变更路径不匹配")
    for name in [active, archive, data["spec_root"], *data["inputs"], *data["targets"],
                 *data["records_sha256"]]:
        if evidence.label(root, name) != name:
            raise CheckpointError(f"检查点路径不是规范项目相对路径：{name}")
    if data.get("verification_mode") != "machine" or not data["records_sha256"]:
        raise CheckpointError("检查点缺少原机器验收依据")
    if (not data["targets"] and not data.get("navigation", {}).get("targets")
            and not data.get("navigation", {}).get("preserved_links")) or not data["inputs"] or not data["baseline"]:
        raise CheckpointError("检查点输入不完整")
    for name, images in all_targets(data).items():
        if evidence.label(root, name) != name:
            raise CheckpointError(f"归档目标不是规范项目相对路径：{name}")
        if name in data["targets"] and (name == data["spec_root"] or not within(name, data["spec_root"])):
            raise CheckpointError("同步目标超出规范根")
        for image in (images["before"], images["expected"]):
            if image["fingerprint"] == "missing":
                if image["content_base64"] is not None:
                    raise CheckpointError("缺失目标不应有内容副本")
            else:
                content = base64.b64decode(image["content_base64"], validate=True)
                content.decode("utf-8")
                if image["fingerprint"].split(":sha256=")[-1] != evidence.digest(content):
                    raise CheckpointError("检查点内容副本与哈希不一致")
    if "navigation" in data:
        check_navigation_plan(root, change, data)
    return data


def check_navigation_plan(root: Path, change: str, data: dict) -> None:
    navigation = data["navigation"]
    active, archive = data["active_change_path"], data["archived_change_path"]
    protected = protected_navigation(root, change, active)
    if set(data["targets"]) & set(navigation["targets"]):
        raise CheckpointError("规范与导航目标重叠")
    references, preserved = [], []
    if (navigation["files"] != sorted(set(navigation["files"]))
            or not set(navigation["files"]).issubset(data["inputs"])
            or not set(navigation["targets"]).issubset(navigation["files"])):
        raise CheckpointError("导航范围与检查点输入不匹配")
    for name in navigation["files"]:
        if evidence.label(root, name) != name or not name.lower().endswith(".md"):
            raise CheckpointError("导航范围必须是规范的 Markdown 文件路径")
        images = navigation["targets"].get(name)
        readonly = any(within(name, parent) for parent in protected)
        if images:
            if readonly or images["before"]["fingerprint"] != data["baseline"].get(name):
                raise CheckpointError(f"导航不能修改历史证据或脱离原基线：{name}")
            before = base64.b64decode(images["before"]["content_base64"]).decode("utf-8")
        else:
            before = evidence.local(root, mapped(name, active, change)).read_text(encoding="utf-8")
        after, refs = archive_links.rewrite(before, name, active, archive)
        references.extend(refs)
        if images:
            executable = int(images["before"]["fingerprint"].split(":")[1].split("=")[1], 8)
            if images["expected"] != content_image(after.encode("utf-8"), executable) or before == after:
                raise CheckpointError(f"导航目标包含链接地址以外的变化：{name}")
        if readonly:
            preserved.extend(item for item in refs if item["destination"] != item["updated_destination"])
        elif before != after and not images:
            raise CheckpointError(f"导航遗漏必要的地址更新：{name}")
    if references != navigation["references"] or preserved != navigation["preserved_links"]:
        raise CheckpointError("导航引用与原文件内容不一致")


def check_locations(root: Path, change: str, data: dict) -> None:
    active, archive = data["active_change_path"], data["archived_change_path"]
    if not evidence.local(root, change).is_dir():
        raise CheckpointError("当前变更目录不存在")
    if change == active:
        if data["stage"] == "archived" or evidence.local(root, archive).exists():
            raise CheckpointError("归档目标已存在或阶段与活动路径不匹配")
    elif evidence.local(root, active).exists() or data["stage"] == "prepared":
        raise CheckpointError("活动与归档目录同时存在，或未完成同步就移动了目录")


def target_ancestors(targets: dict) -> set[str]:
    return {parent.as_posix() for name in targets for parent in Path(name).parents
            if parent.as_posix() != "."}


def check_baseline(root: Path, change: str, data: dict, require_synced: bool = False) -> list[str]:
    check_locations(root, change, data)
    active = data["active_change_path"]
    for name, digest in data["records_sha256"].items():
        path = evidence.local(root, mapped(name, active, change))
        if not path.is_file() or evidence.digest(path.read_bytes()) != digest:
            raise CheckpointError(f"原规划或验收记录已变化：{name}")
    pending = []
    targets = all_targets(data)
    for name, images in targets.items():
        actual = file_image(root, mapped(name, active, change))
        if actual == images["expected"]:
            continue
        if data["stage"] == "prepared" and not require_synced and actual == images["before"]:
            pending.append(name)
        else:
            raise CheckpointError(f"归档目标不符合预登记状态：{name}")
    actual = scopes_snapshot(root, data["inputs"], active, change)
    baseline = data["baseline"]
    ancestors = target_ancestors(targets)
    differences = []
    for name in actual.keys() | baseline.keys():
        if name in targets or actual.get(name) == baseline.get(name):
            continue
        # 允许新增目标所需的目录出现；不允许删除旧目录或在目录中加入其他文件。
        if (name in ancestors and baseline.get(name, "missing") == "missing"
                and actual.get(name) == "directory"):
            continue
        differences.append(name)
    if differences:
        raise CheckpointError(f"非同步输入已变化：{', '.join(sorted(differences)[:12])}")
    check_link_targets(root, change, data, require_synced)
    return sorted(pending)


def run_cli(root: Path, change: str, data: dict, arguments: list[str]) -> dict:
    argv = ["openspec", *arguments]
    record = {"argv": argv, "cwd": ".", "started_at": now()}
    env = dict(os.environ, OPENSPEC_TELEMETRY="0", DO_NOT_TRACK="1")
    try:
        result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=60)
        record.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
    except (OSError, subprocess.TimeoutExpired) as error:
        record.update(exit_code=None, stdout="", stderr=str(error))
    record["finished_at"] = now()
    data["commands"].append(record)
    atomic_write(journal_path(root, change), encoded(data))
    if record["exit_code"] != 0:
        raise CheckpointError(f"实际校验失败，阶段未推进，输出保存在检查点：{' '.join(argv)}")
    return record


def validate_root(root: Path, change: str, data: dict) -> None:
    record = run_cli(root, change, data, ["context", "--json"])
    resolved = json.loads(record["stdout"])["root"]["path"]
    if Path(resolved).resolve() != root:
        raise CheckpointError("OpenSpec CLI 解析到了其他根，停止校验")


def navigation_report(data: dict) -> str:
    navigation = data.get("navigation")
    if navigation is None:
        return ""  # 保持旧 v1 检查点对应报告的字节格式。
    current = data["archived_change_path"] if data["stage"] == "archived" else data["active_change_path"]
    report_parent = f"{current}/reports"

    def link(name: str) -> str:
        actual = mapped(name, data["active_change_path"], current)
        destination = quote(os.path.relpath(actual, report_parent).replace(os.sep, "/"), safe="/.-_~")
        label = name.replace("[", "\\[").replace("]", "\\]").replace("|", "\\|")
        return f"[{label}]({destination})"

    result = ("\n## 归档导航\n\n"
              f"已检查 {len(navigation['files'])} 份 Markdown 的相对文件链接，"
              f"预登记 {len(navigation['targets'])} 份文档的地址更新。"
              "范围、原文、预期内容及目标映射见检查点 navigation；仅更改必要链接地址。\n\n"
              "检查不覆盖远程 URL、站点绝对路径及章节锚点是否存在；代码中的路径保留原意。\n")
    if navigation["targets"]:
        result += "\n已登记导航文档：\n\n" + "\n".join(f"- {link(name)}" for name in navigation["targets"]) + "\n"
    if navigation["preserved_links"]:
        result += ("\n以下原评审、验收或证据文件保留原字节，其中的历史相对链接未直接改写；"
                   "请从下表访问目标，不能宣称这些原文件中的链接已修复。\n\n"
                   "| 原文件与行号 | 当前可访问目标 |\n| --- | --- |\n")
        for item in navigation["preserved_links"]:
            result += f"| {link(item['source'])}:{item['line']} | {link(item['target'])} |\n"
    return result


def archive_report(data: dict) -> str:
    complete = data["stage"] == "archived"
    records = "\n".join(f"- `{name}`：`{digest}`" for name, digest in data["records_sha256"].items())
    return (
        "# OpenSpec 归档记录\n\n"
        f"- 状态：`{data['stage']}`（{'归档完成' if complete else '同步完成，尚未确认移动'}）\n"
        f"- 风险等级：`{data['profile']}`\n- 核验方式：`machine`\n"
        f"- active_change_path：`{data['active_change_path']}`\n"
        f"- archived_change_path：`{data['archived_change_path']}`\n"
        f"- 检查点：`archive-checkpoint/journal.json`\n\n"
        "## 原验收依据\n\n"
        "以下路径保留归档前含义；归档后读取时仅将活动路径前缀映射为归档路径，原记录不重写。\n\n"
        f"{records}\n\n"
        "## 核验结果\n\n"
        "已复核原记录哈希、原记录覆盖的输入、变更文件和预登记规范内容。"
        "实际命令、工作目录、退出码、时间及输出见检查点 commands。\n\n"
        + (("归档后已确认活动目录不存在、归档目录存在、正式规范及归档校验通过，" if data["targets"] else
            "归档后已确认活动目录不存在、归档目录存在、归档校验通过，") +
           "且 openspec list 不再包含该活动变更。\n" if complete else
           ("正式规范" if data["targets"] else "活动变更") +
           "校验通过；移动前须再次 check，移动后运行 archived 完成最终核验。\n")
        + navigation_report(data)
        + "\n归档核验不等于重新执行业务验收，不证明评审语义或独立身份；不执行提交、推送或部署。\n"
    )


def validation_commands(data: dict, action: str) -> list[list[str]]:
    commands = [["context", "--json"]]
    if data["targets"]:
        commands.append(["validate", "--specs", "--strict", "--no-interactive"])
    elif action == "synced":
        commands.append(["validate", Path(data["active_change_path"]).name, "--strict", "--no-interactive"])
    if action == "archived":
        commands += [["validate", "--archived", "--strict", "--no-interactive"], ["list", "--json"]]
    return commands


def check_completed_commands(data: dict) -> None:
    attempt = data.get("last_attempt", {})
    if attempt.get("complete") is False:
        raise CheckpointError("上次实际校验失败或中断，必须重试对应 synced/archived 后才能继续")
    if data["stage"] == "prepared":
        return
    if attempt.get("complete") is not True or attempt.get("action") != data["stage"]:
        raise CheckpointError("完成阶段缺少对应的成功校验记录")
    expected = [["openspec", *arguments] for arguments in validation_commands(data, data["stage"])]
    records = data.get("commands", [])[-len(expected):]
    if len(records) != len(expected):
        raise CheckpointError("完成阶段缺少实际 CLI 命令结果")
    for record, argv in zip(records, expected):
        if (record.get("argv") != argv or record.get("exit_code") != 0
                or record.get("cwd") != "." or not record.get("started_at")
                or not record.get("finished_at") or "stdout" not in record or "stderr" not in record):
            raise CheckpointError("完成阶段的 CLI 命令记录不完整或不成功")
    if data.get("validation") != records[1]:
        raise CheckpointError("归档阶段校验结果与实际命令记录不一致")
    if data["stage"] == "archived" and data.get("post_archive_check") != records[-1]:
        raise CheckpointError("归档后检查结果与实际命令记录不一致")


def finalize(root: Path, change: str, data: dict, action: str) -> dict:
    if action == "synced" and (change != data["active_change_path"] or data["stage"] == "archived"):
        raise CheckpointError("synced 必须在未归档的活动变更上执行")
    if action == "archived" and (change != data["archived_change_path"] or data["stage"] == "prepared"):
        raise CheckpointError("archived 必须在已同步并移动的归档目录上执行")
    check_baseline(root, change, data, require_synced=True)
    data["last_attempt"] = {"action": action, "complete": False, "started_at": now()}
    atomic_write(journal_path(root, change), encoded(data))
    validate_root(root, change, data)
    completed = [run_cli(root, change, data, arguments) for arguments in validation_commands(data, action)[1:]]
    validation = completed[0]
    if action == "archived":
        listing = completed[-1]
        changes = json.loads(listing["stdout"])["changes"]
        if not isinstance(changes, list) or any(item["name"] == Path(data["active_change_path"]).name for item in changes):
            raise CheckpointError("openspec list 仍包含活动变更或返回结构不正确")
        data["post_archive_check"] = listing
    check_baseline(root, change, data, require_synced=True)
    data.update(stage=action, validation=validation, updated_at=now())
    atomic_write(evidence.local(root, f"{change}/{ARCHIVE_REPORT}"), archive_report(data))
    data["last_attempt"]["complete"] = True
    atomic_write(journal_path(root, change), encoded(data))
    # 成功返回包含落盘后的最终核验，调用者无需再补一组同等检查。
    saved = load(root, change)
    if saved != data:
        raise CheckpointError("落盘后的检查点与本次校验记录不一致")
    check_baseline(root, change, saved, require_synced=True)
    check_completed_commands(saved)
    check_report(root, change, saved)
    return saved


def check_report(root: Path, change: str, data: dict) -> bool:
    report = evidence.local(root, f"{change}/{ARCHIVE_REPORT}")
    current = report.is_file() and report.read_text(encoding="utf-8") == archive_report(data)
    if data["stage"] != "prepared" and not current:
        raise CheckpointError("归档报告缺失或状态过期；在当前路径重试 synced 或 archived 以重新核验并补齐")
    return current


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=("links", "prepare", "check", "synced", "archived"))
    result.add_argument("--root", required=True)
    result.add_argument("--change", required=True)
    result.add_argument("--profile", choices=("fast", "standard", "strict"))
    result.add_argument("--mode", default="machine", choices=("machine", "manual"))
    result.add_argument("--archive")
    result.add_argument("--sync-plan", help="预先准备的 JSON 同步计划；targets 中 path 为目标，after 为预期 UTF-8 文件路径或 null")
    result.add_argument("--spec-root", default="openspec/specs", help="CLI 已确认的正式规范根，相对项目根")
    result.add_argument("--link-file", action="append", default=[],
                        help="额外扫描的根内 Markdown 文件，可重复；默认扫描整个变更及根 README.md")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        root = Path(args.root).resolve(strict=True)
        change = evidence.label(root, args.change)
        if args.action == "links":
            if not args.archive:
                raise CheckpointError("links 必须提供 --archive 才能检查移动后的目标")
            archive = evidence.label(root, args.archive)
            navigation = navigation_plan(root, change, archive, args.link_file)
            targets = targets_from_plan(root, args.sync_plan, evidence.label(root, args.spec_root)) if args.sync_plan else {}
            check_link_targets(root, change, {"active_change_path": change, "targets": targets, "navigation": navigation})
            print(encoded({"valid": True, "checked_files": navigation["files"],
                           "pending_navigation_targets": sorted(navigation["targets"]),
                           "preserved_links": navigation["preserved_links"]}), end="")
            return 0
        if args.action == "prepare":
            data = prepare(root, change, args)
            pending = sorted(all_targets(data))
        else:
            data = load(root, change)
            if args.action == "check":
                pending = check_baseline(root, change, data)
                check_completed_commands(data)
            else:
                data = finalize(root, change, data, args.action)
                pending = []
        report_current = check_report(root, change, data)
        print(encoded({"valid": True, "stage": data["stage"], "pending_targets": pending,
                       "archive_report_current": report_current}), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(encoded({"valid": False, "原因": str(error)}), end="")
        return 1


if __name__ == "__main__":
    sys.exit(main())
