# 慢看筆記

用一張紙和一支筆重新觀察身邊的光線與聲音。首頁收錄兩個原創練習「追一小段影子」和「畫一張聲音地圖」。兩篇都依序呈現觀察目標、三個步驟、紀錄示例和一個反思問題。

- [首頁](docs/index.html)
- [AI 開發指南](AGENTS.md)
- [內容頁範本](templates/note.html)

## 本機預覽

直接用瀏覽器開啟 `docs/index.html`。首頁可連到兩篇練習，兩篇都能回到首頁索引。

## GitHub Pages 發布

1. 建立公開 GitHub repository，例如 `slow-look-notes`，將本資料夾內的所有檔案上傳至預設分支，讓 `AGENTS.md` 和 `docs/` 位於 repository 根目錄。上傳後確認 `docs/.nojekyll` 也在。
2. 在 repository 的 **Settings → Pages**，將 **Source** 選為 **Deploy from a branch**。選預設分支（通常為 `main`）和 **/docs**，再按 **Save**。
3. 等待部署成功。從 **Settings → Pages → Visit site** 開啟網站，確認兩張卡片、文章樣式和返回索引連結都正常。繳交時使用實際的 repository 網址與 Pages 網址。

[GitHub Pages 官方設定說明](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## 新增內容

把 [AGENTS.md](AGENTS.md) 交給 AI，指定想新增的觀察主題。AI 可複製範本、填寫四節、依規則命名、更新首頁卡片，最後驗證來回連結。兩篇現有練習共用版型，可用來比對新增頁面的結構和風格。
