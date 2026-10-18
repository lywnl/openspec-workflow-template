"""验证验收映射的结构与引用，不将样例清单视为业务验收。"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import evidence_manifest as manifest


class ManifestTests(unittest.TestCase):
    def setUp(self):
        validation = Path(__file__).resolve().parents[4] / ".codex/validation"
        validation.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=validation)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ("src/example.txt", "tests/example.txt", "logs/result.txt"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("结构校验样例\n", encoding="utf-8")
        self.data = {"requirements": [{"id": "边界处理／任务 1.1", "implementation": ["src/example.txt"],
            "tests": ["tests/example.txt"], "evidence": ["logs/result.txt"], "status": "verified"}],
            "commands": [{"command": "实际命令记录的格式样例", "cwd": ".", "exit_code": 0,
                          "evidence": "logs/result.txt"}]}

    def check(self):
        (self.root / "manifest.json").write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        return manifest.check(self.root, "manifest.json")

    def test_valid_mapping(self):
        self.assertEqual(self.check(), {"valid": True, "requirements": 1, "commands": 1})

    def test_duplicate_ids_are_rejected(self):
        self.data["requirements"].append(copy.deepcopy(self.data["requirements"][0]))
        with self.assertRaisesRegex(manifest.ManifestError, "重复"):
            self.check()

    def test_unverified_states_are_rejected(self):
        for status in ("pending", "skipped", "blocked", True, None):
            with self.subTest(status=status):
                self.data["requirements"][0]["status"] = status
                with self.assertRaisesRegex(manifest.ManifestError, "status=verified"):
                    self.check()

    def test_missing_or_invalid_references_are_rejected(self):
        original = copy.deepcopy(self.data)
        for key in ("implementation", "tests", "evidence"):
            for value in ([], ["missing.txt"], ["tests/example.txt::test_case"], ["../outside.txt"]):
                with self.subTest(key=key, value=value):
                    self.data = copy.deepcopy(original)
                    self.data["requirements"][0][key] = value
                    with self.assertRaises(manifest.ManifestError):
                        self.check()

    def test_symlink_reference_is_rejected(self):
        (self.root / "linked.txt").symlink_to(self.root / "logs/result.txt")
        self.data["requirements"][0]["evidence"] = ["linked.txt"]
        with self.assertRaisesRegex(manifest.ManifestError, "符号链接"):
            self.check()

    def test_command_fields_are_checked(self):
        original = copy.deepcopy(self.data)
        for key, value in (("command", ""), ("cwd", "../"), ("cwd", "src/example.txt"),
                           ("exit_code", True), ("exit_code", "0"), ("evidence", "missing.txt")):
            with self.subTest(key=key, value=value):
                self.data = copy.deepcopy(original)
                self.data["commands"][0][key] = value
                with self.assertRaises(manifest.ManifestError):
                    self.check()

    def test_nonzero_exit_is_preserved_for_semantic_review(self):
        self.data["commands"][0]["exit_code"] = 1
        self.assertTrue(self.check()["valid"])
        self.assertEqual(self.data["commands"][0]["exit_code"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
