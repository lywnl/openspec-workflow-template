"""用隔离文件验证指纹失效条件；权限用例需普通用户的 POSIX 环境，不运行业务验收。"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SPEC = importlib.util.spec_from_file_location("evidence", Path(__file__).with_name("evidence.py"))
assert SPEC and SPEC.loader
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.change = "openspec/changes/example"
        self.tasks = f"{self.change}/tasks.md"
        self.report = f"{self.change}/reviews/change-review.md"
        self.put(f"{self.change}/.openspec.yaml", "schema: fast-change\n")
        self.put(f"{self.change}/proposal.md", "# 提案\n修复边界条件。\n")
        self.put(self.tasks, "- [ ] 1. 修复并验证边界条件\n")
        self.put(self.report, "# 规划评审\nPASS\n")
        self.put("src/module.txt", "实际实现\n")
        self.put("evidence/result.xml", "<testsuite failures='0'/>\n")
        self.put(f"{self.change}/reports/verification.md", "Ready for Archive\n")

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def plan(self, **kwargs):
        args = dict(command="record-plan", profile="standard", independent=None, report=self.report,
                    tasks=self.tasks, plan=[f"{self.change}/proposal.md"], source=[])
        args.update(kwargs)
        return evidence.record(SimpleNamespace(**args), self.root, self.change)

    def verify(self, **kwargs):
        args = dict(command="record-verify", profile="standard", independent=None,
                    report=f"{self.change}/reports/verification.md", code=["src"], evidence=["evidence/result.xml"])
        args.update(kwargs)
        return evidence.record(SimpleNamespace(**args), self.root, self.change)

    def ready(self):
        self.plan()
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        self.verify()

    def test_progress_does_not_invalidate_planning_but_text_does(self):
        self.plan()
        self.put(self.tasks, "- [X] 1. 修复并验证边界条件\n")
        evidence.check_plan(self.root, self.change, "standard")
        self.put(self.tasks, "- [X] 1. 删除验收条件\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_modified_report_or_profile_invalidates(self):
        self.plan()
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "strict")
        self.put(self.report, "BLOCK\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_incomplete_tasks_cannot_record_acceptance(self):
        self.plan()
        with self.assertRaises(evidence.EvidenceError):
            self.verify()

    def test_new_implementation_file_invalidates_acceptance(self):
        self.ready()
        evidence.check_verify(self.root, self.change, "standard")
        self.put("src/new-untracked.txt", "未验收新增实现\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_missing_evidence_invalidates_acceptance(self):
        self.ready()
        (self.root / "evidence/result.xml").unlink()
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_task_unchecked_invalidates_acceptance(self):
        self.ready()
        self.put(self.tasks, "- [ ] 1. 修复并验证边界条件\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_strict_requires_independent_review(self):
        with self.assertRaises(evidence.EvidenceError):
            self.plan(profile="strict")
        self.put("reviewer.md", "独立规划评审 PASS\n")
        self.plan(profile="strict", independent="reviewer.md")
        evidence.check_plan(self.root, self.change, "strict")
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        with self.assertRaises(evidence.EvidenceError):
            self.verify(profile="strict")

    def test_fenced_examples_are_not_tasks(self):
        normalized, states = evidence.task_lines("```md\n- [x] 示例\n```\n- [x] 实际任务\n".encode())
        self.assertEqual(states, [True])
        self.assertIn(b"- [x]", normalized)
        self.assertTrue(normalized.endswith("- [ ] 实际任务\n".encode()))

    def test_outside_paths_and_symlinks_are_rejected(self):
        with self.assertRaises(evidence.EvidenceError):
            evidence.snapshot(self.root, ["../outside.txt"])
        (self.root / "linked").symlink_to(self.root / "src", target_is_directory=True)
        with self.assertRaises(evidence.EvidenceError):
            evidence.snapshot(self.root, ["linked"])

    def test_new_spec_invalidates_planning(self):
        self.put(f"{self.change}/specs/one/spec.md", "第一个规范\n")
        self.plan(plan=[f"{self.change}/specs"])
        self.put(f"{self.change}/specs/two/spec.md", "新增规范\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_self_including_record_range_is_rejected(self):
        with self.assertRaises(evidence.EvidenceError):
            self.plan(plan=[self.change])

    def test_strict_complete_flow_and_independent_report_change(self):
        self.put("independent-plan.md", "独立规划评审：基线完整。\n")
        self.put("independent-code.md", "独立代码评审：未发现阻塞。\n")
        self.plan(profile="strict", independent="independent-plan.md")
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        self.verify(profile="strict", independent="independent-code.md")
        evidence.check_verify(self.root, self.change, "strict")
        self.put("independent-code.md", "独立代码评审：发现待修复阻塞。\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "strict")

    def test_changed_code_bytes_invalidates_acceptance_without_git(self):
        self.ready()
        self.put("src/module.txt", "实施后又修改了行为\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_registered_source_change_invalidates_plan(self):
        self.put("requirements.md", "已确认需求\n")
        self.plan(source=["requirements.md"])
        self.put("requirements.md", "已变更需求\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_corrupt_record_cannot_be_reused(self):
        self.plan()
        evidence.record_path(self.root, self.change, "plan").write_text("[]", encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_removed_execute_permission_invalidates_acceptance(self):
        self.put("src/run.sh", "#!/bin/sh\nexit 0\n")
        script = self.root / "src/run.sh"
        script.chmod(0o755)
        self.ready()
        subprocess.run([str(script)], check=True)
        script.chmod(0o644)
        with self.assertRaises(PermissionError):
            subprocess.run([str(script)], check=True)
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_added_execute_permission_invalidates_planning(self):
        self.plan()
        (self.root / self.tasks).chmod(0o755)
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_unsupported_task_format_is_rejected_before_plan_record(self):
        self.put(self.tasks, '{"tasks": [{"done": true}]}\n')
        with self.assertRaisesRegex(evidence.EvidenceError, "Markdown"):
            self.plan()
        self.assertFalse(evidence.record_path(self.root, self.change, "plan").exists())

    def test_old_snapshot_version_requires_revalidation(self):
        path = self.plan()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_unreadable_directory_fails_instead_of_partial_snapshot(self):
        self.put("src/private/input.txt", "不可漏登记的输入\n")
        directory = self.root / "src/private"
        directory.chmod(0)
        try:
            self.assertFalse(os.access(directory, os.R_OK), "该用例需要普通用户的权限语义")
            with self.assertRaises(OSError):
                evidence.snapshot(self.root, ["src"])
        finally:
            directory.chmod(0o755)


if __name__ == "__main__":
    unittest.main(verbosity=2)
