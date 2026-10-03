const j = p => fetch(p + '?t=' + Date.now()).then(r => r.ok ? r.json() : null).catch(() => null);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cls = v => v == null ? 'mut' : v >= 90 ? 'ok' : v >= 50 ? 'warn' : 'bad';
const ago = iso => { if (!iso) return 'never'; const m = Math.round((Date.now() - new Date(iso)) / 60000); return m < 60 ? m + ' min ago' : m < 2880 ? Math.round(m/60) + ' h ago' : Math.round(m/1440) + ' d ago'; };
(async () => {
  const [doms, up, seo, lh, ln, sec, tr] = await Promise.all(['domains.json','data/uptime/latest.json','data/seo/latest.json','data/lighthouse/latest.json','data/links/latest.json','data/security/latest.json','data/traffic.json'].map(j));
  const by = (d, k='results') => Object.fromEntries(((d && d[k]) || []).map(x => [x.domain, x]));
  const U = by(up), S = by(seo), L = by(lh), K = by(ln), X = by(sec);
  const list = (doms && doms.domains) || (up && up.results.map(r => ({domain: r.domain}))) || [];
  let nUp = 0;
  const rows = list.map(d => {
    const u = U[d.domain], s = S[d.domain], l = L[d.domain], k = K[d.domain], x = X[d.domain];
    if (u && u.up) nUp++;
    const st = !u ? '<span class="mut">–</span>' : u.up ? `<span class="ok"><span class="dot"></span>Up ${u.status}</span>` : `<span class="bad"><span class="dot"></span>Down ${u.status ?? ''}</span>`;
    const ms = u ? `<span class="${u.ms < 1000 ? 'ok' : u.ms < 3000 ? 'warn' : 'bad'}">${u.ms} ms</span>` : '–';
    const tls = u && u.tls_days_left != null ? `<span class="${u.tls_days_left > 21 ? 'ok' : u.tls_days_left > 7 ? 'warn' : 'bad'}">${Math.floor(u.tls_days_left)} d</span>` : '<span class="mut">–</span>';
    const sc = l && l.scores ? ['performance','accessibility','best-practices','seo'].map(c => `<span class="sc ${cls(l.scores[c])}">${l.scores[c] ?? '–'}</span>`).join('') : '<span class="mut">pending</span>';
    const se = !s ? '<span class="mut">pending</span>' : s.ok ? '<span class="ok">Pass</span>' : `<span class="bad" title="${esc(s.failed.join(', '))}">Fail (${s.failed.length})</span>`;
    const lk = !k ? '<span class="mut">pending</span>' : k.error ? '<span class="mut">n/a</span>' : k.broken.length ? `<span class="bad">${k.broken.length} broken</span>` : `<span class="ok">${k.total} ok</span>`;
    const sh = !x ? '<span class="mut">pending</span>' : (x.exposed_paths && x.exposed_paths.length) ? '<span class="bad">Exposed file!</span>' : x.ok_headers ? '<span class="ok">Pass</span>' : `<span class="warn" title="${esc(x.missing_required.join(', '))}">Missing ${x.missing_required.length}</span>`;
    const name = `<a href="https://${esc(d.domain)}/">${esc(d.domain)}</a>` + (d.locked ? ' <span class="mut" title="' + esc(d.lock_note || '') + '">(locked)</span>' : '');
    return `<tr><td>${name}</td><td>${st}</td><td>${ms}</td><td>${tls}</td><td>${sc}</td><td>${se}</td><td>${lk}</td><td>${sh}</td></tr>`;
  });
  document.querySelector('#status tbody').innerHTML = rows.join('');
  document.getElementById('summary').innerHTML = up ? `<b class="${nUp === list.length ? 'ok' : 'bad'}">${nUp}/${list.length} sites up</b> · checked ${ago(up.checked_at)}` : 'No uptime data yet.';
  document.getElementById('checked').textContent = `Uptime ${ago(up && up.checked_at)} · SEO ${ago(seo && seo.checked_at)} · Lighthouse ${ago(lh && lh.checked_at)} · Links ${ago(ln && ln.checked_at)} · Security ${ago(sec && sec.checked_at)}`;
  // traffic
  if (!tr || !tr.days) { document.getElementById('traffic-total').innerHTML = '<p class="mut">No traffic data yet.</p>'; return; }
  const days = Object.keys(tr.days).sort().slice(-14);
  const doms2 = [...new Set(days.flatMap(dd => Object.keys(tr.days[dd].domains || {})))].sort();
  const tot = dd => Object.values(tr.days[dd].domains || {}).reduce((a, v) => [a[0] + (v.visitors || 0), a[1] + (v.pageviews || 0)], [0, 0]);
  const last = days[days.length - 1], [tv, tp] = tot(last);
  document.getElementById('traffic-total').innerHTML = `<p class="summary">Latest digest (${esc(last)}): <b>${tv}</b> visitors · <b>${tp}</b> pageviews across ${doms2.length} domains. Updated ${ago(tr.updated_at)}.</p>`;
  const max = Math.max(1, ...doms2.flatMap(dm => days.map(dd => ((tr.days[dd].domains || {})[dm] || {}).pageviews || 0)));
  document.querySelector('#traffic thead').innerHTML = `<tr><th>Domain</th><th>Last ${days.length} digests (pageviews)</th><th class="num">Visitors (latest)</th><th class="num">Pageviews (latest)</th><th class="num">Pageviews (${days.length} d)</th></tr>`;
  document.querySelector('#traffic tbody').innerHTML = doms2.map(dm => {
    const pv = days.map(dd => ((tr.days[dd].domains || {})[dm] || {}).pageviews);
    const l = (tr.days[last].domains || {})[dm] || {};
    const bars = pv.map((v, i) => `<span class="bar" title="${days[i]}: ${v ?? 'n/a'}" style="height:${2 + Math.round(28 * (v || 0) / max)}px;${v == null ? 'background:#333' : ''}"></span>`).join('');
    return `<tr><td>${esc(dm)}</td><td>${bars}</td><td class="num">${l.visitors ?? '–'}</td><td class="num">${l.pageviews ?? '–'}</td><td class="num">${pv.reduce((a, v) => a + (v || 0), 0)}</td></tr>`;
  }).join('');
})();
