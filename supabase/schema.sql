-- 時屜 · 時間抽屜 App 的雲端同步資料表
-- 在 Supabase → SQL Editor 貼上整段執行一次即可（可重複執行）。
--
-- 設計：
--   * 每個使用者的全部資料是一筆 JSON（payload），id = SHA-256("shiti:" + 小寫 email)（email 只當識別碼，不寄信、不用密碼）。
--   * 資料表開啟 RLS 且「沒有任何 policy」，anon key 無法直接讀寫資料表。
--   * 只能透過下面兩個 security definer 函式存取，而且必須知道 id（＝知道 email）。
--     所以就算網址與 publishable key 公開，不知道 email 就看不到資料（email 不是祕密，安全性等同一組公開程度較高的密語）。

create table if not exists public.shiti_doc (
  id         text primary key check (char_length(id) = 64),
  payload    jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.shiti_doc enable row level security;
revoke all on public.shiti_doc from anon, authenticated;

create or replace function public.shiti_get(p_id text)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  select payload from public.shiti_doc where id = p_id;
$$;

create or replace function public.shiti_put(p_id text, p_payload jsonb)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if char_length(p_id) <> 64 then
    raise exception 'invalid id';
  end if;
  if pg_column_size(p_payload) > 5000000 then
    raise exception 'payload too large';
  end if;
  insert into public.shiti_doc (id, payload, updated_at)
  values (p_id, p_payload, now())
  on conflict (id) do update
    set payload = excluded.payload,
        updated_at = now();
end;
$$;

revoke all on function public.shiti_get(text) from public;
revoke all on function public.shiti_put(text, jsonb) from public;
grant execute on function public.shiti_get(text) to anon, authenticated;
grant execute on function public.shiti_put(text, jsonb) to anon, authenticated;
