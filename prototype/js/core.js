/* Digital Mohalla v3 — core: router, shells, theme, motion and shared components.
   Component names here map 1:1 to React Native components (see README). */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const img = DB.img;
const U = id => DB.users[id];
const I = id => DB.items.find(x => x.id === id);
const rs = n => "Rs " + Number(n).toLocaleString("en-PK");
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const icon = (n, c = "i") => `<i data-lucide="${n}" class="${c}" aria-hidden="true"></i>`;
const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const dow = d => DOW[(d + 1) % 7]; /* October 2026 starts on a Thursday */

/* ---------------- Primitives ---------------- */
const logo = (c = "logo") => `<svg class="${c}" viewBox="0 0 100 100" fill="none" aria-hidden="true"><path d="M13 95V46L50 11l37 35v49" stroke="currentColor" stroke-width="11" stroke-linejoin="round"/><circle cx="36" cy="40" r="8" fill="currentColor"/><circle cx="64" cy="38" r="9" fill="currentColor"/><path d="M25 95V62c0-6 5-11 11-11h4l12 13-6 6-6-6v31zM75 95V62c0-7-5-12-12-12h-5L46 63l6 6 7-7v33z" fill="currentColor"/></svg>`;
const av = (uid, size = "", extra = "") => {
  const u = typeof uid === "string" ? U(uid) : uid; const px = { xs: 50, sm: 64, lg: 120, xl: 180 }[size] || 80;
  return `<span class="avatar ${size} ${extra}" aria-hidden="true">${u.photo ? `<img src="${img(u.photo, px, px)}" alt="" loading="lazy">` : u.initials}</span>`;
};
const photo = (src, o = {}) => `<div class="ph-img ${o.cls || ""}" ${o.ratio ? `style="aspect-ratio:${o.ratio}"` : ""}>
  <img src="${img(src, o.w || 640)}" alt="${o.alt ?? ""}" loading="${o.eager ? "eager" : "lazy"}" ${o.vt ? `style="view-transition-name:${o.vt}"` : ""}>
  ${o.shade ? '<span class="shade"></span>' : ""}${o.tl ? `<span class="tl">${o.tl}</span>` : ""}${o.tr ? `<span class="tr">${o.tr}</span>` : ""}${o.bl ? `<div class="bl">${o.bl}</div>` : ""}${o.inner || ""}</div>`;
const saveBtn = (l = "Save") => `<button class="save" type="button" data-act="save" aria-pressed="false" aria-label="${l}">${icon("heart")}</button>`;
const soon = (t = "Coming soon") => `<span class="soon">${icon("sparkles")}${t}</span>`;
const previewBar = (what, it = "iteration 3") => `<div class="preview-bar">${icon("flask-conical")}<span><strong>Preview.</strong> ${what} is planned for ${it}. Everything here is clickable so the team can agree on it before it's built.</span></div>`;
const tone = (n, t = "green", size = "") => `<span class="tone t-${t}" ${size ? `style="width:${size}px;height:${size}px;border-radius:${size / 3.3}px"` : ""}>${icon(n)}</span>`;

const ST = {
  sufficient: ["shield-check", "Enough evidence"], review: ["eye", "Review recommended"], insufficient: ["sprout", "Not enough history yet"],
  dispute: ["scale", "Open dispute"], held: ["hourglass", "With a moderator"]
};
const stateChip = (s, label) => `<span class="state ${s}">${icon(ST[s][0])}${label || ST[s][1]}</span>`;
const LC = { REQUEST_CREATED: "Sent", HELD_FOR_REVIEW: "With a moderator", ASSESSED: "Waiting for lender", ACCEPTED: "Accepted", ACTIVE: "Borrowed", RETURN_INITIATED: "Being returned", RETURNED: "Returned", COMPLETED: "Completed", EXPIRED: "Expired", NO_SHOW: "No-show", DISPUTED: "Disputed" };

/* Live countdown: data-mins counts down each minute */
const fmt = m => m <= 0 ? "Time's up" : m < 60 ? `${m}m left` : m < 1440 ? `${Math.floor(m / 60)}h ${m % 60}m left` : `${Math.floor(m / 1440)}d ${Math.floor(m % 1440 / 60)}h left`;
const cd = (m, cls = "") => `<span class="cd ${m < 120 ? "urgent" : ""} ${cls}" data-mins="${m}" role="timer"><i></i><span>${fmt(m)}</span></span>`;
setInterval(() => $$("[data-mins]").forEach(e => { const m = Math.max(0, +e.dataset.mins - 1); e.dataset.mins = m; e.lastElementChild.textContent = fmt(m); }), 60000);

/* ---------------- Evidence: recency-weighted Beta posterior curve (signature) ---------------- */
function betaPdf(x, a, b) { return Math.pow(x, a - 1) * Math.pow(1 - x, b - 1); }
function betaCurve(a, b, state) {
  const W = 560, H = 150, N = 140, pts = [];
  for (let i = 0; i <= N; i++) { const x = Math.min(.999, Math.max(.001, i / N)); pts.push([x, betaPdf(x, a, b)]); }
  const max = Math.max(...pts.map(p => p[1])) || 1;
  /* numeric CDF for the 5% and 95% quantiles */
  const tot = pts.reduce((s, p) => s + p[1], 0); let acc = 0, lo = 0, hi = 1;
  for (const [x, y] of pts) { acc += y; if (acc / tot >= .05 && !lo) lo = x; if (acc / tot >= .95) { hi = x; break; } }
  const X = x => 10 + x * (W - 20), Y = y => H - 14 - (y / max) * (H - 34);
  const flat = a === 1 && b === 1;
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${X(x).toFixed(1)} ${(flat ? H - 70 : Y(y)).toFixed(1)}`).join("");
  const band = pts.filter(([x]) => x >= lo && x <= hi);
  const bandPath = `M${X(lo).toFixed(1)} ${H - 14}` + band.map(([x, y]) => `L${X(x).toFixed(1)} ${(flat ? H - 70 : Y(y)).toFixed(1)}`).join("") + `L${X(hi).toFixed(1)} ${H - 14}Z`;
  const col = { sufficient: "var(--primary)", review: "var(--saffron)", insufficient: "var(--sky)" }[state] || "var(--primary)";
  const desc = flat ? "Flat: every outcome is equally possible, because there is no history yet." : hi - lo > .45 ? "Wide: some evidence, still uncertain." : "Narrow and high: lots of consistent evidence.";
  return `<div class="curve"><svg viewBox="0 0 ${W} ${H + 8}" role="img" aria-label="Likely reliability for this loan. 90% of the evidence lies between ${Math.round(lo * 100)} and ${Math.round(hi * 100)} percent. ${desc}">
    <defs><linearGradient id="bg-${state}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${col}" stop-opacity=".45"/><stop offset="1" stop-color="${col}" stop-opacity=".05"/></linearGradient></defs>
    <line class="axis" x1="10" x2="${W - 10}" y1="${H - 14}" y2="${H - 14}"/>
    ${[0, .25, .5, .75, 1].map(t => `<line class="axis" x1="${X(t)}" x2="${X(t)}" y1="${H - 14}" y2="${H - 9}"/>`).join("")}
    <path class="band" d="${bandPath}" fill="url(#bg-${state})"/>
    <path class="line" d="${line}" stroke="${col}"/>
    <text class="lbl" x="10" y="${H + 6}">Less reliable</text><text class="lbl" x="${W - 10}" y="${H + 6}" text-anchor="end">More reliable</text>
    <text class="lbl" x="${(X(lo) + X(hi)) / 2}" y="${H - 22}" text-anchor="middle" style="fill:${col}">90% of the evidence</text></svg>
    <p class="cap">${icon("info")}<span>${desc} The shape of the evidence, not a score.</span></p></div>`;
}
function pathsGraph() {
  const N = { you: [40, 70, "u0", "You"], b: [170, 24, "u2", "Bilal"], k: [125, 122, "u5", "Kamran"], h: [235, 122, "u4", "Hira"], n: [330, 70, "u6", "Nadia"] };
  const E = [["you", "b"], ["b", "n"], ["you", "k"], ["k", "h"], ["h", "n"]];
  return `<div class="graph"><svg viewBox="0 0 370 160" role="img" aria-label="Two community paths: You, Bilal, Nadia; and You, Kamran, Hira, Nadia.">
    ${E.map(([a, b]) => `<path class="e" d="M${N[a][0]} ${N[a][1]}L${N[b][0]} ${N[b][1]}"/>`).join("")}
    ${Object.entries(N).map(([k, [x, y, uid, nm]]) => { const u = U(uid); return `<clipPath id="g${k}"><circle cx="${x}" cy="${y}" r="16"/></clipPath><circle cx="${x}" cy="${y}" r="19" fill="${k === "n" ? "var(--sky)" : k === "you" ? "var(--primary)" : "var(--surface-3)"}"/>${u.photo ? `<image href="${img(u.photo, 64, 64)}" x="${x - 16}" y="${y - 16}" width="32" height="32" clip-path="url(#g${k})" preserveAspectRatio="xMidYMid slice"/>` : `<circle cx="${x}" cy="${y}" r="16" fill="var(--surface-2)"/><text x="${x}" y="${y + 4}" text-anchor="middle">${u.initials}</text>`}<text x="${x}" y="${y + 34}" text-anchor="middle">${nm}</text>`; }).join("")}</svg></div>`;
}
function evidence(a, { name = "the person", interactive = true, tech = true } = {}) {
  return `<section class="ev" aria-label="Evidence report">
    <div class="ev-h"><div class="between">${stateChip(a.state, a.title)}<span class="xs faint">Confidence: ${a.conf}</span></div><p class="lede">${a.lede}</p>
      <p class="ev-note">${icon("info")}Describes the evidence for this loan, not ${name}.</p></div>
    ${betaCurve(a.ab[0], a.ab[1], a.state)}
    <div class="factors">
      <div class="fac"><div class="fl">${icon("history")}Their own loans</div><div class="fv">${a.direct[0]}</div><div class="fx">${a.direct[1]}</div></div>
      <div class="fac"><div class="fl">${icon("waypoints")}Through people you know</div><div class="fv">${a.indirect[0]}</div><div class="fx">${a.indirect[1]}</div>${a.paths ? pathsGraph() : ""}</div>
      <div class="fac"><div class="fl">${icon("radar")}Unusual activity check</div><div class="fv">${a.risk[0]}</div><div class="fx">${a.risk[1]}</div></div></div>
    <div class="sg"><div class="between"><h3 style="font-size:15px">Suggested safeguards</h3><span class="xs faint">You can change these</span></div>
      ${a.safeguards.map(([t, d, on], i) => interactive ? `<label class="check"><input type="checkbox" ${on ? "checked" : ""} name="sg${i}"><span><strong>${t}</strong><span>${d}</span></span></label>` : `<div class="row small mt-2">${icon("check", "i-sm")}${t}</div>`).join("")}</div>
    ${tech ? `<details class="tech"><summary>${icon("chevron-right")}Technical details for reviewers</summary><dl class="kv"><dt>State</dt><dd>${a.code}</dd>${Object.entries(a.tech).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl></details>` : ""}
  </section>`;
}
const miniRange = (ab, state) => {
  const [a, b] = ab, m = a / (a + b), sd = Math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)));
  const lo = Math.max(2, (m - 1.65 * sd) * 100), hi = Math.min(98, (m + 1.65 * sd) * 100);
  const col = { sufficient: "var(--primary)", review: "var(--saffron)", insufficient: "var(--sky)" }[state];
  return `<div class="mini-range" role="img" aria-label="Range ${Math.round(lo)} to ${Math.round(hi)} percent"><i style="left:${a === 1 && b === 1 ? 4 : lo}%;width:${a === 1 && b === 1 ? 92 : hi - lo}%;background:${col}"></i></div><div class="between xs faint mt-1"><span>Less reliable</span><span>More reliable</span></div>`;
};

/* ---------------- Composite components ---------------- */
const itemCard = (it, o = {}) => {
  const ev = DB.lenderEv[it.lender];
  return `<a class="item press" href="#/item/${it.id}" data-vt>
    ${photo(it.photo, { w: 520, alt: it.title, tl: it.restricted ? `<span class="badge glass">${icon("badge-check")}Verified only</span>` : it.trend && o.trend ? `<span class="badge glass">${icon("flame")}${it.trend}</span>` : "", tr: saveBtn("Save " + it.title) })}
    <div class="meta"><h3>${it.title}</h3><p class="sub">${icon("map-pin")}${it.lane} · ${it.avail}</p>
      <div class="foot"><span class="row" style="gap:6px">${av(it.lender, "xs")}<span class="muted">${U(it.lender).short}</span>${ev ? `<span class="status ${ev.state === "sufficient" ? "green" : ev.state === "review" ? "saffron" : "sky"}" title="${ev.tag}"></span>` : ""}</span><span class="price">${it.deposit ? rs(it.deposit) : "No deposit"}</span></div></div></a>`;
};
const evTag = uid => { const e = DB.lenderEv[uid]; return `<span class="badge ${e.state === "sufficient" ? "green" : e.state === "review" ? "saffron" : "sky"}">${icon(ST[e.state][0])}${e.tag}</span>`; };
function timeline(steps) { return `<ol class="tl">${steps.map(s => `<li class="${s.s}"><span class="nd">${s.s === "done" ? icon("check") : s.s === "alert" ? icon("x") : ""}</span><div class="tt">${s.t}</div>${s.d ? `<div class="td">${s.d}</div>` : ""}</li>`).join("")}</ol>`; }
const LIFE = ["Requested", "Accepted", "Handover", "Borrowed", "Returned", "Done"];
const stepsH = (cur, alert) => `<div class="steps-h" aria-label="Step ${cur + 1} of 6">${LIFE.map((l, i) => `<div class="s ${i < cur ? "on" : i === cur ? (alert ? "alert" : "cur") : ""}"><i></i><span class="desk">${l}</span></div>`).join("")}</div>`;
const stepper = (cur, n = 6, alert) => `<div class="stepper">${Array.from({ length: n }, (_, i) => `<i class="${i < cur ? "on" : i === cur ? (alert ? "alert" : "cur") : ""}"></i>`).join("")}</div>`;
function pageHead({ title, sub = "", crumbs = null, back = null, actions = "", eyebrow = "" }) {
  return `<header class="ph rv">${back ? `<a class="back" href="${back[0]}">${icon("arrow-left")}${back[1]}</a>` : ""}${crumbs ? `<nav class="crumbs">${crumbs.map(([l, h], i) => h ? `<a href="${h}">${l}</a>${icon("chevron-right", "i-sm")}` : `<span>${l}</span>`).join("")}</nav>` : ""}
    <div class="between"><div class="grow">${eyebrow ? `<div class="eyebrow mb-2">${eyebrow}</div>` : ""}<h1>${title}</h1>${sub ? `<p>${sub}</p>` : ""}</div>${actions ? `<div class="btns">${actions}</div>` : ""}</div></header>`;
}
const empty = (ic, t, title, text, act = "") => `<div class="empty"><div class="ill t-${t}">${icon(ic)}</div><h2>${title}</h2><p>${text}</p>${act ? `<div class="btns mt-6" style="justify-content:center">${act}</div>` : ""}</div>`;
function done(title, text = "") { setTimeout(confetti, 200); return `<div class="center" style="padding:40px 0 10px"><svg class="done-anim" viewBox="0 0 84 84" aria-hidden="true"><circle cx="42" cy="42" r="40"/><path d="M26 43l11 11 22-24"/></svg><h2 style="font-size:1.6rem">${title}</h2>${text ? `<p class="muted mt-2" style="max-width:46ch;margin-inline:auto">${text}</p>` : ""}</div>`; }
function confetti() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const c = document.createElement("div"); c.className = "confetti";
  const cols = ["#0F7B53", "#F2A32A", "#EC6A52", "#2F7BEA", "#7B61F0", "#34D399"];
  c.innerHTML = Array.from({ length: 30 }, (_, i) => `<i style="background:${cols[i % 6]};--x:${(Math.random() - .5) * 560}px;--y:${-60 - Math.random() * 300}px;--r:${Math.random() * 720}deg;animation-delay:${Math.random() * .1}s"></i>`).join("");
  document.body.appendChild(c); setTimeout(() => c.remove(), 1400);
}

/* Calendar (date range picker) */
function calendar({ id = "cal", sel = [], blocked = [], requested = [], today = 13, start = 3, days = 31, month = "October 2026" } = {}) {
  let cells = DOW.map(d => `<span class="dw">${d[0]}${d[1]}</span>`).join("") + "<span></span>".repeat(start);
  for (let d = 1; d <= days; d++) {
    const s = sel[0], e = sel[1] ?? sel[0];
    const cls = [d === s && "s", d === e && "e", sel.length && d > s && d < e && "in", requested.includes(d) && "req", d === today && "today"].filter(Boolean).join(" ");
    cells += `<button type="button" data-d="${d}" class="${cls}" ${d < today || blocked.includes(d) ? "disabled" : ""} aria-label="${dow(d)} ${d} October${blocked.includes(d) ? ", booked" : ""}${requested.includes(d) ? ", someone else asked" : ""}">${d}</button>`;
  }
  return `<div class="cal" id="${id}"><div class="cal-h"><button class="icon-btn" type="button" aria-label="Previous month">${icon("chevron-left")}</button><strong>${month}</strong><button class="icon-btn" type="button" aria-label="Next month">${icon("chevron-right")}</button></div>
    <div class="cal-g">${cells}</div><div class="cal-l"><span><i style="background:var(--primary)"></i>Your dates</span><span><i style="background:var(--surface-3)"></i>Booked</span><span><i style="background:var(--saffron);border-radius:50%;width:6px;height:6px"></i>Someone else asked</span></div></div>`;
}
function bindCal(id, cb, init = []) {
  let sel = init.slice(); const root = $("#" + id); if (!root) return;
  root.addEventListener("click", e => {
    const b = e.target.closest("button[data-d]"); if (!b || b.disabled) return; const d = +b.dataset.d;
    sel = sel.length === 1 && d > sel[0] ? [sel[0], d] : [d];
    $$("button[data-d]", root).forEach(x => { const n = +x.dataset.d, s = sel[0], en = sel[1] ?? sel[0]; x.classList.toggle("s", n === s); x.classList.toggle("e", n === en); x.classList.toggle("in", n > s && n < en); });
    cb && cb(sel);
  });
}

/* Tabs and segmented controls with animated indicator */
const tabs = (items, sel = 0, id = "") => `<div class="tabs" role="tablist" ${id ? `id="${id}"` : ""}>${items.map(([k, l, n], i) => `<button role="tab" type="button" data-tab="${k}" aria-selected="${i === sel}">${l}${n != null ? `<span class="n">${n}</span>` : ""}</button>`).join("")}<span class="bar"></span></div>`;
const seg = (items, sel = 0, extra = "") => `<div class="seg ${extra}" role="tablist">${items.map(([k, l], i) => `<button role="tab" type="button" data-v="${k}" aria-selected="${i === sel}">${l}</button>`).join("")}<span class="thumb"></span></div>`;
function placeBars(root = document) {
  $$(".tabs", root).forEach(t => { const s = $('[aria-selected="true"]', t), b = $(".bar", t); if (s && b) { b.style.width = s.offsetWidth - 20 + "px"; b.style.transform = `translateX(${s.offsetLeft + 10}px)`; } });
  $$(".seg", root).forEach(t => { const s = $('[aria-selected="true"]', t), b = $(".thumb", t); if (s && b) { b.style.width = s.offsetWidth + "px"; b.style.transform = `translateX(${s.offsetLeft}px)`; } });
}

/* ---------------- Overlays ---------------- */
function dialog(html, label = "Dialog", cls = "dialog") {
  closeDialog();
  const s = document.createElement("div"); s.className = "scrim"; s.id = "scrim";
  s.innerHTML = `<div class="${cls}" role="dialog" aria-modal="true" aria-label="${label}">${cls === "dialog" ? '<div class="grab"></div>' : ""}${html}</div>`;
  s.addEventListener("click", e => { if (e.target === s || e.target.closest("[data-close]")) closeDialog(); });
  document.body.appendChild(s); hydrate(s);
  const f = s.querySelector("[autofocus], input, textarea, button:not([data-close])"); f && f.focus();
  return s;
}
function closeDialog() { $("#scrim")?.remove(); }
function toast(msg, { undo, rich, ic = "circle-check" } = {}) {
  const box = $("#toasts"); const t = document.createElement("div");
  t.className = "toast" + (rich ? " rich" : ""); t.setAttribute("role", "status");
  t.innerHTML = rich ? `${av(rich.who, "sm", "ti")}<div class="grow"><div class="tt">${rich.t}</div><div class="td">${rich.d}</div></div>${rich.href ? `<a class="btn btn-sm btn-soft" href="${rich.href}">View</a>` : ""}` : `${icon(ic)}<span class="grow">${msg}</span>${undo ? `<button type="button">Undo</button>` : ""}`;
  box.appendChild(t); hydrate(t);
  if (undo) t.querySelector("button").onclick = () => { undo(); t.remove(); };
  t.addEventListener("click", e => { if (e.target.closest("a")) t.remove(); });
  setTimeout(() => { t.classList.add("out"); setTimeout(() => t.remove(), 220); }, rich ? 6500 : 4200);
}

/* ---------------- Theme (with circular reveal) ---------------- */
const THEME = { get() { try { return localStorage.getItem("dm-theme"); } catch { return null; } }, set(v) { try { localStorage.setItem("dm-theme", v); } catch {} } };
function applyTheme(t) { document.documentElement.dataset.theme = t; $$("[data-theme-icon]").forEach(e => { e.innerHTML = icon(t === "dark" ? "sun" : "moon"); }); refreshIcons(); }
applyTheme(THEME.get() || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
function toggleTheme(e) {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; THEME.set(next);
  const r = e?.currentTarget?.getBoundingClientRect?.() || e?.target?.getBoundingClientRect?.();
  if (r) { document.documentElement.style.setProperty("--tx", r.left + r.width / 2 + "px"); document.documentElement.style.setProperty("--ty", r.top + r.height / 2 + "px"); }
  if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) return applyTheme(next);
  document.documentElement.classList.add("theme-swap");
  const vt = document.startViewTransition(() => applyTheme(next));
  const end = () => document.documentElement.classList.remove("theme-swap");
  vt.finished.finally(end); setTimeout(end, 900);
}

/* ---------------- Shells ---------------- */
const NAV = [["#/home", "home", "Home", "house"], ["#/borrow", "borrow", "Borrow", "search"], ["#/activity", "activity", "Activity", "arrow-left-right"], ["#/community", "community", "Community", "users-round"], ["#/inbox", "inbox", "Inbox", "message-circle"]];
function siteNav(active, role) {
  if (role === "public") return `<div class="wrap"><a class="brand" href="#/welcome">${logo()}Digital Mohalla</a>
    <nav class="navlinks desk" aria-label="Sections"><a href="#/welcome">Product</a><a href="#/welcome" data-scroll="how">How it works</a><a href="#/welcome" data-scroll="modules">Modules</a><a href="#/hci">Design notes</a></nav>
    <div class="nav-right"><button class="icon-btn" type="button" data-act="theme" aria-label="Toggle dark mode"><span data-theme-icon></span></button><a class="btn btn-ghost btn-sm desk" href="#/login">Log in</a><a class="btn btn-primary btn-sm" href="#/register">Get started</a></div></div>`;
  const unread = DB.notifications.filter(n => n.unread).length;
  const u = U(role === "moderator" ? "mod" : role === "admin" ? "admin" : "u0");
  return `<div class="wrap" style="max-width:${role === "member" ? "1200px" : "100%"}"><a class="brand" href="${role === "member" ? "#/home" : role === "moderator" ? "#/mod" : "#/admin"}">${logo()}<span>Digital Mohalla</span>${role !== "member" ? `<small class="desk">${role === "moderator" ? "Moderator console" : "Admin"}</small>` : ""}</a>
    ${role === "member" ? `<nav class="navlinks" aria-label="Main">${NAV.map(([h, k, l]) => `<a href="${h}" ${k === active ? 'aria-current="page"' : ""}>${l}${k === "community" ? '<span class="soon-dot" title="Some features coming soon"></span>' : ""}</a>`).join("")}</nav>` : ""}
    <div class="nav-right">
      <button class="kbd-search" type="button" data-act="cmdk">${icon("search")}Search Digital Mohalla<kbd>Ctrl K</kbd></button>
      <button class="icon-btn mob" type="button" data-act="cmdk" aria-label="Search">${icon("search")}</button>
      ${role === "member" ? `<div style="position:relative" class="desk"><button class="btn btn-primary btn-sm" type="button" data-act="create">${icon("plus")}New</button></div>` : ""}
      <button class="icon-btn" type="button" data-act="theme" aria-label="Toggle dark mode"><span data-theme-icon></span></button>
      <div style="position:relative"><button class="icon-btn" type="button" data-act="bell" aria-label="Notifications, ${unread} unread">${icon("bell")}${unread ? '<span class="dot"></span>' : ""}</button></div>
      <div style="position:relative"><button class="avatar-btn" type="button" data-act="me" aria-label="Account menu">${av(u, "sm")}</button></div>
    </div></div>`;
}
function tabbar(active) {
  return [["#/home", "home", "Home", "house"], ["#/borrow", "borrow", "Borrow", "search"]].map(([h, k, l, ic]) => `<a href="${h}" ${k === active ? 'aria-current="page"' : ""}>${icon(ic)}${l}</a>`).join("")
    + `<button class="create" type="button" data-act="create" aria-label="Create"><span>${icon("plus")}</span></button>`
    + [["#/community", "community", "Community", "users-round"], ["#/activity", "activity", "Activity", "arrow-left-right"]].map(([h, k, l, ic]) => `<a href="${h}" ${k === active ? 'aria-current="page"' : ""}>${icon(ic)}${l}${k === "activity" && active !== "activity" ? '<span class="dot"></span>' : ""}</a>`).join("");
}
const CONSOLE = {
  moderator: [["Review", [["#/mod", "queue", "Case queue", "list-checks", 6], ["#/mod/members", "members", "Join requests", "user-check", 3], ["#/mod/reports", "reports", "Reports & flags", "flag", 3]]], ["Community", [["#/mod/events", "events", "Event approvals", "calendar-check", "soon"], ["#/mod/audit", "audit", "Audit log", "scroll-text"]]]],
  admin: [["Overview", [["#/admin", "dash", "Analytics", "chart-no-axes-combined"], ["#/admin/cases", "queue", "Escalations", "siren", 1]]], ["Manage", [["#/admin/users", "users", "Users & roles", "users", "soon"], ["#/admin/communities", "communities", "Communities", "map", "soon"], ["#/admin/vendors", "vendors", "Vendor verification", "store", "soon"], ["#/admin/knowledge", "kb", "Assistant knowledge", "book-open-check", "soon"]]], ["Integrity", [["#/admin/audit", "audit", "Audit log", "scroll-text"]]]]
};
function consoleShell(role, active, inner) {
  const groups = CONSOLE[role];
  const flat = groups.flatMap(g => g[1]);
  return `<div class="console"><aside class="side" aria-label="Console navigation">
      <div class="card card-2" style="padding:12px;margin-bottom:6px"><div class="row">${tone(role === "admin" ? "globe" : "shield-check", role === "admin" ? "violet" : "green", 34)}<div><div class="small" style="font-weight:650">${role === "admin" ? "All communities" : "Block C, Gulberg III"}</div><div class="xs faint">${role === "admin" ? "Platform admin" : "Your community only"}</div></div></div></div>
      ${groups.map(([g, ls]) => `<h4>${g}</h4>${ls.map(([h, k, l, ic, n]) => `<a href="${h}" ${k === active ? 'aria-current="page"' : ""}>${icon(ic)}${l}${n === "soon" ? '<span class="n">Soon</span>' : n ? `<span class="n">${n}</span>` : ""}</a>`).join("")}`).join("")}
      <h4>Switch</h4><a href="#/home">${icon("house")}Resident app</a>${role === "moderator" ? `<a href="#/admin">${icon("layout-dashboard")}Admin</a>` : `<a href="#/mod">${icon("shield-check")}Moderator console</a>`}
    </aside><div class="console-main"><div class="wrap" style="max-width:1360px"><div class="console-tabs chips">${flat.map(([h, k, l]) => `<a class="chip" href="${h}" ${k === active ? 'aria-pressed="true"' : ""}>${l}</a>`).join("")}</div>${inner}</div></div></div>`;
}

/* ---------------- Popovers (create, bell, account) ---------------- */
function popover(anchor, html) {
  closePop(); const p = document.createElement("div"); p.className = "pop"; p.id = "pop"; p.innerHTML = html;
  anchor.parentElement.appendChild(p); hydrate(p);
  setTimeout(() => document.addEventListener("click", closePopOutside), 0);
}
function closePop() { $("#pop")?.remove(); document.removeEventListener("click", closePopOutside); }
function closePopOutside(e) { if (!e.target.closest("#pop")) closePop(); }
const CREATE_MENU = `<div class="ph2">Create</div>
  <a href="#/lend">${tone("hand-heart", "green", 32)}<span><b>Lend an item</b><br><span class="xs faint">List something neighbours can borrow</span></span></a>
  <a href="#/ask">${tone("megaphone", "saffron", 32)}<span><b>Ask the mohalla</b> ${soon("Soon")}<br><span class="xs faint">Request something nobody has listed</span></span></a>
  <a href="#/forum/new">${tone("message-square-plus", "violet", 32)}<span><b>Start a discussion</b> ${soon("Soon")}<br><span class="xs faint">Ask, recommend, share</span></span></a>
  <a href="#/events/new">${tone("calendar-plus", "sky", 32)}<span><b>Host an event</b> ${soon("Soon")}<br><span class="xs faint">Cleanups, workshops, celebrations</span></span></a>`;

/* ---------------- Command palette ---------------- */
function cmdItems() {
  return [
    ["Go to", "house", "Home", "#/home"], ["Go to", "search", "Borrow (search)", "#/borrow"], ["Go to", "arrow-left-right", "Activity", "#/activity"], ["Go to", "users-round", "Community hub", "#/community"],
    ["Go to", "message-circle", "Inbox", "#/inbox"], ["Go to", "bell", "Notifications", "#/notifications"], ["Go to", "shield-check", "My evidence", "#/evidence"], ["Go to", "settings", "Settings", "#/settings"],
    ["Create", "hand-heart", "Lend an item", "#/lend"], ["Create", "megaphone", "Ask the mohalla", "#/ask"], ["Create", "message-square-plus", "Start a discussion", "#/forum/new"], ["Create", "calendar-plus", "Host an event", "#/events/new"],
    ...DB.items.filter(i => i.lender !== "u0").map(i => ["Items", "package", i.title, "#/item/" + i.id]),
    ["Community", "messages-square", "Forum", "#/forum"], ["Community", "calendar-days", "Events", "#/events"], ["Community", "store", "Local vendors", "#/vendors"], ["Community", "piggy-bank", "Kameti", "#/kameti"], ["Community", "bot", "Mohalla assistant", "#/assistant"], ["Community", "chart-no-axes-column", "Neighbourhood insights", "#/insights"],
    ["Consoles", "shield-check", "Moderator console", "#/mod"], ["Consoles", "layout-dashboard", "Admin analytics", "#/admin"],
    ["Help", "circle-help", "How evidence works (HCI notes)", "#/hci"], ["Help", "map", "Prototype screen map", "proto"]
  ];
}
function openCmdk() {
  const s = dialog(`<div class="q">${icon("search")}<input id="cq" placeholder="Search items, pages, actions…" aria-label="Search" autocomplete="off"><kbd>Esc</kbd></div><div class="res" id="cres" role="listbox"></div>
    <div class="foot"><span>↑↓ to move</span><span>Enter to open</span><span>Try “deg”, “events”, “dark”</span></div>`, "Command palette", "cmdk");
  s.style.alignItems = "flex-start";
  let idx = 0, list = [];
  const draw = q => {
    q = q.trim().toLowerCase();
    const extra = q.includes("dark") || q.includes("theme") ? [["Actions", "moon", "Toggle dark mode", "theme"]] : [];
    list = extra.concat(cmdItems().filter(x => !q || x[2].toLowerCase().includes(q) || x[0].toLowerCase().includes(q))).slice(0, 40); idx = 0;
    let g = ""; $("#cres").innerHTML = list.length ? list.map((x, i) => (x[0] !== g ? `<div class="grp">${(g = x[0])}</div>` : "") + `<a href="${x[3].startsWith("#") ? x[3] : "#"}" data-i="${i}" role="option" aria-selected="${i === 0}">${tone(x[1], "neutral", 30)}${x[2]}<span class="k">${x[0]}</span></a>`).join("") : `<div class="empty" style="padding:28px">${icon("search-x")}<p>No matches for “${esc(q)}”.</p></div>`;
    refreshIcons();
  };
  const pick = i => { const x = list[i]; if (!x) return; closeDialog(); if (x[3] === "theme") toggleTheme(); else if (x[3] === "proto") toggleMap(); else location.hash = x[3]; };
  $("#cq").oninput = e => draw(e.target.value);
  $("#cq").onkeydown = e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); idx = (idx + (e.key === "ArrowDown" ? 1 : -1) + list.length) % list.length; $$("#cres a").forEach(a => a.setAttribute("aria-selected", +a.dataset.i === idx)); $(`#cres a[data-i="${idx}"]`)?.scrollIntoView({ block: "nearest" }); }
    if (e.key === "Enter") { e.preventDefault(); pick(idx); }
  };
  $("#cres").addEventListener("click", e => { const a = e.target.closest("a[data-i]"); if (a) { e.preventDefault(); pick(+a.dataset.i); } });
  draw("");
}

/* ---------------- Router with view transitions ---------------- */
const ROUTES = [];
function route(p, fn) { const keys = []; ROUTES.push({ re: new RegExp("^" + p.replace(/:(\w+)/g, (_, k) => (keys.push(k), "([^/]+)")) + "$"), keys, fn }); }
let cleanup = null, liveTimer = null;
function resolve() {
  const path = location.hash.slice(1) || "/welcome";
  for (const r of ROUTES) { const m = path.match(r.re); if (m) { const p = {}; r.keys.forEach((k, i) => (p[k] = decodeURIComponent(m[i + 1]))); return [r, p, path]; } }
  return [null, {}, path];
}
function paint() {
  if (cleanup) { cleanup(); cleanup = null; } clearTimeout(liveTimer); closeDialog(); closePop();
  const [r, p, path] = resolve(); if (!r) { location.hash = "#/home"; return; }
  const v = r.fn(p);
  const role = v.role || (path.startsWith("/mod") ? "moderator" : path.startsWith("/admin") ? "admin" : "member");
  document.body.classList.toggle("bare", !!v.bare);
  document.title = (v.title ? v.title + " · " : "") + "Digital Mohalla";
  $("#topnav").hidden = !!v.bare; $("#topnav").innerHTML = v.bare ? "" : siteNav(v.nav, role);
  $("#tabbar").hidden = v.bare || role !== "member"; $("#tabbar").innerHTML = role === "member" ? tabbar(v.nav) : "";
  $("#view").innerHTML = role === "moderator" || role === "admin" ? consoleShell(role, v.nav, v.html) : v.html;
  hydrate(document); window.scrollTo(0, 0);
  v.after && v.after();
  $("#view").focus({ preventScroll: true });
}
function render() {
  if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) return paint();
  const vt = document.startViewTransition(paint);
  vt.finished.finally(() => { $$("[style*='view-transition-name']").forEach(e => { if (!e.closest("#view")) e.style.viewTransitionName = ""; }); });
}
window.addEventListener("hashchange", render);

/* Hydrate: icons, reveals, indicators, theme icons */
let io;
function hydrate(root) {
  refreshIcons();
  $$("[data-theme-icon]", root).forEach(e => { e.innerHTML = icon(document.documentElement.dataset.theme === "dark" ? "sun" : "moon"); });
  refreshIcons();
  io = io || new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -6% 0px" });
  $$("[data-stagger]", root).forEach(g => [...g.children].forEach((c, i) => { c.classList.add("rv"); c.style.setProperty("--d", Math.min(i, 12)); }));
  $$(".rv:not(.in)", root).forEach(e => io.observe(e));
  requestAnimationFrame(() => placeBars(root));
  $$("[data-count]", root).forEach(el => { const end = +el.dataset.count, t0 = performance.now(), dec = el.dataset.dec ? 1 : 0; const f = t => { const p = Math.min(1, (t - t0) / 1000); el.textContent = (end * (1 - Math.pow(1 - p, 3))).toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g, ","); if (p < 1) requestAnimationFrame(f); }; requestAnimationFrame(f); });
}
function refreshIcons() { window.lucide && lucide.createIcons({ attrs: { "stroke-width": 1.9 } }); }
window.addEventListener("resize", () => placeBars());

/* ---------------- Global interactions ---------------- */
document.addEventListener("click", e => {
  const vtA = e.target.closest("a[data-vt]");
  if (vtA && !e.target.closest("[data-act]")) { const im = $("img", vtA); if (im) im.style.viewTransitionName = "hero"; }
  const t = e.target.closest("[data-act]"); if (!t) return;
  const a = t.dataset.act;
  if (a === "save") { e.preventDefault(); const on = t.getAttribute("aria-pressed") !== "true"; t.setAttribute("aria-pressed", on); if (on) toast("Saved to your list"); }
  if (a === "theme") toggleTheme(e);
  if (a === "cmdk") openCmdk();
  if (a === "create") { e.stopPropagation(); if (innerWidth < 900) dialog(`<h2>Create</h2><div class="pop" style="position:static;box-shadow:none;border:0;padding:0;margin-top:12px;animation:none">${CREATE_MENU}</div>`, "Create"); else popover(t, CREATE_MENU); }
  if (a === "bell") { e.stopPropagation(); if (innerWidth < 900) { location.hash = "#/notifications"; return; } popover(t, `<div class="between" style="padding:8px 10px"><b>Notifications</b><a class="link xs" href="#/notifications" style="padding:0;display:inline">See all</a></div>${DB.notifications.slice(0, 5).map(n => `<a href="${n.href}">${tone(n.icon, n.tone, 32)}<span class="grow"><b style="font-weight:600;font-size:14px">${n.t}</b><br><span class="xs faint">${n.d}</span></span>${n.unread ? '<span class="status coral" style="font-size:0"></span>' : ""}</a>`).join("")}`); $("#pop").style.width = "380px"; }
  if (a === "me") { e.stopPropagation(); popover(t, `<div class="row" style="padding:10px 12px">${av("u0", "")}<div><b>Sana Malik</b><div class="xs faint">Block C · resident</div></div></div><hr>
    <a href="#/profile">${icon("user")}Profile</a><a href="#/evidence">${icon("shield-check")}My evidence</a><a href="#/inbox">${icon("message-circle")}Inbox</a><a href="#/listings">${icon("package")}My listings</a><a href="#/settings">${icon("settings")}Settings</a><hr>
    <a href="#/mod">${icon("shield")}Moderator console</a><a href="#/admin">${icon("layout-dashboard")}Admin</a><hr><a href="#/welcome">${icon("log-out")}Sign out</a>`); }
  if (a === "tab") { /* generic tabs */ }
});
document.addEventListener("click", e => {
  const b = e.target.closest(".tabs [role=tab], .seg [role=tab]"); if (!b) return;
  const g = b.parentElement; $$("[role=tab]", g).forEach(x => x.setAttribute("aria-selected", x === b)); placeBars(g.parentElement);
  const key = b.dataset.tab, scope = g.closest("[data-tabs-scope]");
  if (key && scope) $$("[data-panel]", scope).filter(p => p.closest("[data-tabs-scope]") === scope).forEach(p => { p.hidden = p.dataset.panel !== key; if (!p.hidden) { $$(".rv", p).forEach(x => x.classList.add("in")); hydrate(p); } });
});
document.addEventListener("click", e => {
  const c = e.target.closest("[data-chips] .chip"); if (!c) return;
  $$(".chip", c.parentElement).forEach(x => x.setAttribute("aria-pressed", x === c));
});
document.addEventListener("pointermove", e => { const s = e.target.closest?.(".spot"); if (!s) return; const r = s.getBoundingClientRect(); s.style.setProperty("--mx", e.clientX - r.left + "px"); s.style.setProperty("--my", e.clientY - r.top + "px"); }, { passive: true });
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmdk(); }
  if (e.key === "/" && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); openCmdk(); }
  if (e.key === "Escape") { closeDialog(); closePop(); $("#map")?.remove(); }
});

/* Simulated live push (dynamic feel): one notification a while after landing on home */
function scheduleLive(list) { let i = 0; const next = () => { if (i >= list.length) return; liveTimer = setTimeout(() => { toast("", { rich: list[i++] }); next(); }, i ? 14000 : 5000); }; next(); }

/* ---------------- Screen map (prototype only) ---------------- */
const MAP = [];
function screens(group, list) { MAP.push([group, list]); }
function toggleMap() {
  if ($("#map")) return $("#map").remove();
  const d = document.createElement("aside"); d.className = "drawer"; d.id = "map"; d.setAttribute("aria-label", "Screen map");
  d.innerHTML = `<div class="between"><h2 style="font-size:1.2rem">Screen map</h2><button class="icon-btn" type="button" data-close-map aria-label="Close">${icon("x")}</button></div>
    <p class="small muted mt-2">Every workflow from the project overview. Iteration 2 screens are live; later modules are marked <span class="soon">${icon("sparkles")}Soon</span>.</p>
    ${MAP.map(([g, l]) => `<h3>${g}</h3>${l.map(([n, h, r]) => `<a href="${h}">${n}<small>${r || ""}</small></a>`).join("")}`).join("")}`;
  d.addEventListener("click", e => { if (e.target.closest("a") || e.target.closest("[data-close-map]")) d.remove(); });
  document.body.appendChild(d); refreshIcons();
}
window.addEventListener("DOMContentLoaded", () => { $("#proto").onclick = toggleMap; paint(); });
