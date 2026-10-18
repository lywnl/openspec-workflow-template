"""验证相对文件地址计算；不以固定报告文案代替归档行为测试。"""

import unittest

from archive_links import LinkError, relative_target, rewrite


ACTIVE = "openspec/changes/example"
ARCHIVE = "openspec/changes/archive/2026-10-18-example"


class ArchiveLinksTests(unittest.TestCase):
    def test_readme_inbound_link_keeps_label_title_query_and_fragment(self):
        text = f'[验收]({ACTIVE}/reports/verification.md?view=raw#结果 "验收标题")\n'
        updated, references = rewrite(text, "README.md", ACTIVE, ARCHIVE)
        self.assertEqual(updated, text.replace(ACTIVE, ARCHIVE))
        self.assertEqual(references[0]["archived_target"], f"{ARCHIVE}/reports/verification.md")

    def test_outgoing_source_links_rebase_while_internal_link_is_unchanged(self):
        text = "[规则](../../../../AGENTS.md) [配置](../../../config.yaml) [提案](../proposal.md)\n"
        updated, references = rewrite(text, f"{ACTIVE}/sources/user-request.md", ACTIVE, ARCHIVE)
        self.assertEqual(updated, "[规则](../../../../../AGENTS.md) [配置](../../../../config.yaml) [提案](../proposal.md)\n")
        self.assertEqual([item["target"] for item in references], ["AGENTS.md", "openspec/config.yaml", f"{ACTIVE}/proposal.md"])

    def test_reference_definitions_images_nested_labels_and_encoded_paths(self):
        text = (f'[报告][result]\n\n[result]: <{ACTIVE}/sources/我的 说明.md> "原始说明"\n'
                f'[![图示]({ACTIVE}/diagram.png)]({ACTIVE}/proposal.md)\n')
        updated, references = rewrite(text, "README.md", ACTIVE, ARCHIVE)
        self.assertIn(f"<{ARCHIVE}/sources/%E6%88%91%E7%9A%84%20%E8%AF%B4%E6%98%8E.md>", updated)
        self.assertIn(f"[![图示]({ARCHIVE}/diagram.png)]({ARCHIVE}/proposal.md)", updated)
        self.assertEqual(len(references), 3)

    def test_balanced_and_escaped_parentheses_are_valid_destinations(self):
        for destination in (f"{ACTIVE}/a(b).md", f"{ACTIVE}/a\\(b\\).md", f"{ACTIVE}/a%28b%29.md"):
            with self.subTest(destination=destination):
                updated, references = rewrite(f"[报告]({destination})", "README.md", ACTIVE, ARCHIVE)
                self.assertEqual(updated, f"[报告]({ARCHIVE}/a%28b%29.md)")
                self.assertEqual(references[0]["target"], f"{ACTIVE}/a(b).md")

    def test_code_comments_footnote_text_external_and_anchor_links_are_preserved(self):
        literal = f"[历史示例]({ACTIVE}/missing.md)"
        text = (f"`{literal}`\n```md\n{literal}\n```\n~~~\n{literal}\n~~~\n"
                f"\n    {literal}\n\n<!-- {literal} -->\n"
                "[^1]: 这是脚注正文，不是链接定义。\n"
                "[网站](https://example.com/a) [邮件](mailto:a@example.com) [章节](#验收) [站点](/guide)\n")
        self.assertEqual(rewrite(text, "README.md", ACTIVE, ARCHIVE), (text, []))

    def test_nested_list_links_are_not_mistaken_for_indented_code(self):
        text = f"- 导航\n    - [报告]({ACTIVE}/proposal.md)\n      [详细报告]({ACTIVE}/design.md)\n"
        updated, references = rewrite(text, "README.md", ACTIVE, ARCHIVE)
        self.assertEqual(updated, text.replace(ACTIVE, ARCHIVE))
        self.assertEqual(len(references), 2)

    def test_changed_destinations_preserve_crlf_and_all_other_text(self):
        text = f"# 交付\r\n\r\n正文 [报告]({ACTIVE}/proposal.md)。\r\n"
        updated, _ = rewrite(text, "README.md", ACTIVE, ARCHIVE)
        self.assertEqual(updated.encode(), text.replace(ACTIVE, ARCHIVE).encode())

    def test_entity_encoded_fragment_keeps_its_meaning_after_move(self):
        text = f"[章节]({ACTIVE}/proposal.md&#35;why)"
        updated, refs = rewrite(text, "README.md", ACTIVE, ARCHIVE)
        self.assertEqual(updated, f"[章节]({ARCHIVE}/proposal.md#why)")
        self.assertEqual(refs[0]["target"], f"{ACTIVE}/proposal.md")

    def test_html_and_out_of_root_paths_are_explicitly_rejected(self):
        for text in ('<a href="doc.md">报告</a>', "[外部](../private.md)", "[坏地址](a(b.md)"):
            with self.subTest(text=text), self.assertRaises(LinkError):
                rewrite(text, "README.md", ACTIVE, ARCHIVE)
        with self.assertRaises(LinkError):
            relative_target("README.md", "%2Fetc/passwd")


if __name__ == "__main__":
    unittest.main(verbosity=2)
