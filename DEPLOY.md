# 部署指示：時屜（Time_APP）→ GitHub + Supabase + Vercel

> 個人專案，一律使用與細水長流（`../Budget_APP`）相同的個人帳號，不是公司「拾壤／SENSESOIL」帳號。
> 這台電腦的 `~/.git-credentials` 裡只有 SENSESOIL 的 token，**不要用它推這個 repo**。

## 0. 帳號與目標

| 項目 | 值 |
| --- | --- |
| 專案資料夾 | `C:\Users\User\.antigravity\Time_APP` |
| GitHub 帳號 | **wjwei0321** |
| GitHub repo | `https://github.com/wjwei0321/Time_APP`（**Private**） |
| 本機 git 身分 | `atw007wj <atw007wj@gmail.com>`（已寫進這個 repo 的 `.git/config`） |
| remote | `origin = https://wjwei0321@github.com/wjwei0321/Time_APP.git`（已設定，推送時由 Git Credential Manager 使用 wjwei0321 的登入） |
| 分支 | `main` |
| Vercel | 帳號 atw007wj，team **WEI（wei-08fb）**，project **time_app**，連到上面的 repo |
| Supabase | 帳號 wjwei0321，project **Time_APP**（Tokyo）。免費方案每個組織最多 2 個執行中的專案；若額度不夠，改在細水長流的專案（`tbukohrgpxxhmtsqgzon`）執行 `supabase/schema.sql`，資料表與函式名稱（`shiti_*`）不會互相衝突 |

### 帳號檢查（每次推送前）

```powershell
git config user.email     # 必須是 atw007wj@gmail.com
git remote -v             # 必須是 https://wjwei0321@github.com/wjwei0321/Time_APP.git
```

## 1. GitHub

1. 以 wjwei0321 登入 → https://github.com/new → Repository name `Time_APP`、**Private**、不要勾 README／.gitignore／license。
2. `git push -u origin main`（Windows 認證視窗若跳出，登入 **wjwei0321**）。

## 2. Supabase

1. 以 wjwei0321 登入 → New project → 名稱 `Time_APP`、Region **Northeast Asia (Tokyo)**。
2. SQL Editor 貼上 `supabase/schema.sql` → Run（顯示 `Success. No rows returned`）。
3. Settings → API Keys → 複製 **Publishable key**（`sb_publishable_` 開頭，**不要用 secret／service_role**）。
4. 填進 `index.html` 的 `CONFIG.SUPA_URL`、`CONFIG.SUPA_KEY`，commit。
5. 驗證：

```powershell
curl.exe -s -X POST "https://<ref>.supabase.co/rest/v1/rpc/shiti_get" -H "apikey: KEY" -H "Content-Type: application/json" -d "{\"p_id\":\"0000000000000000000000000000000000000000000000000000000000000000\"}"
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

push 到 `main` 就會自動部署。正式網址預計 `https://time-app-wei.vercel.app`（在 Project → Settings → Domains 設定）。

## 4. 驗收

1. 打開正式網址 → 出現「時屜」歡迎畫面。
2. 設定 → 雲端同步 → 輸入 8 字以上的同步密語 → 狀態變成「已同步」。
3. 手機開同一網址、輸入同一組密語 → 裝置代碼相同、資料一致。
4. 手機 Safari「分享 → 加入主畫面」。
