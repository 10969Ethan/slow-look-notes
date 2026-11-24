#!/usr/bin/env python3
"""建立一篇新練習的骨架。

用法：
    python3 tools/new_note.py <slug> <分類>
    python3 tools/new_note.py texture-trail 觸感

會做的事（只用 Python 標準函式庫）：
  1. 檢查 slug 是否為英文小寫 kebab-case、檔案是否已存在、分類是否在 tools/categories.json。
  2. 取「現有最大編號 + 1」作為新編號（兩位數）。
  3. 從 templates/note.html 建立 docs/notes/<slug>.html，填好編號、分類、底色類別與「上一篇」連結。
  4. 在上一篇（目前最後一篇）的 pager 補上「下一篇」連結。
  5. 在 docs/index.html 的 <!-- cards:end --> 前插入一張卡片骨架。

內容欄位（{{標題}}、{{摘要}}…）刻意留空，由 AI 或作者依 AGENTS.md 填寫；
填完後執行 python3 tools/check.py，有殘留的雙大括號就不會通過。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "docs" / "notes"
INDEX = ROOT / "docs" / "index.html"
TEMPLATE = ROOT / "templates" / "note.html"
CATEGORIES = json.loads((ROOT / "tools" / "categories.json").read_text(encoding="utf-8"))

LABEL_RE = re.compile(r'<p class="label">練習 (\d{2,}) ／ ([^<]+)</p>')
H1_RE = re.compile(r"<h1>([^<]+)</h1>")
NEXT_MARK = "<!-- next -->"
CARDS_END = "<!-- cards:end -->"


def fail(msg: str) -> None:
    print(f"✗ {msg}")
    sys.exit(1)


def existing_notes():
    """回傳 [(編號, slug, 標題)]，依編號排序。"""
    notes = []
    for path in NOTES.glob("*.html"):
        html = path.read_text(encoding="utf-8")
        m = LABEL_RE.search(html)
        t = H1_RE.search(html)
        if m:
            notes.append((int(m.group(1)), path.stem, t.group(1) if t else path.stem))
    return sorted(notes)


def main() -> None:
    if len(sys.argv) != 3:
        fail("用法：python3 tools/new_note.py <slug> <分類>")
    slug, category = sys.argv[1], sys.argv[2]

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        fail(f"slug「{slug}」必須是英文小寫 kebab-case，例如 texture-trail")
    target = NOTES / f"{slug}.html"
    if target.exists():
        fail(f"{target.relative_to(ROOT)} 已存在；公開頁的檔名視為固定網址，請換一個 slug")
    if category not in CATEGORIES:
        names = "、".join(CATEGORIES)
        fail(f"分類「{category}」不在 tools/categories.json（目前有：{names}）。"
             "新分類請先依 AGENTS.md「新增分類」一節登錄。")

    notes = existing_notes()
    number = (notes[-1][0] + 1) if notes else 1
    num = f"{number:02d}"
    css_class = CATEGORIES[category]["class"]

    prev_link = ""
    if notes:
        p_num, p_slug, p_title = notes[-1]
        prev_link = f'<a class="prev" href="{p_slug}.html">← 練習 {p_num:02d} {p_title}</a>'

    html = TEMPLATE.read_text(encoding="utf-8")
    html = (html.replace("{{編號}}", num)
                .replace("{{分類}}", category)
                .replace("{{底色類別}}", css_class)
                .replace("{{上一篇}}", prev_link))
    target.write_text(html, encoding="utf-8")

    # 上一篇補「下一篇」連結（標題先用 slug，check.py 會要求填成正式標題）
    if notes:
        prev_path = NOTES / f"{notes[-1][1]}.html"
        prev_html = prev_path.read_text(encoding="utf-8")
        if NEXT_MARK not in prev_html:
            fail(f"{prev_path.name} 找不到 {NEXT_MARK}，無法補上下一篇連結")
        prev_html = prev_html.replace(
            NEXT_MARK, f'<a class="next" href="{slug}.html">練習 {num} {{{{標題}}}} →</a>')
        prev_path.write_text(prev_html, encoding="utf-8")

    card = f"""<li class="card {css_class}">
          <a href="notes/{slug}.html">
            <div class="card-body">
              <span class="label">練習 {num} ／ {category}</span>
              <h3>{{{{標題}}}} <span aria-hidden="true">↗</span></h3>
              <p>{{{{摘要}}}}</p>
              <span class="time">{{{{時間}}}}</span>
            </div>
          </a>
        </li>
        {CARDS_END}"""
    index = INDEX.read_text(encoding="utf-8")
    if CARDS_END not in index:
        fail(f"docs/index.html 找不到 {CARDS_END}")
    INDEX.write_text(index.replace(CARDS_END, card, 1), encoding="utf-8")

    print(f"✓ 建立 docs/notes/{slug}.html（練習 {num} ／ {category}，.{css_class}）")
    print("  接下來：")
    print(f"  1. 填完 docs/notes/{slug}.html 所有 {{{{…}}}} 欄位")
    print("  2. 填完 docs/index.html 新卡片與上一篇 pager 的 {{標題}} 等欄位（可加原創 SVG）")
    print("  3. 執行 python3 tools/check.py，直到全部通過")


if __name__ == "__main__":
    main()
