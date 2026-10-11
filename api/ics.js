// 行事曆訂閱：/api/ics?id=<同步 id>
// iPhone／Mac 行事曆用 webcal:// 訂閱、Google 日曆用「從網址新增」。抽屜改了，行事曆會在下次重新整理時自動更新。
// 資料來源是雲端同步的那一份（Supabase shiti_get），所以要先在 App 裡用 email 同步。
const SUPA_URL = 'https://tbukohrgpxxhmtsqgzon.supabase.co';
const SUPA_KEY = 'sb_publishable_naaPTzV6pdPoiTctKsiShg_VJQqsXCs';  // publishable key，公開也安全
const BY = ['', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];

const esc = s => String(s).replace(/[\\;,]/g, m => '\\' + m).replace(/\r?\n/g, '\\n');
// 每行最多 75 bytes，超過要折行（行事曆規格 RFC 5545）
function fold(line) {
  const out = []; let cur = '', bytes = 0;
  for (const ch of line) {
    const b = Buffer.byteLength(ch);
    if (bytes + b > (out.length ? 74 : 75)) { out.push(cur); cur = ''; bytes = 0; }
    cur += ch; bytes += b;
  }
  out.push(cur);
  return out.join('\r\n ');
}
function todayIn(tz) {
  try { return new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); }
  catch (e) { return new Date().toISOString().slice(0, 10); }
}

module.exports = async (req, res) => {
  const id = String(req.query.id || '');
  if (!/^[0-9a-f]{64}$/.test(id)) { res.status(400).send('missing or invalid id'); return; }
  const tz = String(req.query.tz || 'Asia/Taipei');
  let doc = null;
  try {
    const r = await fetch(`${SUPA_URL}/rest/v1/rpc/shiti_get`, { method: 'POST', headers: { apikey: SUPA_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ p_id: id }) });
    if (!r.ok) throw new Error(String(r.status));
    doc = await r.json();
  } catch (e) { res.status(502).send('cannot reach database'); return; }
  if (!doc || doc.v !== 1) { res.status(404).send('no synced data for this id'); return; }

  const live = a => (a || []).filter(x => !x.del);
  const lead = (doc.prefs && doc.prefs.lead) || 0;
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
  const t0 = todayIn(tz);
  const L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Shiti//ZH-TW', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
    'X-WR-CALNAME:時屜', `X-WR-TIMEZONE:${tz}`, 'REFRESH-INTERVAL;VALUE=DURATION:PT4H', 'X-PUBLISHED-TTL:PT4H'];
  for (const x of live(doc.drawers)) {
    if (!x.days || !x.days.length || !/^\d{1,2}:\d{2}$/.test(x.start) || !/^\d{1,2}:\d{2}$/.test(x.end)) continue;
    // 第一次打開的日期：從今天起第一個符合的星期
    const d = new Date(t0 + 'T00:00:00Z');
    for (let k = 0; k < 7 && !x.days.includes(d.getUTCDay() || 7); k++) d.setUTCDate(d.getUTCDate() + 1);
    const ds = d.toISOString().slice(0, 10).replace(/-/g, ''), hhmm = t => t.padStart(5, '0').replace(':', '');
    const items = live(doc.items).filter(it => it.drawer === x.id && it.when === 'every').map(it => '・' + it.title).join('\n');
    L.push('BEGIN:VEVENT', `UID:${x.id}@shiti`, `DTSTAMP:${stamp}`, `DTSTART:${ds}T${hhmm(x.start)}00`, `DTEND:${ds}T${hhmm(x.end)}00`,
      `RRULE:FREQ=WEEKLY;BYDAY=${x.days.map(w => BY[w]).join(',')}`, `SUMMARY:${esc('抽屜｜' + x.name)}`, `DESCRIPTION:${esc(items || '打開時屜，看看抽屜裡有什麼。')}`,
      'BEGIN:VALARM', 'ACTION:DISPLAY', `DESCRIPTION:${esc(`「${x.name}」打開了`)}`, `TRIGGER:${lead ? `-PT${lead}M` : 'PT0S'}`, 'END:VALARM', 'END:VEVENT');
  }
  L.push('END:VCALENDAR');
  res.setHeader('Content-Type', 'text/calendar; charset=utf-8');
  res.setHeader('Content-Disposition', 'inline; filename="shiti.ics"');
  res.setHeader('Cache-Control', 'public, max-age=300');
  res.status(200).send(L.map(fold).join('\r\n') + '\r\n');
};
