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
        validation = Path(__file__).resolve().parents[4] / ".codex/validation"
        validation.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=validation)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.change = "openspec/changes/example"
        self.tasks = f"{self.change}/tasks.md"
        self.report = f"{self.change}/reviews/change-review.md"
        self.put(f"{self.change}/.openspec.yaml", "schema: spec-driven\nx-workflow_profile: standard\n")
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
                    tasks=self.tasks, plan=[f"{self.change}/proposal.md"], source=[], reference=[])
        args.update(kwargs)
        return evidence.record(SimpleNamespace(**args), self.root, self.change)

    def verify(self, **kwargs):
        args = dict(command="record-verify", profile="standard", independent=None,
                    report=f"{self.change}/reports/verification.md", code=["src"], evidence=["evidence/result.xml"])
        args.update(kwargs)
        return evidence.record(SimpleNamespace(**args), self.root, self.change)

    def ready(self):
        self.plan()
        evidence.start_apply(self.root, self.change, "standard")
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
        evidence.start_apply(self.root, self.change, "standard")
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
        evidence.start_apply(self.root, self.change, "strict")
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
        evidence.start_apply(self.root, self.change, "strict")
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

    def test_unknown_snapshot_format_rejected(self):
        path = self.plan()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = 999
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_reference_drift_blocks_start_without_rewriting_record(self):
        path = self.plan(reference=["src"])
        original = path.read_bytes()
        self.put("src/module.txt", "实施前意外变化\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "实施参考基线"):
            evidence.start_apply(self.root, self.change, "standard")
        self.assertEqual(original, path.read_bytes())

    def test_started_reference_changes_allow_plan_and_repeat_start_is_read_only(self):
        path = self.plan(reference=["src"])
        evidence.start_apply(self.root, self.change, "standard")
        original = path.read_bytes()
        self.put("src/module.txt", "任务中的正常修改\n")
        self.put("src/new.txt", "任务中的新增实现\n")
        evidence.check_plan(self.root, self.change, "standard")
        evidence.start_apply(self.root, self.change, "standard")
        self.assertEqual(original, path.read_bytes())
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        self.verify()
        evidence.check_verify(self.root, self.change, "standard")
        self.put("src/new.txt", "验收之后的修改\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_start_does_not_exempt_changed_planning(self):
        self.plan(reference=["src"])
        evidence.start_apply(self.root, self.change, "standard")
        self.put(self.tasks, "- [ ] 1. 改变验收口径\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.start_apply(self.root, self.change, "standard")

    def test_completed_tasks_without_start_cannot_record_acceptance(self):
        self.plan()
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "尚未登记实施开始"):
            self.verify()
        self.assertFalse(evidence.record_path(self.root, self.change, "verify").exists())

    def test_overlapping_reference_and_constraints_rejected(self):
        for source, reference in (("src", "src/module.txt"), ("src/module.txt", "src"), ("src", "src")):
            with self.subTest(source=source, reference=reference):
                with self.assertRaisesRegex(evidence.EvidenceError, "不能重叠"):
                    self.plan(source=[source], reference=[reference])

    def test_acceptance_requires_code_coverage_of_references(self):
        self.plan(reference=["src"])
        evidence.start_apply(self.root, self.change, "standard")
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "未覆盖实施参考"):
            self.verify(code=["src/module.txt"])

    def test_deleted_reference_captured_by_parent_directory(self):
        self.plan(reference=["src/module.txt"])
        evidence.start_apply(self.root, self.change, "standard")
        (self.root / "src/module.txt").unlink()
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        self.verify(code=["src"])
        evidence.check_verify(self.root, self.change, "standard")
        self.put("src/module.txt", "删除后又出现\n")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_verify(self.root, self.change, "standard")

    def test_start_apply_cli_and_v1_record(self):
        path = self.plan(reference=["src"])
        result = subprocess.run([os.sys.executable, "-B", str(Path(evidence.__file__)),
            "start-apply", "--root", str(self.root), "--change", self.change, "--profile", "standard"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["implementation_started"])
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], 1)

    def test_malformed_start_marker_rejected(self):
        path = self.plan()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["implementation_started"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            evidence.check_plan(self.root, self.change, "standard")

    def test_start_write_failure_preserves_original_record(self):
        path = self.plan(reference=["src"])
        original = path.read_bytes()
        path.parent.chmod(0o500)
        try:
            self.assertFalse(os.access(path.parent, os.W_OK), "测试需要普通用户权限语义")
            with self.assertRaises(OSError):
                evidence.start_apply(self.root, self.change, "standard")
        finally:
            path.parent.chmod(0o700)
        self.assertEqual(original, path.read_bytes())
        self.assertFalse(list(path.parent.glob(".evidence-*")))

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

    def test_main_report_can_also_be_independent_and_auxiliary(self):
        self.put(f"{self.change}/.openspec.yaml", "schema: spec-driven\nx-workflow_profile: strict\n")
        path = self.plan(profile="strict", independent=self.report,
                         review_evidence=[self.report, str(self.root / self.report)])
        data = evidence.check_plan(self.root, self.change, "strict")
        self.assertEqual(data["reports"], [self.report])
        self.assertEqual(data["independent"], self.report)
        self.assertEqual(len(data["report_snapshot"]), 1)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], 1)

    def test_auxiliary_plan_report_is_deduplicated_and_bound(self):
        auxiliary = f"{self.change}/reviews/source-review.md"
        self.put(auxiliary, "来源核对材料\n")
        path = self.plan(review_evidence=[auxiliary, auxiliary, str(self.root / auxiliary)])
        original = path.read_bytes()
        data = evidence.check_plan(self.root, self.change, "standard")
        self.assertEqual(set(data["reports"]), {self.report, auxiliary})
        self.assertIn(auxiliary, data["report_snapshot"])
        self.put(auxiliary, "发现必需行为遗漏\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "评审报告"):
            evidence.check_plan(self.root, self.change, "standard")
        self.assertEqual(path.read_bytes(), original)

    def test_auxiliary_verify_report_is_deduplicated_and_bound(self):
        self.ready()
        auxiliary = f"{self.change}/reviews/quality-review.md"
        self.put(auxiliary, "实现核对材料\n")
        report = f"{self.change}/reports/verification.md"
        self.verify(review_evidence=[auxiliary, str(self.root / auxiliary), report])
        data = evidence.check_verify(self.root, self.change, "standard")
        self.assertEqual(data["inputs"].count(auxiliary), 1)
        self.assertEqual(data["inputs"].count(report), 1)
        self.assertIn(auxiliary, data["snapshot"])
        self.put(auxiliary, "实现核对发现问题\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "验收证据"):
            evidence.check_verify(self.root, self.change, "standard")

    def test_invalid_auxiliary_reports_preserve_existing_records(self):
        self.ready()
        self.put("empty.md", " \n\t")
        (self.root / "linked.md").symlink_to(self.root / self.report)
        (self.root / "linked-dir").symlink_to(self.root / "src", target_is_directory=True)
        invalid = ["missing.md", "empty.md", "src", "../outside.md", "linked.md", "linked-dir/module.txt"]
        for kind, record in (("plan", self.plan), ("verify", self.verify)):
            original = evidence.record_path(self.root, self.change, kind).read_bytes()
            for name in invalid:
                with self.subTest(kind=kind, path=name):
                    with self.assertRaises(evidence.EvidenceError):
                        record(review_evidence=[name])
                    self.assertEqual(evidence.record_path(self.root, self.change, kind).read_bytes(), original)

    def test_auxiliary_report_cannot_include_own_output(self):
        self.ready()
        for kind, record in (("plan", self.plan), ("verify", self.verify)):
            path = evidence.record_path(self.root, self.change, kind)
            original = path.read_bytes()
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(evidence.EvidenceError, "即将写入的记录"):
                    record(review_evidence=[str(path)])
                self.assertEqual(path.read_bytes(), original)

    def test_auxiliary_report_cannot_overlap_mutable_reference(self):
        with self.assertRaisesRegex(evidence.EvidenceError, "不能重叠"):
            self.plan(reference=["src"], review_evidence=["src/module.txt"])
        self.assertFalse(evidence.record_path(self.root, self.change, "plan").exists())

    def test_missing_raw_evidence_prevents_first_acceptance_record(self):
        self.plan()
        evidence.start_apply(self.root, self.change, "standard")
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        (self.root / "evidence/result.xml").unlink()
        with self.assertRaises(evidence.EvidenceError):
            self.verify()
        self.assertFalse(evidence.record_path(self.root, self.change, "verify").exists())

    def test_metadata_normalization_requires_new_review(self):
        self.put(f"{self.change}/.openspec.yaml", "schema: spec-driven\nworkflow_profile: standard\n")
        path = self.plan()
        original = path.read_bytes()
        self.put(f"{self.change}/.openspec.yaml", "schema: spec-driven\nx-workflow_profile: standard\n")
        with self.assertRaisesRegex(evidence.EvidenceError, "规划或来源"):
            evidence.check_plan(self.root, self.change, "standard")
        self.assertEqual(path.read_bytes(), original)

    def test_repeatable_review_evidence_cli_for_both_stages(self):
        auxiliary = f"{self.change}/reviews/topic-review.md"
        self.put(auxiliary, "附加核对材料\n")
        common = [os.sys.executable, "-B", str(Path(evidence.__file__))]
        suffix = ["--root", str(self.root), "--change", self.change, "--profile", "standard",
                  "--review-evidence", auxiliary, "--review-evidence", auxiliary]
        result = subprocess.run(common + ["record-plan", "--tasks", self.tasks,
            "--plan", f"{self.change}/proposal.md", "--report", self.report] + suffix,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(evidence.check_plan(self.root, self.change, "standard")["reports"].count(auxiliary), 1)
        evidence.start_apply(self.root, self.change, "standard")
        self.put(self.tasks, "- [x] 1. 修复并验证边界条件\n")
        result = subprocess.run(common + ["record-verify", "--code", "src", "--evidence", "evidence/result.xml",
            "--report", f"{self.change}/reports/verification.md"] + suffix, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(evidence.check_verify(self.root, self.change, "standard")["inputs"].count(auxiliary), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
