/* SUPPORT THE DEV: the shared monthly-goal pop-up for every BigPic site (bigpicsolutions.com/support/support.js).
   Add <script src="https://bigpicsolutions.com/support/support.js" defer></script> to a page; any element with
   data-support-open (or a link to #support) opens it, and a floating button appears if the page has none.
   support.json (next to this file) holds the payment addresses + the fallback totals; the live totals come from Pulse.
   Real numbers only: a failed load says so, never "$0". */
(() => {
  if (window.__bpSupportLoaded) return;
  window.__bpSupportLoaded = true;
  // Everything is resolved relative to this script, so the same files serve every BigPic site.
  const SRC = (document.currentScript && document.currentScript.src) || '';
  const BASE = SRC ? new URL('./', SRC).href : 'https://bigpicsolutions.com/support/';
  const LIVE = 'https://pulse.bigpicsolutions.com/v1/support';
  const DIALOG_HTML = `<dialog class="bp-support" id="bp-support" aria-labelledby="support-h">
<form method="dialog" class="x-form"><button class="x" aria-label="Close">&times;</button></form>
<div class="sheet">
    <h2 id="support-h">SUPPORT THE DEV</h2>
    <p class="goal">MONTHLY INCOME GOAL &middot; <b id="sGoal">$3,000</b></p>
    <span class="badge" id="sBadge">&nbsp;</span>
    <p class="why">I&rsquo;m an independent developer building free games and tools through BigPic Solutions, and I&rsquo;m open about it: every dollar I earn this month counts toward this goal, from tips like yours to my tech work for clients.</p>
    <p class="note">Same creative journey. Brighter tomorrow.</p>
    <p class="status" id="sStatus" role="status">Loading the latest numbers&hellip;</p>

    <div class="meters">
      <div class="meter week">
        <div class="row"><span class="name">This week</span><span class="pct" data-k="pct">&nbsp;</span></div>
        <p class="target"><span data-k="range">&nbsp;</span> &middot; target <span data-k="goal">&nbsp;</span></p>
        <p class="raised"><b data-k="got">&nbsp;</b> received</p>
        <div class="meter-bar" role="progressbar" aria-label="This week" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>
        <div class="foot2"><span><span data-k="goal">&nbsp;</span> goal</span><span data-k="left">&nbsp;</span></div>
      </div>
      <div class="meter month">
        <div class="row"><span class="name">This month</span><span class="pct" data-k="pct">&nbsp;</span></div>
        <p class="target"><span data-k="range">&nbsp;</span> &middot; target <span data-k="goal">&nbsp;</span></p>
        <p class="raised"><b data-k="got">&nbsp;</b> received</p>
        <div class="meter-bar" role="progressbar" aria-label="This month" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>
        <div class="foot2"><span><span data-k="goal">&nbsp;</span> goal</span><span data-k="left">&nbsp;</span></div>
      </div>
    </div>

    <div class="miles">
      <div class="name">Monthly milestones</div>
      <div class="track"><span class="fill"></span>
        <div class="stop" data-pct="25"><span class="dot"><svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg><svg class="st" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3.2l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6-4.5-4.2 6.1-.7z"/></svg></span><span class="p">25%</span><span class="d">&nbsp;</span></div>
        <div class="stop" data-pct="50"><span class="dot"><svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg><svg class="st" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3.2l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6-4.5-4.2 6.1-.7z"/></svg></span><span class="p">50%</span><span class="d">&nbsp;</span></div>
        <div class="stop" data-pct="75"><span class="dot"><svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg><svg class="st" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3.2l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6-4.5-4.2 6.1-.7z"/></svg></span><span class="p">75%</span><span class="d">&nbsp;</span></div>
        <div class="stop" data-pct="100"><span class="dot"><svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg><svg class="st" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3.2l2.6 5.6 6.1.7-4.5 4.2 1.2 6-5.4-3-5.4 3 1.2-6-4.5-4.2 6.1-.7z"/></svg></span><span class="p">100%</span><span class="d">&nbsp;</span></div>
      </div>
    </div>

    <div class="give">
      <p class="ask">If you want to help, <b>tips move the bar.</b> A dollar, ten, twenty: whatever you think it&rsquo;s worth.</p>
      <div class="card-row">
        <a class="btn off" id="sCard" aria-disabled="true">TIP BY CARD OR PAYPAL</a>
        <span class="sub" id="sCardSub">Card tips are coming soon.</span>
      </div>
      <p class="crypto-h">Or tip in crypto</p>
      <div class="coins">
        <details class="coin" data-coin="btc"><summary><span class="c-name">Bitcoin</span><span class="c-net">BTC &middot; Bitcoin network</span><span class="c-go">Coming soon</span></summary><div class="c-body"></div></details>
        <details class="coin" data-coin="sol"><summary><span class="c-name">Solana</span><span class="c-net">SOL &middot; Solana network</span><span class="c-go">Coming soon</span></summary><div class="c-body"></div></details>
        <details class="coin" data-coin="usdc_sol"><summary><span class="c-name">USDC</span><span class="c-net">USDC &middot; Solana network</span><span class="c-go">Coming soon</span></summary><div class="c-body"></div></details>
        <details class="coin" data-coin="eth"><summary><span class="c-name">Ethereum</span><span class="c-net">ETH &middot; Ethereum mainnet</span><span class="c-go">Coming soon</span></summary><div class="c-body"></div></details>
        <details class="coin" data-coin="near"><summary><span class="c-name">NEAR</span><span class="c-net">NEAR &middot; NEAR Protocol</span><span class="c-go">Coming soon</span></summary><div class="c-body"></div></details>
      </div>
      <p class="fine">Tips are voluntary support for an independent developer, not tax-deductible charitable donations. The goal counts money actually received (tips and paid client work) before fees and taxes, less refunds. Crypto counts at its US dollar value on the day it arrives. Times are Pacific.</p>
    </div>
</div>
</dialog>`;
  const ready = (fn) => (document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', fn, { once: true }) : fn());
  ready(() => {
  if (!document.querySelector('link[data-support-css]')) {
    const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = BASE + 'support.css'; css.setAttribute('data-support-css', ''); document.head.appendChild(css);
  }
  if (!/fonts\.googleapis\.com[^"']*Cinzel/.test(document.head.innerHTML)) {            // the dialog's two fonts, if the host page doesn't already load them
    const f = document.createElement('link'); f.rel = 'stylesheet'; f.href = 'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap'; document.head.appendChild(f);
  }
  document.body.insertAdjacentHTML('beforeend', DIALOG_HTML);
  const dlg = document.getElementById('bp-support');
  const $ = (sel, el = dlg) => el.querySelector(sel);
  const MON = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const SHORT = MON.map((m) => m.slice(0, 3));
  const money = (n) => '$' + (Math.round(n * 100) % 100 ? n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : Math.round(n).toLocaleString('en-US'));
  const num = (v) => (typeof v === 'number' && isFinite(v) ? v : null);
  const ymd = (v) => { const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(String(v || '')); if (!m) return null; const y = +m[1], mo = +m[2], d = m[3] ? +m[3] : 1;
    return mo >= 1 && mo <= 12 && d >= 1 && d <= 31 ? { y, mo, d } : null; };
  const day = (o) => SHORT[o.mo - 1] + ' ' + o.d;
  // the coins: what the QR code carries (USDC rides Solana Pay with the official USDC mint so wallets pick the right token)
  const USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
  const COINS = {
    btc: { warn: 'Send Bitcoin on the Bitcoin network only.', uri: (a) => 'bitcoin:' + a, ok: (a) => /^(bc1[02-9ac-hj-np-z]{11,87}|[13][1-9A-HJ-NP-Za-km-z]{25,34})$/i.test(a) },
    sol: { warn: 'Send SOL on the Solana network only.', uri: (a) => 'solana:' + a, ok: (a) => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(a) },
    usdc_sol: { warn: 'Send USDC on the Solana network only (not Ethereum).', uri: (a) => 'solana:' + a + '?spl-token=' + USDC_MINT, ok: (a) => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(a) },
    eth: { warn: 'Send ETH on Ethereum mainnet only (not other networks).', uri: (a) => 'ethereum:' + a, ok: (a) => /^0x[0-9a-fA-F]{40}$/.test(a) },
    near: { warn: 'Send NEAR on NEAR Protocol only.', uri: (a) => a, ok: (a) => /^([a-z0-9_-]+\.)*[a-z0-9_-]+(\.near)?$|^[0-9a-f]{64}$/.test(a) && a.length >= 2 && a.length <= 64 },
  };

  function meter(el, got, goal, range) {
    const pct = goal > 0 ? (got / goal) * 100 : 0, vis = Math.max(0, Math.min(100, pct));
    el.querySelectorAll('[data-k="goal"]').forEach((n) => (n.textContent = money(goal)));
    $('[data-k="range"]', el).textContent = range;
    $('[data-k="got"]', el).textContent = money(got);
    $('[data-k="left"]', el).textContent = got >= goal ? money(got - goal) + ' over goal' : money(goal - got) + ' to go';
    $('[data-k="pct"]', el).textContent = Math.floor(pct) + '%';
    $('.meter-bar', el).setAttribute('aria-valuenow', String(Math.floor(vis)));
    $('.meter-bar i', el).style.width = vis + '%';
  }

  function payments(pay) {
    const card = $('#sCard'), sub = $('#sCardSub');
    if (typeof pay.card === 'string' && /^https:\/\/ko-fi\.com\/[A-Za-z0-9_]+\/?$/.test(pay.card)) {
      card.href = pay.card; card.target = '_blank'; card.rel = 'noopener'; card.classList.remove('off'); card.removeAttribute('aria-disabled');
      sub.textContent = 'Opens my Ko-fi page (card or PayPal). You choose the amount, from $5.';
    } else { card.removeAttribute('href'); card.classList.add('off'); card.setAttribute('aria-disabled', 'true'); sub.textContent = 'Card tips are coming soon.'; }
    dlg.querySelectorAll('.coin').forEach((c) => {
      const key = c.dataset.coin, spec = COINS[key], a = typeof pay[key] === 'string' ? pay[key].trim() : '';
      const live = !!a && spec.ok(a);
      if (c.dataset.addr === (live ? a : '')) return;                      // unchanged: keep it as it is (open or closed)
      c.dataset.addr = live ? a : ''; c.open = false; c.classList.toggle('off', !live);
      $('.c-go', c).textContent = live ? 'Show address' : 'Coming soon';
      const body = $('.c-body', c); body.textContent = '';
      if (!live) return;
      const qr = document.createElement('div'); qr.className = 'qr'; qr.setAttribute('aria-hidden', 'true');
      const side = document.createElement('div');
      const w = document.createElement('p'); w.className = 'c-warn'; w.textContent = spec.warn;
      const addr = document.createElement('code'); addr.className = 'addr'; addr.textContent = a;
      const b = document.createElement('button'); b.type = 'button'; b.className = 'btn'; b.textContent = 'COPY ADDRESS';
      const said = document.createElement('span'); said.className = 'copied'; said.setAttribute('aria-live', 'polite');
      b.addEventListener('click', () => {
        const done = (t) => { said.textContent = t; clearTimeout(b._t); b._t = setTimeout(() => (said.textContent = ''), 2500); };
        if (navigator.clipboard) navigator.clipboard.writeText(a).then(() => done('Copied.'), () => done('Copy failed: select the address above.'));
        else done('Select the address above to copy it.');
      });
      side.append(w, addr, b, said); body.append(qr, side);
      c._uri = spec.uri(a);
    });
  }
  // QR codes: the small library loads only when someone opens a coin
  let qrLib = null;
  const loadQR = () => qrLib || (qrLib = new Promise((ok, no) => { const sc = document.createElement('script');
    sc.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js'; sc.onload = () => ok(window.QRCode); sc.onerror = no; document.head.appendChild(sc); }));
  dlg.querySelectorAll('.coin').forEach((c) => c.addEventListener('toggle', () => {
    if (!c.classList.contains('off')) $('.c-go', c).textContent = c.open ? 'Hide address' : 'Show address';
    if (!c.open) return;
    if (c.classList.contains('off')) { c.open = false; return; }
    dlg.querySelectorAll('.coin[open]').forEach((o) => { if (o !== c) o.open = false; });
    const box = $('.qr', c);
    if (box && !box.childElementCount) loadQR().then((QR) => { if (!box.childElementCount) new QR(box, { text: c._uri, width: 132, height: 132, correctLevel: QR.CorrectLevel.M }); }, () => box.remove());
  }));

  let data = null, loadedAt = 0;
  function render() {
    const status = $('#sStatus');
    const d = data || {}, period = ymd(d.month), wk = ymd(d.week_start), upd = ymd(d.updated);
    const gM = num(d.goal_month), gW = num(d.goal_week), rM = num(d.received_month), rW = num(d.received_week);
    payments(d.pay && typeof d.pay === 'object' ? d.pay : {});
    const ok = period && wk && upd && gM > 0 && gW > 0 && rM !== null && rW !== null;
    if (!ok) {
      status.textContent = data === null ? 'Loading the latest numbers\u2026' : 'The latest numbers couldn\u2019t be loaded right now. Please try again later.';
      status.classList.toggle('bad', data !== null);
      return;
    }
    status.classList.remove('bad');
    status.textContent = 'Updated ' + MON[upd.mo - 1] + ' ' + upd.d + ', ' + upd.y + '.';
    $('#sGoal').textContent = money(gM);
    $('#sBadge').textContent = MON[period.mo - 1] + ' ' + period.y + (num(d.month_number) ? ' \u00b7 Month ' + d.month_number : '');
    const end = new Date(Date.UTC(wk.y, wk.mo - 1, wk.d + 6)), we = { mo: end.getUTCMonth() + 1, d: end.getUTCDate() };
    meter($('.meter.week'), rW, gW, day(wk) + ' \u2013 ' + day(we));
    meter($('.meter.month'), rM, gM, MON[period.mo - 1]);
    const pct = (rM / gM) * 100;
    dlg.querySelectorAll('.stop').forEach((st) => { const p = +st.dataset.pct; $('.d', st).textContent = money((gM * p) / 100); st.classList.toggle('hit', pct >= p); });
    $('.track .fill').style.width = (pct >= 25 ? Math.min(75, ((pct - 25) / 75) * 75) : 0) + '%';
  }
  // Payment addresses come from support.json (next to this script); the live totals from the income ledger, published once a
  // day through Pulse. If Pulse can't be reached, support.json's own dated totals are shown instead.
  const TOTALS = ['updated', 'month', 'month_number', 'week_start', 'goal_month', 'goal_week', 'received_month', 'received_week'];
  const getJSON = (url, opts) => fetch(url, opts).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }).then((j) => (j && typeof j === 'object' ? j : null), () => null);
  function load() {
    loadedAt = Date.now();
    Promise.all([getJSON(BASE + 'support.json', { cache: 'no-store' }), getJSON(LIVE, { mode: 'cors', credentials: 'omit' })])
      .then(([local, live]) => {
        data = local || {};
        if (live && TOTALS.every((k) => k in live) && ymd(live.month) && num(live.goal_month) > 0) TOTALS.forEach((k) => (data[k] = live[k]));
      })
      .then(() => { if (dlg.open) replay(); else render(); });
  }
  function replay() {
    dlg.querySelectorAll('.meter-bar i, .track .fill').forEach((e) => { e.style.transition = 'none'; e.style.width = '0'; void e.offsetWidth; e.style.transition = ''; });
    requestAnimationFrame(render);
  }
  function open() {
    if (dlg.open) return;
    document.dispatchEvent(new CustomEvent('support:open'));            // lets a host page tidy up (close its mobile menu)
    document.documentElement.classList.add('support-lock');
    dlg.showModal(); replay();
    if (Date.now() - loadedAt > 60000) load();                          // fresh numbers if the page has been open a while
    if (location.hash !== '#support') history.replaceState(null, '', '#support');
  }
  dlg.addEventListener('close', () => {
    document.documentElement.classList.remove('support-lock');
    if (location.hash === '#support') history.replaceState(null, '', location.pathname + location.search);
  });
  dlg.addEventListener('click', (e) => {                                  // only a click outside the box closes it
    if (e.target !== dlg) return;
    const r = dlg.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dlg.close();
  });
  document.addEventListener('click', (e) => {                              // any [data-support-open] element, now or added later
    const t = e.target.closest && e.target.closest('[data-support-open], a[href="#support"]');
    if (t) { e.preventDefault(); open(); }
  });
  if (!document.querySelector('[data-support-open], a[href="#support"]')) {   // a page with no trigger of its own gets a floating one
    const fl = document.createElement('a'); fl.className = 'support-float'; fl.href = '#support'; fl.setAttribute('data-support-open', '');
    fl.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M12 20.5s-7.5-4.6-9.2-9.4C1.6 7.6 3.8 4.5 7 4.5c2.1 0 3.6 1.2 5 3 1.4-1.8 2.9-3 5-3 3.2 0 5.4 3.1 4.2 6.6-1.7 4.8-9.2 9.4-9.2 9.4z"/></svg><span>Support the dev</span>';
    document.body.appendChild(fl);
  }
  render(); load();
  if (location.hash === '#support') open();
  window.addEventListener('hashchange', () => { if (location.hash === '#support') open(); });
});
})();
