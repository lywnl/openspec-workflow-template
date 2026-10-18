"""核对归档同步的中断与失效边界；成功 CLI 路径另由集成测试执行。"""

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import archive_checkpoint as checkpoint
import evidence


class ArchiveCheckpointTests(unittest.TestCase):
    def setUp(self):
        validation = Path(__file__).resolve().parents[4] / ".codex/validation"
        validation.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=validation)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.change = "openspec/changes/example"
        self.archive = "openspec/changes/archive/2026-10-18-example"
        self.tasks = f"{self.change}/tasks.md"
        self.target = "openspec/specs/example/spec.md"
        self.put(f"{self.change}/.openspec.yaml", "schema: spec-driven\nx-workflow_profile: standard\n")
        self.put(f"{self.change}/proposal.md", "文件基线测试用提案\n")
        self.put(self.tasks, "- [ ] 1.1 修改及验证\n")
        self.put(f"{self.change}/reviews/change-review.md", "仅测试记录格式的规划输入\n")
        self.put("src/module.txt", "原实现\n")
        self.put("tests/check.txt", "测试输入\n")
        self.put(".codex/result.txt", "测试证据输入\n")
        self.put(self.target, "原规范\n")
        evidence.record(SimpleNamespace(command="record-plan", profile="standard", independent=None,
            report=f"{self.change}/reviews/change-review.md", tasks=self.tasks,
            plan=[f"{self.change}/proposal.md"], source=["openspec/specs"], reference=["src", "tests"]),
            self.root, self.change)
        evidence.start_apply(self.root, self.change, "standard")
        self.put(self.tasks, "- [x] 1.1 修改及验证\n")
        self.put(f"{self.change}/reports/verification.md", "仅测试记录格式的验收输入\n")
        manifest = {"requirements": [{"id": "1.1", "implementation": ["src/module.txt"],
            "tests": ["tests/check.txt"], "evidence": [".codex/result.txt"], "status": "verified"}],
            "commands": [{"command": "样例命令", "cwd": ".", "exit_code": 0, "evidence": ".codex/result.txt"}]}
        self.put(f"{self.change}/reports/verification-manifest.json", json.dumps(manifest, ensure_ascii=False))
        evidence.record(SimpleNamespace(command="record-verify", profile="standard", independent=None,
            report=f"{self.change}/reports/verification.md", code=["src", "tests"],
            evidence=[".codex/result.txt", f"{self.change}/reports/verification-manifest.json"]), self.root, self.change)
        self.put(".codex/sync/after.md", "预登记的新规范\n")
        self.put(".codex/sync/new.md", "新增规范\n")
        self.put(".codex/sync/plan.json", json.dumps({"targets": [
            {"path": self.target, "after": ".codex/sync/after.md"},
            {"path": "openspec/specs/new/spec.md", "after": ".codex/sync/new.md"}]}))

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def prepare(self):
        return checkpoint.prepare(self.root, self.change, SimpleNamespace(archive=self.archive,
            profile="standard", mode="machine", sync_plan=".codex/sync/plan.json", spec_root="openspec/specs"))

    def apply_expected(self, data, names=None):
        for name in names if names is not None else data["targets"]:
            image = data["targets"][name]["expected"]
            target = self.root / name
            if image["content_base64"] is None:
                target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(base64.b64decode(image["content_base64"]))

    def test_partial_sync_resumes_only_remaining_registered_targets(self):
        data = self.prepare()
        self.apply_expected(data, [self.target])
        current = checkpoint.load(self.root, self.change)
        self.assertEqual(checkpoint.check_baseline(self.root, self.change, current), ["openspec/specs/new/spec.md"])
        self.apply_expected(current, ["openspec/specs/new/spec.md"])
        self.assertEqual(checkpoint.check_baseline(self.root, self.change, current), [])
        self.assertEqual(current["targets"], data["targets"])

    def test_changing_preparation_copy_does_not_redefine_expected(self):
        data = self.prepare()
        self.put(".codex/sync/after.md", "未经预登记的其他内容\n")
        current = checkpoint.load(self.root, self.change)
        self.assertEqual(current["targets"], data["targets"])
        self.apply_expected(current)
        self.assertEqual((self.root / self.target).read_text(encoding="utf-8"), "预登记的新规范\n")
        self.assertEqual(checkpoint.check_baseline(self.root, self.change, current), [])

    def test_extra_source_or_evidence_change_blocks_resume(self):
        data = self.prepare()
        for name in ("src/module.txt", ".codex/result.txt", f"{self.change}/reviews/change-review.md"):
            original = (self.root / name).read_bytes()
            with self.subTest(path=name):
                self.put(name, "额外修改\n")
                with self.assertRaisesRegex(checkpoint.CheckpointError, "非同步输入"):
                    checkpoint.check_baseline(self.root, self.change, data)
            (self.root / name).write_bytes(original)

    def test_new_unregistered_spec_blocks_resume(self):
        data = self.prepare()
        self.put("openspec/specs/extra/spec.md", "未登记规范\n")
        with self.assertRaisesRegex(checkpoint.CheckpointError, "非同步输入"):
            checkpoint.check_baseline(self.root, self.change, data)

    def test_changed_original_record_blocks_resume(self):
        data = self.prepare()
        path = evidence.record_path(self.root, self.change, "verify")
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(checkpoint.CheckpointError, "原规划或验收记录"):
            checkpoint.check_baseline(self.root, self.change, data)

    def test_unregistered_target_content_is_rejected(self):
        data = self.prepare()
        self.put(self.target, "既非旧版也非登记新版\n")
        with self.assertRaisesRegex(checkpoint.CheckpointError, "不符合预登记状态"):
            checkpoint.check_baseline(self.root, self.change, data)

    def test_existing_checkpoint_cannot_be_overwritten(self):
        self.prepare()
        path = checkpoint.journal_path(self.root, self.change)
        original = path.read_bytes()
        with self.assertRaisesRegex(checkpoint.CheckpointError, "检查点目录已存在"):
            self.prepare()
        self.assertEqual(path.read_bytes(), original)

    def test_interrupted_cli_records_failure_without_advancing_stage(self):
        data = self.prepare()
        self.apply_expected(data)
        with patch.object(checkpoint.subprocess, "run", side_effect=subprocess.TimeoutExpired("openspec", 60)):
            with self.assertRaisesRegex(checkpoint.CheckpointError, "实际校验失败"):
                checkpoint.finalize(self.root, self.change, data, "synced")
        saved = checkpoint.load(self.root, self.change)
        self.assertEqual(saved["stage"], "prepared")
        self.assertFalse(saved["last_attempt"]["complete"])
        self.assertIsNone(saved["commands"][-1]["exit_code"])
        with self.assertRaisesRegex(checkpoint.CheckpointError, "失败或中断"):
            checkpoint.check_completed_commands(saved)

    def test_move_before_sync_is_rejected(self):
        data = self.prepare()
        target = self.root / self.archive
        target.parent.mkdir(parents=True)
        (self.root / self.change).rename(target)
        with self.assertRaisesRegex(checkpoint.CheckpointError, "未完成同步"):
            checkpoint.check_locations(self.root, self.archive, data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
