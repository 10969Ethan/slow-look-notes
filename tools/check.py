#!/usr/bin/env python3
"""檢查整站是否符合 AGENTS.md 的規則。只用 Python 標準函式庫。

用法：python3 tools/check.py
全部通過時回傳 0；任何一條規則不符就列出「檔案：問題」並回傳 1。
GitHub Actions（.github/workflows/check.yml）每次 push 都會跑這支程式。
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
NOTES = DOCS / "notes"
CSS = (DOCS / "assets" / "site.css").read_text(encoding="utf-8")
CATEGORIES = json.loads((ROOT / "tools" / "categories.json").read_text(encoding="utf-8"))
CLASS_TO_CAT = {v["class"]: k for k, v in CATEGORIES.items()}
SECTIONS = ["觀察目標", "練習步驟", "紀錄示例", "想一想"]
META = ["時間", "準備", "地點"]
VOID = {"meta", "link", "br", "img", "hr", "input", "path", "circle", "rect", "ellipse", "line", "polyline", "polygon", "stop"}

errors: list[str] = []


def err(path: Path, msg: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}：{msg}")


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children, self.text = [], ""

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def all_text(self):
        return (self.text + "".join(c.all_text() for c in self.children)).strip()

    def find_all(self, tag=None, cls=None):
        out = []
        for c in self.children:
            if (tag is None or c.tag == tag) and (cls is None or cls in c.classes):
                out.append(c)
            out.extend(c.find_all(tag, cls))
        return out

    def find(self, tag=None, cls=None):
        r = self.find_all(tag, cls)
        return r[0] if r else None


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", [])
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        # 文字依序接在目前節點（足以比對標題、摘要這類單純文字）
        self.cur.text += data


def parse(path: Path):
    b = Builder()
    b.feed(path.read_text(encoding="utf-8"))
    return b.root


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("↗", "")).strip()


def check_common(path: Path, root: Node, raw: str):
    html = root.find("html")
    if not html or html.attrs.get("lang") != "zh-Hant":
        err(path, '<html> 需要 lang="zh-Hant"')
    if not any(m.attrs.get("name") == "viewport" for m in root.find_all("meta")):
        err(path, "缺少 viewport meta")
    if not any(m.attrs.get("charset", "").lower() == "utf-8" for m in root.find_all("meta")):
        err(path, '缺少 <meta charset="utf-8">')
    if "{{" in raw or "}}" in raw:
        err(path, "還有沒填完的 {{…}} 欄位")
    if len(root.find_all("h1")) != 1:
        err(path, f"每頁只能有一個 H1（目前 {len(root.find_all('h1'))} 個）")
    for svg in root.find_all("svg"):
        if svg.attrs.get("aria-hidden") != "true" or svg.attrs.get("focusable") != "false":
            err(path, '裝飾 SVG 需要 aria-hidden="true" 與 focusable="false"')
    # 所有相對連結都要指到存在的檔案
    for node in root.find_all():
        for attr in ("href", "src"):
            url = node.attrs.get(attr)
            if not url or re.match(r"^(https?:|mailto:|#)", url):
                continue
            if url.startswith("/"):
                err(path, f"{url} 是絕對路徑；GitHub Pages 子路徑下會壞，請改相對路徑")
                continue
            file_part = url.split("#")[0]
            if file_part and not (path.parent / file_part).resolve().exists():
                err(path, f"連結 {url} 指到不存在的檔案")


def check_note(path: Path):
    raw = path.read_text(encoding="utf-8")
    root = parse(path)
    check_common(path, root, raw)
    info = {"slug": path.stem}

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", path.stem):
        err(path, "檔名必須是英文小寫 kebab-case")

    header = root.find("header", "entry-header")
    if not header:
        err(path, "缺少 header.entry-header")
        return None
    label = clean(header.find("p", "label").all_text()) if header.find("p", "label") else ""
    m = re.fullmatch(r"練習 (\d{2,}) ／ (.+)", label)
    if not m:
        err(path, f"標籤需為「練習 NN ／ 分類」，目前是「{label}」")
        return None
    info["num"], info["cat"] = int(m.group(1)), m.group(2)
    if info["cat"] not in CATEGORIES:
        err(path, f"分類「{info['cat']}」沒有登錄在 tools/categories.json")
    else:
        want = CATEGORIES[info["cat"]]["class"]
        if want not in header.classes:
            err(path, f"分類「{info['cat']}」的標頭底色類別應為 .{want}")

    h1 = root.find("h1")
    info["title"] = clean(h1.all_text()) if h1 else ""
    if len(info["title"]) > 8:
        err(path, f"標題「{info['title']}」超過 8 個字")
    ps = [c for c in header.children if c.tag == "p" and "label" not in c.classes]
    info["summary"] = clean(ps[0].all_text()) if ps else ""

    title_tag = root.find("title")
    if not title_tag or clean(title_tag.all_text()) != f"{info['title']}｜慢看筆記":
        err(path, "<title> 需為「標題｜慢看筆記」")
    desc = next((m.attrs.get("content") for m in root.find_all("meta") if m.attrs.get("name") == "description"), None)
    if desc != info["summary"]:
        err(path, "meta description 必須和摘要一字不差")

    dl = root.find("dl", "meta")
    dts = [clean(d.all_text()) for d in dl.find_all("dt")] if dl else []
    if dts != META:
        err(path, f"dl.meta 需依序有 {'、'.join(META)}，目前是 {dts}")
    else:
        info["time"] = clean(dl.find_all("dd")[0].all_text())
        tm = re.fullmatch(r"約 (\d+) 分鐘", info["time"])
        if not tm:
            err(path, f"時間格式需為「約 N 分鐘」，目前是「{info['time']}」")
        elif not 5 <= int(tm.group(1)) <= 15:
            err(path, "時間需介於 5 到 15 分鐘")

    h2s = [clean(h.all_text()) for h in root.find_all("h2")]
    if h2s != SECTIONS:
        err(path, f"H2 需依序為 {'、'.join(SECTIONS)}，目前是 {h2s}")
    steps = root.find("ol", "steps")
    if not steps or len(steps.find_all("li")) != 3:
        err(path, "練習步驟需為 ol.steps，且剛好三個步驟")
    if not root.find("section", "example"):
        err(path, "紀錄示例需放在 section.example")
    reflect = [s for s in root.find_all("section") if s.attrs.get("aria-labelledby") == "reflect"]
    if reflect and not reflect[0].all_text().endswith("？"):
        err(path, "「想一想」需以一個問句（？）結尾")

    back = root.find("a", "back")
    if not back or back.attrs.get("href") != "../index.html#notes":
        err(path, "缺少回索引連結 a.back（../index.html#notes）")

    pager = root.find("nav", "pager")
    if not pager:
        err(path, "缺少 nav.pager")
    else:
        prev, nxt = pager.find("a", "prev"), pager.find("a", "next")
        info["prev"] = prev.attrs["href"][:-5] if prev else None
        info["next"] = nxt.attrs["href"][:-5] if nxt else None
        info["prev_text"] = clean(prev.all_text()) if prev else None
        info["next_text"] = clean(nxt.all_text()) if nxt else None
    return info


def check_index(notes_by_slug):
    path = DOCS / "index.html"
    raw = path.read_text(encoding="utf-8")
    root = parse(path)
    check_common(path, root, raw)
    if "<!-- cards:end -->" not in raw:
        err(path, "ul.cards 結尾需保留 <!-- cards:end --> 標記（new_note.py 用它插入卡片）")
    cards = root.find("ul", "cards")
    if not cards:
        err(path, "缺少 ul.cards")
        return
    items = [li for li in cards.children if li.tag == "li"]
    seen = []
    for li in items:
        a = li.find("a")
        href = a.attrs.get("href", "") if a else ""
        slug = Path(href).stem
        seen.append(slug)
        note = notes_by_slug.get(slug)
        if not note:
            err(path, f"卡片 {href} 沒有對應的內頁")
            continue
        label = clean(li.find("span", "label").all_text()) if li.find("span", "label") else ""
        title = clean(li.find("h3").all_text()) if li.find("h3") else ""
        summ = clean(li.find("p").all_text()) if li.find("p") else ""
        time = clean(li.find("span", "time").all_text()) if li.find("span", "time") else ""
        if label != f"練習 {note['num']:02d} ／ {note['cat']}":
            err(path, f"{slug} 卡片標籤「{label}」和內頁不一致")
        if title != note["title"]:
            err(path, f"{slug} 卡片標題「{title}」和內頁「{note['title']}」不一致")
        if summ != note["summary"]:
            err(path, f"{slug} 卡片摘要和內頁不一致")
        if time != note.get("time"):
            err(path, f"{slug} 卡片時間「{time}」和內頁「{note.get('time')}」不一致")
        cat = note["cat"]
        if cat in CATEGORIES and CATEGORIES[cat]["class"] not in li.classes:
            err(path, f"{slug} 卡片底色類別應為 .{CATEGORIES[cat]['class']}")
    ordered = [n["slug"] for n in sorted(notes_by_slug.values(), key=lambda n: n["num"])]
    if seen != ordered:
        err(path, f"卡片順序需依編號排列，且每篇剛好一張：應為 {ordered}，目前是 {seen}")


def check_sequence(notes):
    notes = sorted(notes, key=lambda n: n["num"])
    nums = [n["num"] for n in notes]
    if nums != list(range(1, len(notes) + 1)):
        errors.append(f"docs/notes：編號需從 01 連續遞增，目前是 {nums}")
    for i, n in enumerate(notes):
        p = notes[i - 1] if i > 0 else None
        q = notes[i + 1] if i + 1 < len(notes) else None
        where = f"docs/notes/{n['slug']}.html"
        if n.get("prev") != (p["slug"] if p else None):
            errors.append(f"{where}：上一篇應指向 {p['slug'] if p else '（無）'}")
        elif p and n["prev_text"] != f"← 練習 {p['num']:02d} {p['title']}":
            errors.append(f"{where}：上一篇連結文字應為「← 練習 {p['num']:02d} {p['title']}」")
        if n.get("next") != (q["slug"] if q else None):
            errors.append(f"{where}：下一篇應指向 {q['slug'] if q else '（無）'}")
        elif q and n["next_text"] != f"練習 {q['num']:02d} {q['title']} →":
            errors.append(f"{where}：下一篇連結文字應為「練習 {q['num']:02d} {q['title']} →」")
    if notes:
        last = (NOTES / f"{notes[-1]['slug']}.html").read_text(encoding="utf-8")
        if "<!-- next -->" not in last:
            errors.append(f"docs/notes/{notes[-1]['slug']}.html：最後一篇的 pager 需保留 <!-- next --> 標記")


def check_categories():
    for name, cat in CATEGORIES.items():
        cls, color = cat["class"], cat["color"]
        if f"--{cls}: {color};" not in CSS:
            errors.append(f"docs/assets/site.css：缺少分類「{name}」的變數 --{cls}: {color};")
        if f".{cls} {{ background: var(--{cls}); }}" not in CSS:
            errors.append(f"docs/assets/site.css：缺少 .{cls} {{ background: var(--{cls}); }}")


def main():
    notes = [n for n in (check_note(p) for p in sorted(NOTES.glob("*.html"))) if n]
    by_slug = {n["slug"]: n for n in notes}
    check_sequence(notes)
    check_index(by_slug)
    about = DOCS / "about.html"
    if about.exists():
        check_common(about, parse(about), about.read_text(encoding="utf-8"))
    check_categories()
    if not (DOCS / ".nojekyll").exists():
        errors.append("docs/.nojekyll：檔案不存在")

    if errors:
        print(f"✗ {len(errors)} 個問題：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"✓ 全部通過：{len(notes)} 篇練習、{len(CATEGORIES)} 個分類、首頁卡片與上下篇連結一致")


if __name__ == "__main__":
    main()
