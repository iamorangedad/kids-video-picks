#!/usr/bin/env python3
"""Render the WeChat comparison tables from data/catalog.json (stdlib only)."""

import argparse
import html
import json
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("学习类", "自然类", "人文类", "情感品格类", "益智动画类", "动画娱乐类")
VERDICT_RANK = {"强烈推荐": 0, "推荐": 1, "有保留": 2, "不推荐": 3}
COLUMNS = ("图片", "名称", "判断", "适龄", "简介", "研判", "证据状态", "视频链接")
NAV = ("[返回首页](../../README.md) · [审核方法](review-method.md) · "
       "[不推荐](not-recommended.md) · [文章28待核验](pending-article-28.md)")


def text(value):
    """Escape literal cell text, including GFM pipes and inline Markdown syntax."""
    value = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    value = html.escape(value, quote=True)
    for char, entity in (("|", "&#124;"), ("\\", "&#92;"), ("*", "&#42;"),
                         ("_", "&#95;"), ("[", "&#91;"), ("]", "&#93;"),
                         ("`", "&#96;")):
        value = value.replace(char, entity)
    return value.replace("\n", "<br>")


def attribute(value):
    """Keep attribute values literal; line breaks belong in cell text only."""
    value = str(value or "").replace("\r", " ").replace("\n", " ")
    return html.escape(value, quote=True).replace("|", "&#124;")


def link(label, url):
    """Use angle-wrapped destinations so parentheses/spaces cannot break links."""
    if urlsplit(url).scheme not in ("http", "https"):
        raise ValueError(f"Expected a public http(s) URL: {url!r}")
    destination = quote(url, safe=":/?#[]@!$&'()*+,;=%-._~")
    return f"[{text(label)}](<{destination}>)"


def compact(value, limit=100):
    """Keep long descriptions compact without discarding any original text."""
    value = str(value or "未核实")
    if len(value) <= limit:
        return text(value)
    preview = value[:80].rstrip() + "…（展开）"
    return f"<details><summary>{text(preview)}</summary>{text(value)}</details>"


def sort_key(entry):
    return (VERDICT_RANK[entry["verdict"]], entry["name_zh"].casefold(), entry["id"])


def page_name(entry):
    # Exclusions win over pending status; every entry appears on one page only.
    if entry["verdict"] == "不推荐":
        return "not-recommended.md"
    if entry.get("pending_verification"):
        return "pending-article-28.md"
    if entry["category"] not in CATEGORIES:
        raise ValueError(f"Unknown category: {entry['category']!r}")
    return entry["category"] + ".md"


def thumbnail(entry):
    image_path = Path(entry["image_path"])
    if image_path.is_absolute() or ".." in image_path.parts:
        raise ValueError(f"Invalid image path: {image_path}")
    if not (ROOT / image_path).is_file():
        raise ValueError(f"Missing image: {image_path}")
    src = quote("../../" + image_path.as_posix(), safe="/-._~")
    kind = entry.get("image_kind", "图片来源未核实")
    if "自制文字" in kind:
        caption = "文字封面（非官方海报）"
    elif "通用配图" in kind:
        caption = "公众号通用图（非本片海报）"
    elif "原库图片" in kind:
        caption = "旧图（未逐张鉴定）"
    elif "独立评测" in kind:
        caption = "评测页海报"
    else:
        caption = kind
    title = kind + "；" + (entry.get("image_note") or "")
    image = (f'<a href="{src}"><img src="{src}" width="80" '
             f'alt="{attribute(entry["name_zh"])}" title="{attribute(title)}"></a>')
    # A title card is original artwork, not the stale image_url retained in data.
    source = (None if "自制文字" in kind
              else entry.get("image_source") or entry.get("image_url"))
    if source:
        caption = link(caption, source)
    else:
        caption = text(caption)
    return image + "<br>" + caption


def name_cell(entry):
    value = f'<a id="{attribute(entry["id"])}"></a>' + text(entry["name_zh"])
    if entry.get("name_en") and entry["name_en"].casefold() != entry["name_zh"].casefold():
        value += "<br>" + text(entry["name_en"])
    if entry.get("article_year"):
        value += "<br>" + text(f"原文年份：{entry['article_year']}（未核实）")
    sources = [link(f"文章{s['article_no']}", s["url"]) for s in entry.get("sources", [])]
    if sources:
        value += "<br>" + " · ".join(dict.fromkeys(sources))
    return value


def age_cell(entry):
    value = text(entry.get("reviewed_age") or "未核实")
    original = entry.get("age_group")
    if original and not entry.get("pending_verification"):
        value += ("<br><details><summary>原文说法</summary>"
                  + text(original) + "</details>")
    return value


def evidence_cell(entry):
    review = entry.get("review", {})
    parts = [text(review.get("status") or "未核实"),
             "置信度：" + text(review.get("confidence") or "未核实")]
    for evidence in review.get("evidence", []):
        citation = link(evidence["source"], evidence["url"])
        scope = evidence.get("scope")
        if scope and scope != "单部作品":
            citation += "（" + text(scope) + "）"
        parts.append(citation)
    if not review.get("evidence"):
        parts.append("未取得作品级独立依据")
    return "<br>".join(parts)


def video_cell(entry):
    url = entry.get("video_url")
    if not url:
        return "未核实正版正片"
    kind = entry.get("video_kind") or ""
    label = "官方入口（非已验证正片）" if kind.startswith("官方") else "地址（播放未核实）"
    return link(label, url)


def row(entry):
    cells = (thumbnail(entry), name_cell(entry), text(entry["verdict"]),
             age_cell(entry), compact(entry.get("description_zh")),
             text(entry.get("review_rationale_zh") or "未核实"),
             evidence_cell(entry), video_cell(entry))
    assert len(cells) == len(COLUMNS)
    assert all("|" not in cell and "\n" not in cell and "\r" not in cell for cell in cells)
    return "| " + " | ".join(cells) + " |"


def render_page(filename, entries):
    if filename == "not-recommended.md":
        title = "不推荐作为0—12岁儿童日常片单"
        introduction = (f"本页 {len(entries)} 条。不是否定艺术价值。成熟青少年可按各自年龄、"
                        "经历与家庭选择另外讨论。")
    elif filename == "pending-article-28.md":
        title = "文章28：仅片名留档，待独立核验"
        introduction = (f"本页 {len(entries)} 条，全部暂为有保留，**不进入精选**。原文未逐片标龄，"
                        "年份仅为原文说法。未核实的简介、原名、评分、视频和海报不编造。")
    else:
        title = filename.removesuffix(".md")
        introduction = (f"本页 {len(entries)} 条，按强烈推荐→推荐→有保留排序。"
                        "**有保留不等于推荐；年龄不等于听力难度；图片不证明适龄。**")
    lines = [f"# {title}", "",
             "<!-- Generated by scripts/render_wechat_tables.py; edit data/catalog.json instead. -->",
             "", NAV, "", introduction, "",
             "每行一部，名称下的文章编号链接原文。适龄为审核建议；折叠的“原文说法”不代表采信。"
             "缩略图可点开放大，图下注明海报、旧图或文字封面；长简介可展开。", "",
             "未注明已核实的豆瓣/IMDb评分和人数一律视为未核实；公众号评分不作独立证据。"
             "独立评测不等于教育效果证明，相关App/合集也不是单片认证。"
             "视频列仅保留官方入口等已记录地址，**不代表免费、完整或当地可播正片**；"
             "候选地址不展示。完整字段见[主目录数据](../../data/catalog.json)。", "",
             "| " + " | ".join(COLUMNS) + " |",
             "| " + " | ".join("---" for _ in COLUMNS) + " |"]
    lines.extend(row(entry) for entry in sorted(entries, key=sort_key))
    return "\n".join(lines) + "\n"


def generate():
    catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
    entries = catalog["entries"]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate catalog IDs")
    groups = {category + ".md": [] for category in CATEGORIES}
    groups.update({"not-recommended.md": [], "pending-article-28.md": []})
    for entry in entries:
        groups[page_name(entry)].append(entry)
    return {ROOT / "docs/wechat" / name: render_page(name, rows)
            for name, rows in groups.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated tables are stale")
    args = parser.parse_args()
    changed = []
    for path, content in generate().items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(path.relative_to(ROOT).as_posix())
            if not args.check:
                path.write_text(content, encoding="utf-8")
    if args.check and changed:
        parser.exit(1, "Stale comparison tables:\n" + "\n".join(changed) + "\n")
    print(("Checked" if args.check else "Rendered") + " 8 comparison tables; "
          + str(len(changed)) + " file(s) " + ("stale" if args.check else "updated"))


if __name__ == "__main__":
    main()
