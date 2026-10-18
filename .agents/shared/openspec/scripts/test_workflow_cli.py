"""用真实 CLI 验证隔离流程；样例报告仅供机器路径测试，不代表语义评审。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import evidence


ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = Path(__file__).resolve().parent
TASKS = "## 1. 实施\n\n- [ ] 1.1 实现所需调整\n- [ ] 1.2 验证既有行为及调整结果\n"
FAST_PROPOSAL = """# Change: 修正文案错字

## Why
隔离样例的文案存在错字，需要恢复已有约定。

## What Changes
- 仅修正文案，保持接口与行为。

## 非目标
不新增业务能力或规范约定。

## 风险判定
Profile: fast；仅低风险文案修复。

## 验收标准
文案正确，其他内容及原有行为保持。

## Source Inputs
| ID | 位置 | 类型／确认状态 | 采纳范围 | 替代关系 |
| --- | --- | --- | --- | --- |
| U1 | 本测试用例 | 测试样例 | 机器状态检查 | 无 |
"""
PROPOSAL = """# Change: 任务列表调整

## Why
测试隔离项目中规划状态和机器核验的衔接。

## What Changes
- 完成一个有明确验收条件的局部调整。

## Capabilities
### New Capabilities
- `listing`: 返回可验证的任务列表结果。
### Modified Capabilities
无。

## Impact
仅隔离测试项目。

## Source Inputs
| ID | 位置 | 类型／确认状态 | 采纳范围 | 替代关系 |
| --- | --- | --- | --- | --- |
| U1 | 本测试用例 | 测试样例 | 机器状态检查 | 无 |
"""
DELTA = """## ADDED Requirements

### Requirement: 返回任务列表
系统 SHALL 返回符合当前筛选条件的任务列表。

#### Scenario: 没有匹配任务
- **WHEN** 当前筛选条件没有匹配任务
- **THEN** 返回有效的空列表
"""
MAIN_SPEC = """# Listing Specification

## Purpose
定义隔离测试项目的列表能力，用于验证规划产物、实现证据和正式规范同步之间的衔接。
这些要求只属于临时样例，不代表模板新增业务能力，也不能作为其他项目已经完成实现验收的证明。

## Requirements

""" + DELTA.split("## ADDED Requirements\n\n", 1)[1]


@unittest.skipUnless(shutil.which("openspec"), "未安装 OpenSpec CLI，未执行集成验证")
class WorkflowCliTests(unittest.TestCase):
    def setUp(self):
        validation = ROOT / ".codex/validation"
        validation.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=validation)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(ROOT / "openspec/schemas", self.root / "openspec/schemas")
        shutil.copy2(ROOT / "openspec/config.yaml", self.root / "openspec/config.yaml")
        (self.root / "openspec/specs").mkdir()
        self.log = validation / "logs/cli" / (self._testMethodName + ".jsonl")
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.log.write_text("", encoding="utf-8")
        self.run_command(["openspec", "--version"])

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def run_command(self, argv, expected=0):
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, timeout=60,
            env=dict(os.environ, OPENSPEC_TELEMETRY="0", DO_NOT_TRACK="1", PYTHONDONTWRITEBYTECODE="1"))
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"argv": argv, "cwd": str(self.root), "started_at": started,
                "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
                ensure_ascii=False) + "\n")
        if expected is not None:
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def cli(self, *arguments, expected=0):
        return self.run_command(["openspec", *arguments], expected)

    def status(self):
        return json.loads(self.cli("status", "--change", self.name, "--json").stdout)

    def new(self, profile="fast", skip_specs=True):
        self.name = "sample-" + profile
        self.profile = profile
        self.change = "openspec/changes/" + self.name
        schema = "fast-change" if profile == "fast" else "spec-driven"
        self.cli("new", "change", self.name, "--schema", schema)
        metadata = self.root / self.change / ".openspec.yaml"
        # CLI 可自动生成 skip_specs；测试显式控制该字段，不能追加重复键。
        text = "\n".join(line for line in metadata.read_text(encoding="utf-8").splitlines()
                         if not line.startswith("skip_specs:")) + "\n"
        text += f"x-workflow_profile: {profile}\nx-trial: true\n"
        if profile == "fast" and skip_specs:
            text += "skip_specs: true\n"
        metadata.write_text(text, encoding="utf-8")

    def planning(self, complete=False):
        self.put(f"{self.change}/proposal.md", FAST_PROPOSAL if self.profile == "fast" else PROPOSAL)
        self.put(f"{self.change}/tasks.md", TASKS.replace("[ ]", "[x]") if complete else TASKS)
        if self.profile != "fast":
            self.put(f"{self.change}/design.md", "## Context\n隔离验证。\n\n## Decisions\n使用既有列表接口。\n")
            self.put(f"{self.change}/specs/listing/spec.md", DELTA)
            self.put(f"{self.change}/sources/user-request.md", "U1：机器路径测试输入，不是实际业务需求。\n")

    def records(self):
        """建立显式标注为测试样例的基线；不据此声称独立语义评审完成。"""
        self.put("src/example.txt", "隔离实现输入\n")
        self.put("tests/check.txt", "隔离验证输入\n")
        self.put(".codex/result.txt", "机器路径测试证据样例\n")
        report = f"{self.change}/reviews/change-review.md"
        self.put(report, "机器路径测试用报告；不构成真实规划或独立评审。\n")
        plan_files = [f"{self.change}/proposal.md"]
        sources = ["openspec/specs"]
        if self.profile != "fast":
            plan_files.extend([f"{self.change}/design.md", f"{self.change}/specs"])
            sources.append(f"{self.change}/sources")
        evidence.record(SimpleNamespace(command="record-plan", profile=self.profile,
            independent=report if self.profile == "strict" else None, report=report,
            tasks=f"{self.change}/tasks.md", plan=plan_files, source=sources, reference=["src", "tests"]),
            self.root, self.change)
        evidence.start_apply(self.root, self.change, self.profile)
        self.put(f"{self.change}/tasks.md", TASKS.replace("[ ]", "[x]"))
        self.put(f"{self.change}/reports/verification.md", "机器路径测试用验收报告。\n")
        code_review = f"{self.change}/reviews/implementation-review.md"
        if self.profile == "strict":
            self.put(code_review, "仅测试独立报告参数的绑定，不构成真实独立代码评审。\n")
        proofs = [".codex/result.txt"]
        if self.profile != "fast":
            manifest = {"requirements": [{"id": "返回任务列表／1.1／1.2", "implementation": ["src/example.txt"],
                "tests": ["tests/check.txt"], "evidence": [".codex/result.txt"], "status": "verified"}],
                "commands": [{"command": "机器路径测试样例", "cwd": ".", "exit_code": 0,
                              "evidence": ".codex/result.txt"}]}
            path = f"{self.change}/reports/verification-manifest.json"
            self.put(path, json.dumps(manifest, ensure_ascii=False))
            proofs.append(path)
        evidence.record(SimpleNamespace(command="record-verify", profile=self.profile,
            independent=code_review if self.profile == "strict" else None,
            report=f"{self.change}/reports/verification.md", code=["src", "tests"], evidence=proofs),
            self.root, self.change)

    def checkpoint(self, action, change=None, extra=None, expected=0):
        result = self.run_command([sys.executable, "-B", str(SCRIPTS / "archive_checkpoint.py"), action,
            "--root", str(self.root), "--change", change or self.change, *(extra or [])], expected)
        return json.loads(result.stdout)

    def test_fast_dependencies_and_planning_completion(self):
        self.new()
        initial = self.status()
        self.assertEqual(initial["schemaName"], "fast-change")
        self.assertEqual(initial["applyRequires"], ["tasks"])
        artifacts = {item["id"]: item for item in initial["artifacts"]}
        self.assertEqual(set(artifacts), {"proposal", "tasks"})
        self.assertEqual(artifacts["tasks"]["requires"], ["proposal"])
        self.assertFalse((self.root / self.change / "proposal.md").exists())
        self.put(f"{self.change}/proposal.md", FAST_PROPOSAL)
        self.assertEqual({a["id"]: a["status"] for a in self.status()["artifacts"]}["tasks"], "ready")
        self.put(f"{self.change}/tasks.md", TASKS)
        self.assertTrue(self.status()["isPlanningComplete"])
        self.assertEqual(evidence.task_lines((self.root / self.change / "tasks.md").read_bytes())[1], [False, False])
        self.cli("validate", self.name, "--strict", "--no-interactive")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_tasks(self.root, f"{self.change}/tasks.md")

    def test_fast_without_skip_specs_fails_then_passes_with_declaration(self):
        self.new(skip_specs=False)
        self.planning()
        result = self.cli("validate", self.name, "--strict", "--no-interactive", expected=None)
        self.assertNotEqual(result.returncode, 0)
        metadata = self.root / self.change / ".openspec.yaml"
        metadata.write_text(metadata.read_text(encoding="utf-8") + "skip_specs: true\n", encoding="utf-8")
        self.cli("validate", self.name, "--strict", "--no-interactive")

    def test_standard_and_strict_keep_all_planning_dependencies(self):
        for profile in ("standard", "strict"):
            with self.subTest(profile=profile):
                self.new(profile)
                self.put(f"{self.change}/proposal.md", PROPOSAL)
                state = self.status()
                self.assertEqual(state["schemaName"], "spec-driven")
                artifacts = {item["id"]: item for item in state["artifacts"]}
                self.assertEqual(set(artifacts), {"proposal", "specs", "design", "tasks"})
                self.assertEqual(set(artifacts["tasks"]["requires"]), {"specs", "design"})
                self.assertFalse(state["isPlanningComplete"])
                self.planning()
                self.assertTrue(self.status()["isPlanningComplete"])
                self.cli("validate", self.name, "--strict", "--no-interactive")

    def test_risk_upgrade_preserves_tasks_and_invalidates_old_baseline(self):
        self.new()
        self.planning()
        self.records()
        tasks = (self.root / self.change / "tasks.md").read_bytes()
        record = evidence.record_path(self.root, self.change, "plan")
        original = record.read_bytes()
        metadata = self.root / self.change / ".openspec.yaml"
        metadata.write_text(metadata.read_text(encoding="utf-8").replace("schema: fast-change", "schema: spec-driven")
            .replace("x-workflow_profile: fast", "x-workflow_profile: standard").replace("skip_specs: true\n", ""), encoding="utf-8")
        state = self.status()
        self.assertEqual(state["schemaName"], "spec-driven")
        self.assertFalse(state["isPlanningComplete"])
        self.assertEqual((self.root / self.change / "tasks.md").read_bytes(), tasks)
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "fast")
        self.assertEqual(record.read_bytes(), original)

    def test_fast_archive_requires_no_spec_or_sync_checkpoint(self):
        self.new()
        self.planning()
        self.records()
        evidence.check_verify(self.root, self.change, "fast")
        self.cli("validate", self.name, "--strict", "--no-interactive")
        records = {kind: evidence.record_path(self.root, self.change, kind).read_bytes() for kind in ("plan", "verify")}
        archive = "openspec/changes/archive/2026-10-18-" + self.name
        (self.root / archive).parent.mkdir(parents=True, exist_ok=True)
        (self.root / self.change).rename(self.root / archive)
        self.cli("validate", "--archived", "--strict", "--no-interactive")
        listing = json.loads(self.cli("list", "--json").stdout)
        self.assertFalse(any(item["name"] == self.name for item in listing["changes"]))
        self.assertFalse((self.root / self.change).exists())
        self.assertFalse((self.root / archive / "specs").exists())
        self.assertFalse((self.root / archive / "reports/archive-checkpoint").exists())
        for kind, original in records.items():
            self.assertEqual(evidence.record_path(self.root, archive, kind).read_bytes(), original)

    def test_strict_sync_and_moved_archive_recovery_use_real_cli(self):
        self.new("strict")
        self.planning()
        self.records()
        self.cli("validate", self.name, "--strict", "--no-interactive")
        records = {kind: evidence.record_path(self.root, self.change, kind).read_bytes() for kind in ("plan", "verify")}
        archive = "openspec/changes/archive/2026-10-18-" + self.name
        self.put(".codex/sync/listing.md", MAIN_SPEC)
        self.put(".codex/sync/plan.json", json.dumps({"targets": [
            {"path": "openspec/specs/listing/spec.md", "after": ".codex/sync/listing.md"}]}))
        prepared = self.checkpoint("prepare", extra=["--profile", "strict", "--mode", "machine", "--archive", archive,
                                                   "--sync-plan", ".codex/sync/plan.json"])
        self.assertEqual(prepared["stage"], "prepared")
        self.assertEqual(self.checkpoint("check")["pending_targets"], ["openspec/specs/listing/spec.md"])
        self.put("openspec/specs/listing/spec.md", MAIN_SPEC)
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "strict")
        self.assertEqual(self.checkpoint("check")["pending_targets"], [])
        self.assertEqual(self.checkpoint("synced")["stage"], "synced")
        self.checkpoint("check")
        (self.root / archive).parent.mkdir(parents=True, exist_ok=True)
        (self.root / self.change).rename(self.root / archive)
        self.assertEqual(self.checkpoint("check", archive)["stage"], "synced")
        self.assertEqual(self.checkpoint("archived", archive)["stage"], "archived")
        self.assertFalse((self.root / self.change).exists())
        for kind, original in records.items():
            self.assertEqual(evidence.record_path(self.root, archive, kind).read_bytes(), original)
        # 模拟已移动后归档报告丢失，必须重跑真实 CLI 才能恢复。
        (self.root / archive / "reports/archive-record.md").unlink()
        self.assertFalse(self.checkpoint("check", archive, expected=1)["valid"])
        self.assertTrue(self.checkpoint("archived", archive)["archive_report_current"])
        journal = json.loads((self.root / archive / "reports/archive-checkpoint/journal.json").read_text(encoding="utf-8"))
        self.assertTrue(journal["last_attempt"]["complete"])
        self.assertTrue(all(item["exit_code"] == 0 for item in journal["commands"]))
        self.assertNotIn(self.name, [item["name"] for item in json.loads(journal["commands"][-1]["stdout"])["changes"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
