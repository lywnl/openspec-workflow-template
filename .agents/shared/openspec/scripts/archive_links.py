"""识别常见 Markdown 相对文件链接，仅计算归档移动所需的目标地址变化。"""

from __future__ import annotations

import html
import posixpath
import re
from urllib.parse import quote, unquote


class LinkError(ValueError):
    pass


def within(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent + "/")


def mapped(path: str, active: str, archive: str) -> str:
    return archive + path[len(active):] if within(path, active) else path


def prose(text: str) -> str:
    """保留字符偏移，排除围栏、缩进代码、代码跨度及 HTML 注释。"""
    lines = []
    fence = None
    list_indents = []
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        indent = len(line) - len(line.lstrip(" "))
        item = re.match(r"^ *(?:[-*+]|\d+[.)]) +", line)
        if line.strip() and fence is None:
            while list_indents and indent < list_indents[-1]:
                list_indents.pop()
            if item:
                list_indents.append(item.end())
        code_indent = (list_indents[-1] if list_indents else 0) + 4
        hidden = fence is not None or marker is not None or (not item and indent >= code_indent) or line.startswith("\t")
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
        lines.append(re.sub(r"[^\r\n]", " ", line) if hidden else line)
    value = "".join(lines)
    for pattern in (r"<!--[\s\S]*?-->", r"(?<![\\`])(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)"):
        value = re.sub(pattern, lambda match: re.sub(r"[^\r\n]", " ", match.group()), value)
    return value


def destinations(text: str) -> list[tuple[int, int]]:
    """支持内联链接/图片、引用定义、尖括号目标和转义/成对括号。"""
    visible = prose(text)
    starts = re.compile(r"(?P<reference>^ {0,3}\[(?!\^)[^\]\n]+\]:[ \t]*)|(?P<inline>(?<!\\)\]\([ \t]*)", re.M)
    spans = []
    for match in starts.finditer(visible):
        # 没有标签起始符的普通文本不是链接。
        if match.group("inline") and "[" not in visible[:match.start()].rsplit("\n", 1)[-1]:
            continue
        start = match.end()
        if start >= len(visible):
            continue
        if visible[start] == "<":
            end = start + 1
            while end < len(visible) and visible[end] not in ">\r\n":
                end += 2 if visible[end] == "\\" else 1
            if end >= len(visible) or visible[end] != ">":
                raise LinkError("Markdown 链接尖括号未闭合，请人工核对")
            start += 1
            tail = end + 1
        else:
            end, depth = start, 0
            while end < len(visible):
                char = visible[end]
                if char == "\\" and end + 1 < len(visible):
                    end += 2
                    continue
                if char.isspace() or (char == ")" and depth == 0):
                    break
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                end += 1
            if depth:
                raise LinkError("Markdown 链接目标括号不配对，请人工核对")
            tail = end
        if match.group("inline") and not re.match(
                r"\s*(?:(?:\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\([^)]*\))\s*)?\)", visible[tail:]):
            raise LinkError("Markdown 链接格式超出自动处理范围，请人工核对")
        if end > start:
            spans.append((start, end))
    # HTML 文件链接不应被静默漏检；代码示例中的同类文本已被排除。
    if re.search(r"<[^>]+\b(?:href|src)\s*=", visible, re.I):
        raise LinkError("存在 HTML href/src 链接，请按人工导航核验约定处理，不宣称自动覆盖")
    return spans


def relative_target(source: str, destination: str) -> str | None:
    value = html.unescape(re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", destination))
    if not value or value.startswith(("#", "?", "/")) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
        return None
    path = unquote(re.split(r"[?#]", value, maxsplit=1)[0], errors="strict")
    if "\\" in path or "\0" in path or path.startswith("/"):
        raise LinkError(f"不支持的本地链接路径：{destination}")
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    if target == ".." or target.startswith("../"):
        raise LinkError(f"相对链接超出项目根：{source} -> {destination}")
    return target


def rewrite(text: str, source: str, active: str, archive: str) -> tuple[str, list[dict]]:
    """纯计算：只更换因移动失效的地址，保留标签、正文、标题和查询/片段。"""
    new_source = mapped(source, active, archive)
    references, replacements = [], []
    for start, end in destinations(text):
        destination = text[start:end]
        target = relative_target(source, destination)
        if target is None:
            continue
        expected_target = mapped(target, active, archive)
        # 对外链接在多一层目录后可能越界；新地址应从原目标计算。
        try:
            actual_target = relative_target(new_source, destination)
        except LinkError:
            actual_target = None
        updated = destination
        if actual_target != expected_target:
            suffix = re.search(r"[?#].*", html.unescape(destination), re.S)
            relative = posixpath.relpath(expected_target, posixpath.dirname(new_source) or ".")
            updated = quote(relative, safe="/.-_~") + (suffix.group() if suffix else "")
            replacements.append((start, end, updated))
        references.append({"source": source, "line": text.count("\n", 0, start) + 1,
                           "destination": destination, "updated_destination": updated,
                           "target": target, "archived_target": expected_target})
    for start, end, updated in reversed(replacements):
        text = text[:start] + updated + text[end:]
    return text, references
