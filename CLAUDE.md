# 時序（時間抽屜 App，專案資料夾 Time_APP）— 給 AI 助理的常駐指示

- 回覆使用者用繁體中文。姊妹作是 `../Budget_APP`（細水長流），設計語言沿用它：字體、長流橘單一色系 × 日夜、Tabler outline 圖示、元件樣式。
- 帳號一律個人：GitHub `wjwei0321/Time_APP`、Vercel team WEI／project time_app（正式網址 https://timeapp-wei.vercel.app）、Supabase 與細水長流共用 project Work&Life_Balance（ref `tbukohrgpxxhmtsqgzon`，時序用 `shiti_doc`＋`shiti_get/put`；同步以 email 當識別碼，不寄信、不用密碼，使用者明確選擇此做法）。git 作者 `atw007wj`；push 到 main 會自動部署。細節見 `DEPLOY.md`。
- 不要用這台電腦 `~/.git-credentials` 裡的 SENSESOIL token。
- 產品定義見 `PRODUCT.md`。

## 結構

| 檔案 | 說明 |
| --- | --- |
| `index.html` | 整個 App（HTML/CSS/JS，沒有 build 步驟）。圖示路徑內嵌在 `ICONS`（Tabler outline，MIT，授權見 `icons/TABLER-LICENSE.txt`） |
| `quotes.js` | 每日一句，730 句（主題：格局、視野、激勵、成長心態、溝通、善、謙遜、情商、情緒管理、正念、系統觀、成功者思維、認知、運動家；約兩成來自納瓦爾、巴菲特、蒙格、賈伯斯、馬斯克、黃仁勳、稻盛和夫、郝旭烈、Ryan Leak）：早上（04:00–15:59）`QUOTES`、傍晚以後（16:00–隔天 03:59）`QUOTES_PM` 各 365 句，依一年中的第幾天輪替（中文原文附英譯、英文原文附中譯、其他語言只放中英譯＋出處地區） |
| `audio/` | 英文發音音檔：`s/<英文句 SHA-1 前 12 碼>.mp3`（730 句）、`w/<單字>.mp3`（2,163 字）、`index.json`。用 Kokoro 開源神經語音（Apache-2.0，聲音 af_heart）預先產生：`python tools/make_audio.py --budget 540`（可重複執行，會接著做；改金句後再跑一次，舊句子的檔案會自動刪除）。模型放在 `~/.cache/kokoro/`，不進 repo |
| `glossary.js` | 金句裡所有英文單字的中文解釋（點單字時顯示）。由 `tools/gloss_*.txt` 經 `python tools/build_glossary.py` 產生；改金句後要重跑，它會列出缺的字 |
| `api/ics.js` | Vercel 函式：`/api/ics?id=<同步 id>&tz=` 依雲端資料產生行事曆訂閱（webcal），iPhone 主畫面 App 不能下載檔案，所以用訂閱取代 .ics 下載 |
| `sw.js`、`manifest.webmanifest`、`icons/*.png` | PWA；圖示用 `python tools/make_icons.py` 重畫 |
| 本機預覽 | `python -m http.server 8766`；網址加 `?at=HH:MM`、`?day=YYYY-MM-DD` 可把時鐘撥到指定時間測試 |

## 資料模型（localStorage `shiti.data.v1`；外觀設定 `shiti.ui.v1`）

```
{ v:1,
  prefs: { wake, sleep, buffer(分), cap(%), notify, lead(分), closed:{ 'YYYY-MM-DD': ts|-1 } },
  drawers: [{ id, name, icon, tone:'pool'|'moss'|'amber'|'slate'|'plum'|'ink', start:'HH:MM', end, days:[1..7](1=週一), order, c, u, del? }],
  items:   [{ id, title, drawer: drawerId|'pocket', when:'every'|'next'|'YYYY-MM-DD', mins?, ask?, hint?, doneAt?, doneOn?, doneDates?:{date:ts|-1}, rolled?, c, u, del? }],
  logs:    [{ id, d, key: drawerId|'g<分鐘>', start, end (分鐘), kind:'plan'|'rest'|'other'|'leak', dr?, demo? }],
  plans:   [{ id, d, start(分鐘), mins, title, item?: 留白清單事項 id, done?, demo? }],   // 排進某段留白的事
  recs:    [{ id, d, at(分鐘), title, item?, plan?, drawer?, note, demo? }],          // 完成紀錄（時間＋細節，例如讀到第幾頁）
  goals:   [{ id, title, core, doneAt?, drawer?, demo? }],   // 人生清單（目標 50 件），core＝核心目標（最多 10 個）
  vision:  { text, at },                                      // 五年後的你
  top3:    { 'YYYY-MM-DD': [itemId…] },                       // 今天的三件事
  // items 另有 goal?（對應目標）、week?（那一週的週一）
  skips:   { 'YYYY-MM-DD'+key: 1 },
  demo?: 1 }
```

- 舊資料在開 App 時由 `migrate()` 補欄位。
- 打勾完成會產生一筆 `recs`；`ask` 為真（或標題像讀書、運動）時會跳出「記下這一次」讓使用者寫細節，並提供「接著上次」。
- 刪除用 `del:1`，可復原。示範資料以 `demo:1`／`-1` 標記，設定頁可一鍵清除。
- 一天 = 起床到就寢；抽屜之間的空檔是「留白」（gap）。
- 過了日期沒做的指定日事項，開 App 時自動變成「下次打開」（`rolled:1`）。
- 守門規則（`drawerChecks`）：重疊＝擋下；緩衝不足、超過每日上限（七分滿）＝提醒。

## 設計

- 主視覺是「此刻的抽屜」：面板＋把手＋拉出來的內盒（`.face`/`.pull`/`.tray`）。面板裡的水位（`.liquid`，沿用細水長流）＝這段還剩多少時間，會隨時間下降。
- 每次打開 App（以及離開超過 30 分鐘、或換日後回來）都先出現滿版「今日一句」，只有金句，按右下角 > 才進入（`showDawn`）。英文單字可點：顯示中文解釋（`GLOSS`，找不到原字會試著去掉 s/ed/ing 等）、音標與英文釋義（dictionaryapi.dev，查不到不影響），發音優先播放 `audio/` 的音檔（像真人說話），沒有音檔才退回瀏覽器內建語音；底部「英文發音」播放整句並標出唸到的字（依進度比例估算）。只有英文發音，沒有中文朗讀。今天頁不再放金句卡。
- 單一色系「長流橘」（與長流、細水同一個橘 #F2711C，App 圖示也是橘底）× 白天／夜晚，預設跟系統；設定裡用圖示切換（半圓＝跟系統、太陽、月亮），不提供色系選擇。超量／流失用覆盆子紅、留白用金色（偏黃褐，和橘色分得開）。
- 朱色＝超量／流失；金色＝用心留白。
- 已經沒有色系屬性；只有 `data-mode`（嵌在 Artifact 時外層的 `data-theme=light|dark` 在「跟系統」時會被採用）。
- 網頁無法在關閉後排程通知：通知只在 App 開著時有效，可靠提醒靠行事曆訂閱（`api/ics.js`，需先用 email 同步）。

## 目標（王永福「便利貼思考法」簡化版，來源：Cheers 2023-07-15）

- 每年問「五年後的我會是什麼樣子」→ 人生清單寫到 50 件 → 選出核心 10 個 → 每週替核心目標安排行動（直接變成抽屜或留白清單裡的事項，`goal`＋`week`）→ 每天挑 3 件（`top3`）。
- 週日安排的是下週（`planWeek()`），其他天是這週。週日、週一若還沒安排，今天頁會提醒。
- 導覽列第四格是「目標」；留白清單併到「抽屜」頁的切換（`UI.tab = 'pocket'` 仍可用）。
