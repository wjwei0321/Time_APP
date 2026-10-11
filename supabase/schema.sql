-- 時屜 · 雲端同步（email 登入版）
-- 在 Supabase → SQL Editor 貼上整段執行一次即可（可重複執行）。
--
-- 設計：
--   * 用 Supabase Auth 的 email＋密碼登入；每個帳號的全部資料是一筆 JSON（payload）。
--   * RLS：已登入的人只能讀寫自己那一筆（auth.uid() = user_id），沒登入（anon）完全碰不到。
--   * 2026-04 起新資料表不會自動開放給 Data API，所以下面明確 grant 給 authenticated。
--   * 與細水長流共用專案；細水長流的 budget_* 不受影響。

create table if not exists public.shiti_user_doc (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  payload    jsonb not null check (pg_column_size(payload) < 5000000),
  updated_at timestamptz not null default now()
);

alter table public.shiti_user_doc enable row level security;
revoke all on public.shiti_user_doc from anon, authenticated;
grant select, insert, update on public.shiti_user_doc to authenticated;

drop policy if exists "shiti own doc: read" on public.shiti_user_doc;
create policy "shiti own doc: read" on public.shiti_user_doc
  for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "shiti own doc: insert" on public.shiti_user_doc;
create policy "shiti own doc: insert" on public.shiti_user_doc
  for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "shiti own doc: update" on public.shiti_user_doc;
create policy "shiti own doc: update" on public.shiti_user_doc
  for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

-- 停用舊的「同步密語」入口（任何人都能呼叫的 security definer 函式）。
-- 舊資料表 shiti_doc 只有部署測試資料，保留不刪；確認不需要後可以自行 drop。
drop function if exists public.shiti_get(text);
drop function if exists public.shiti_put(text, jsonb);
