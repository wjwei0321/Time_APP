# 給 AI 助理（Antigravity、Codex 等）

這個專案（時序，資料夾 Time_APP）的常駐說明寫在 `CLAUDE.md`，部署、帳號與「同步方式的歷程」寫在 `DEPLOY.md`。
動手前請先讀這兩份。重點：

- 一律使用個人帳號（GitHub wjwei0321、作者 atw007wj），不要用這台電腦裡 SENSESOIL 的 token。
- 已經上線：https://timeapp-wei.vercel.app ，push 到 `main` 會自動部署，不需要手動重新部署。
- 雲端同步目前是「只輸入 email」，用 Supabase 的 `shiti_get`／`shiti_put`；不要執行舊版（`48aada2`）的 Supabase Auth SQL。
- 回覆使用者用繁體中文。
