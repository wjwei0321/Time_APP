# 時屜（時間抽屜 App）— 給 AI 助理的常駐指示

- 回覆使用者用繁體中文。姊妹作是 `../Budget_APP`（細水長流），設計語言沿用它：字體、四色系 × 日夜、Tabler outline 圖示、元件樣式。
- git 作者沿用細水長流的個人身分 `atw007wj`（已寫在本 repo 的 .git/config）。尚未建立 GitHub／Vercel，未 push。
- 產品定義見 `PRODUCT.md`。

## 結構

| 檔案 | 說明 |
| --- | --- |
| `index.html` | 整個 App（HTML/CSS/JS，沒有 build 步驟）。圖示路徑內嵌在 `ICONS`（Tabler outline，MIT，授權見 `icons/TABLER-LICENSE.txt`） |
| `sw.js`、`manifest.webmanifest`、`icons/*.png` | PWA；圖示用 `python tools/make_icons.py` 重畫 |
| 本機預覽 | `python -m http.server 8766`；網址加 `?at=HH:MM`、`?day=YYYY-MM-DD` 可把時鐘撥到指定時間測試 |

## 資料模型（localStorage `shiti.data.v1`；外觀設定 `shiti.ui.v1`）

```
{ v:1,
  prefs: { wake, sleep, buffer(分), cap(%), notify, lead(分), closed:{ 'YYYY-MM-DD': ts|-1 } },
  drawers: [{ id, name, icon, tone:'pool'|'moss'|'amber'|'slate'|'plum'|'ink', start:'HH:MM', end, days:[1..7](1=週一), order, c, u, del? }],
  items:   [{ id, title, drawer: drawerId|'pocket', when:'every'|'next'|'YYYY-MM-DD', mins?, doneAt?, doneOn?, doneDates?:{date:ts|-1}, rolled?, c, u, del? }],
  logs:    [{ id, d, key: drawerId|'g<分鐘>', start, end (分鐘), kind:'plan'|'rest'|'other'|'leak', dr?, demo? }],
  skips:   { 'YYYY-MM-DD'+key: 1 },
  demo?: 1 }
```

- 刪除用 `del:1`，可復原。示範資料以 `demo:1`／`-1` 標記，設定頁可一鍵清除。
- 一天 = 起床到就寢；抽屜之間的空檔是「留白」（gap）。
- 過了日期沒做的指定日事項，開 App 時自動變成「下次打開」（`rolled:1`）。
- 守門規則（`drawerChecks`）：重疊＝擋下；緩衝不足、超過每日上限（七分滿）＝提醒。

## 設計

- 主視覺是「此刻的抽屜」：面板＋把手＋拉出來的內盒（`.face`/`.pull`/`.tray`），內盒打開的動畫是唯一的招牌動作。
- 朱色＝超量／流失；金色＝用心留白。
- 色系屬性是 `data-palette`（不是 `data-theme`，因為嵌在 Artifact 時外層會蓋 `data-theme=light|dark`）。
- 網頁無法在關閉後排程通知：通知只在 App 開著時有效，可靠提醒靠匯出 .ics 到手機行事曆。
