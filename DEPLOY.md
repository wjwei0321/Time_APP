# 部署指示：時屜（Time_APP）→ GitHub + Supabase + Vercel

> ✅ 已於 2026-10-11 完成：GitHub push、Vercel 自動部署、Supabase schema、正式網址 https://timeapp-wei.vercel.app 雲端同步實測成功。以下保留做為重建參考。

## 目前狀態（給接手的 AI 助理，例如 Antigravity）— 2026-10-11

**已全部上線，不需要重新部署或重跑 SQL。** push 到 `main` 就會自動部署。

| 部分 | 現況 |
| --- | --- |
| 前端 | `index.html`＋`quotes.js`，靜態檔，Vercel 直接提供 |
| 雲端同步 | **只輸入 email**（不用密碼、不寄信）。App 算 `SHA-256("shiti:" + 小寫 email)` 當 id，呼叫 Supabase RPC `shiti_get(p_id)`／`shiti_put(p_id, p_payload)`。資料在 `public.shiti_doc`（RLS 開、無 policy，只能經由這兩個函式） |
| 行事曆 | Vercel 函式 `api/ics.js`：`/api/ics?id=<同上 id>&tz=Asia/Taipei` 回傳行事曆，App 用 `webcal://` 訂閱。id 沒有資料時回 404、格式錯回 400，屬正常 |
| Supabase 物件 | 現存：`shiti_doc` 資料表、`shiti_get`、`shiti_put`。另有細水長流的 `budget_*`，不要動 |

### 同步方式的歷程（看 git log 會看到這些，免得誤會）

1. `2cb7498`：先做「同步密語」（使用者輸入一組密語）。資料庫部分就是現在的 `supabase/schema.sql`，**已在 Supabase 執行過**。
2. `48aada2`：改成 Supabase Auth email＋密碼登入（資料表 `shiti_user_doc`）。**這版的 SQL 從來沒有在 Supabase 執行過**，使用者嫌確認信麻煩。
3. `2d40fa0`：改回第 1 版的資料庫做法，只是把「密語」換成「email」。資料庫不用動。

所以：
- **不要**再執行 `48aada2` 版本的 SQL（會刪掉正在使用的 `shiti_get`／`shiti_put`）。
- **不要**建立 `shiti_user_doc`、不要開 Supabase Auth 的設定，現在用不到。
- `shiti_doc` 裡有幾筆部署測試資料（`deploy-check-…`、`sync-test-…@example.com`、`ics-test@example.com` 算出來的 id），沒有人會用到，可以留著。

> 個人專案，一律使用與細水長流（`../Budget_APP`）相同的個人帳號，不是公司「拾壤／SENSESOIL」帳號。
> 這台電腦的 `~/.git-credentials` 裡只有 SENSESOIL 的 token，**不要用它推這個 repo**。

## 0. 帳號與目標

| 項目 | 值 |
| --- | --- |
| 專案資料夾 | `C:\Users\User\.antigravity\Time_APP` |
| GitHub 帳號 | **wjwei0321** |
| GitHub repo | `https://github.com/wjwei0321/Time_APP`（目前 Public；可在 Settings → General 改為 Private，不影響部署） |
| 本機 git 身分 | `atw007wj <atw007wj@gmail.com>`（已寫進這個 repo 的 `.git/config`） |
| remote | `origin = https://wjwei0321@github.com/wjwei0321/Time_APP.git`（已設定，推送時由 Git Credential Manager 使用 wjwei0321 的登入） |
| 分支 | `main` |
| Vercel | 帳號 atw007wj，team **WEI（wei-08fb）**，project **time_app**，連到上面的 repo |
| 正式網址 | **https://timeapp-wei.vercel.app** |
| Supabase | 帳號 wjwei0321，**與細水長流共用 project Work&Life_Balance**（原名 Budget_APP，ref `tbukohrgpxxhmtsqgzon`，Tokyo）。時屜用 `shiti_doc`／`shiti_get`／`shiti_put`，與 `budget_*` 互不影響。同步以 email 當識別碼：id = SHA-256("shiti:"+小寫 email)，不寄信、不用密碼（使用者選擇的簡便做法；知道 email 的人理論上能讀寫這份資料） |

### 帳號檢查（每次推送前）

```powershell
git config user.email     # 必須是 atw007wj@gmail.com
git remote -v             # 必須是 https://wjwei0321@github.com/wjwei0321/Time_APP.git
```

## 1. GitHub

1. 以 wjwei0321 登入 → https://github.com/new → Repository name `Time_APP`、**Private**、不要勾 README／.gitignore／license。
2. `git push -u origin main`（Windows 認證視窗若跳出，登入 **wjwei0321**）。

## 2. Supabase

1. 不另開專案（免費方案有專案數上限），使用 Work&Life_Balance：https://supabase.com/dashboard/project/tbukohrgpxxhmtsqgzon/sql/new
2. SQL Editor 貼上 `supabase/schema.sql` → Run（顯示 `Success. No rows returned`）。
3. `index.html` 的 `CONFIG` 與 `api/ics.js` 已填入這個專案的網址與 publishable key。
4. 驗證：

```powershell
curl.exe -s -X POST "https://tbukohrgpxxhmtsqgzon.supabase.co/rest/v1/rpc/shiti_get" -H "apikey: KEY" -H "Content-Type: application/json" -d "{\"p_id\":\"0000000000000000000000000000000000000000000000000000000000000000\"}"
```

回傳 `null` 代表成功。

## 3. Vercel

以 atw007wj 登入 → team WEI → Add New Project → Import `wjwei0321/Time_APP`：

| 設定 | 值 |
| --- | --- |
| Project Name | `time_app` |
| Framework Preset | **Other** |
| Root Directory | `./` |
| Build / Output / Install Command | 全部留空 |
| Environment Variables | 不需要 |

push 到 `main` 就會自動部署。正式網址 `https://timeapp-wei.vercel.app`（Project → Settings → Domains）。注意 `time-app.vercel.app` 是別人的網站。

## 4. 驗收

1. 打開正式網址 → 出現「時屜」歡迎畫面。
2. 設定 → 資料 → 用 email 同步 → 輸入 email（第一次要按兩次確認）→ 狀態變成「已同步」。
3. 手機開同一網址，在歡迎畫面按「已經在別台裝置用過？登入」→ 輸入同一個 email → 資料出現。
4. 手機 Safari「分享 → 加入主畫面」。
