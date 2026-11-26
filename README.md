# 慢看筆記

一張紙、一支筆，五到十五分鐘，在熟悉的地方重新觀察光線、聲音、觸感、顏色和節奏。

- 🌐 網站：<https://10969ethan.github.io/slow-look-notes/>
- 🤖 AI 開發規則：[AGENTS.md](AGENTS.md)（Claude Code 透過 [CLAUDE.md](CLAUDE.md) 讀取同一份）
- 🎨 統一風格圖像生成 Agent（另一份作業）：[style-agent/](style-agent/)
- 🛠 製作方式與新增紀錄：[docs/about.html](https://10969ethan.github.io/slow-look-notes/about.html)

## 這個專案的重點

這不只是一個網站，而是一套**讓 AI 能持續長出新頁面的規則**：

| 零件 | 檔案 | 作用 |
| --- | --- | --- |
| 規則 | `AGENTS.md` | 目的、語氣、頁面結構、寫作規則表、命名、分類、完成條件 |
| 範本 | `templates/note.html` | 每篇練習的固定骨架 |
| 分類登錄表 | `tools/categories.json` | 分類 → CSS 類別與色碼的唯一來源 |
| 產生器 | `tools/new_note.py` | 自動編號、上下篇連結、插入首頁卡片 |
| 檢查器 | `tools/check.py` | 把規則變成自動檢查；GitHub Actions 每次 push 都跑 |

第一版只有 01、02 兩篇；03–05 是只給 AI 一句指令，照 AGENTS.md 新增的（含一個新分類「節奏」），過程記錄在製作方式頁。

## 新增一篇練習

```bash
python3 tools/new_note.py texture-trail 觸感   # 1. 建骨架
# 2. 依 AGENTS.md 第 5 節填內容與首頁卡片
python3 tools/check.py                         # 3. 檢查到全部通過
```

或直接對 AI 說：「依照 AGENTS.md 新增一篇『氣味』練習：在廚房分辨三種氣味的強弱。」

## 本機預覽

直接用瀏覽器開啟 `docs/index.html`，或執行 `python3 -m http.server -d docs 8000`。

## 發布

GitHub Pages：**Settings → Pages → Deploy from a branch → `main` / `/docs`**。
