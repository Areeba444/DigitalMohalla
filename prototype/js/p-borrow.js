/* Resident: home dashboard, borrow/search (W23), item (W24), request (B5), ask the mohalla (B9–B11, soon) */

const LIVE = [
  { who: "u2", t: "Bilal accepted your request", d: "Large deg · 18–19 Oct. Plan the handover in chat.", href: "#/inbox" },
  { who: "u7", t: "Farah answered your question", d: "“Rashid Tailors did ours in 2 days…”", href: "#/forum/p2" }
];
const needs = () => DB.loans.filter(l => l.col === "action").map(l => ({ ...l, it: I(l.item), u: U(l.other) }));

function homeView(isNew) {
  const hr = new Date().getHours(), greet = hr < 12 ? "Good morning" : hr < 17 ? "Good afternoon" : "Good evening";
  const n = needs();
  return `<div class="wrap">
    <section class="ph" style="padding-bottom:8px"><div class="between rv">
      <div><button class="badge outline" type="button" data-act="cmdk" style="height:30px">${icon("map-pin")}Block C, Gulberg III${icon("chevron-down")}</button>
        <h1 class="mt-3" style="font-size:clamp(1.9rem,4vw,2.9rem)">${isNew ? "Welcome to Block C, Sana" : `${greet}, Sana`}</h1>
        <p>${isNew ? "You're in. Here's how to get going." : `${n.length} things need you today · ${new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}`}</p></div>
      <div class="btns desk"><a class="btn btn-outline" href="#/borrow">${icon("search")}Borrow something</a><a class="btn btn-primary" href="#/lend">${icon("plus")}Lend an item</a></div></div></section>

    ${isNew ? `<div class="bento mt-4" data-stagger>
      <div class="card card-pad-lg b4"><div class="between"><h3>Get started</h3><span class="badge green">1 of 3 done</span></div>${stepper(1, 3)}
        <div class="mt-6">${timeline([{ s: "done", t: "Joined Block C", d: "Approved by Imran Q." }, { s: "now", t: "Borrow something small first", d: "A ladder or books. Small loans build evidence fastest." }, { s: "todo", t: "List one thing you rarely use", d: "Lending gives neighbours more paths to trust you." }])}</div>
        <div class="btns"><a class="btn btn-primary" href="#/borrow">Browse Block C</a><a class="btn btn-outline" href="#/lend">List an item</a></div></div>
      <div class="card b2 spot">${stateChip("insufficient")}<h3 class="mt-4">New here isn't bad</h3><p class="small muted mt-2">Lenders see that you have no history yet, shown in neutral blue, never red. It changes after your first completed loan.</p>${miniRange([1, 1], "insufficient")}<a class="link small mt-4" style="display:inline-block" href="#/evidence">How evidence works</a></div>
    </div>` : `<div class="bento mt-4" data-stagger>
      <div class="card b4" style="padding:8px"><div class="card-head" style="padding:12px 12px 0"><h3>${icon("bell-ring", "i")}Needs you</h3><a href="#/activity">All activity ${icon("arrow-right", "i-sm")}</a></div>
        <div>${n.map(l => `<a class="li" href="${l.href}" style="border-radius:14px;border:0">${photo(l.it.photo, { w: 140, alt: "" })}<span class="grow"><span class="t">${l.label}</span><span class="d">${l.it.title} · ${l.role === "lender" ? "to" : "from"} ${l.u.short}. ${l.next}</span></span>${l.mins ? cd(l.mins) : `<span class="badge ${l.tone}">${icon("arrow-right")}</span>`}</a>`).join("")}</div></div>
      <a class="card b2 spot hover" href="#/evidence"><div class="between"><h3>Your evidence</h3>${icon("arrow-up-right", "i faint")}</div><div class="mt-4">${stateChip("sufficient")}</div><p class="small muted mt-3">As a borrower: 7 completed loans, all on time.</p>${miniRange([16, 2.2], "sufficient")}</a>
      <a class="card b2 spot hover" href="#/loan/b2"><div class="between"><h3>Out with you</h3><span class="badge green">2 items</span></div><div class="row mt-4">${photo(I("ladder").photo, { w: 140, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:52px;border-radius:12px" class="ph-img ')}<div class="grow"><b class="small">Aluminium ladder</b><div class="xs faint">Due tomorrow, 8 pm</div></div></div><div class="mt-4">${stepper(3)}</div><p class="xs faint mt-3">${icon("alarm-clock", "i-sm")} Physics books are 1 day overdue</p></a>
      <div class="card b2"><div class="between"><h3>Community pulse</h3><span class="badge green"><span class="live"></span>Live</span></div><div id="pulse" class="mt-3" style="height:172px;overflow:hidden;mask-image:linear-gradient(#000 70%,transparent);-webkit-mask-image:linear-gradient(#000 70%,transparent)"></div></div>
      <a class="card b2 hover" href="#/event/e1" style="padding:0;overflow:hidden">${photo(DB.events[0].photo, { w: 600, ratio: "16/9", alt: "", tl: soon(), shade: true, bl: `<b>${DB.events[0].t}</b><div class="xs" style="opacity:.85">Sat 18 Oct · ${DB.events[0].where}</div>` })}<div style="padding:12px 16px" class="between"><span class="small muted">You're going · 52 of 60</span>${icon("arrow-up-right", "i faint")}</div></a>
      <a class="card b2 hover spot" href="#/forum/p1"><div class="between"><span class="badge violet">${icon("messages-square")}Forum</span>${soon()}</div><h3 class="mt-4" style="line-height:1.35">${DB.posts[0].t}</h3><p class="small muted mt-2">${DB.posts[0].comments} answers · best answer by Farah</p><div class="row mt-4"><span class="avs">${["u7", "u3", "u5"].map(u => av(u, "xs")).join("")}</span><span class="xs faint">+15 neighbours</span></div></a>
    </div>`}

    <section class="section"><h2 class="sec-title">In demand this week<a href="#/borrow">Browse all ${icon("arrow-right", "i-sm")}</a></h2>
      <div class="grid-4" data-stagger>${["deg", "chairs", "projector", "tent"].map(id => itemCard(I(id), { trend: 1 })).join("")}</div></section>
    <section class="section"><h2 class="sec-title">Free near you</h2>
      <div class="chips" data-chips>${DB.categories.map((c, i) => `<button class="chip" type="button" aria-pressed="${i === 0}">${icon(c.icon)}${c.label}</button>`).join("")}</div>
      <div class="grid-4 mt-4" data-stagger>${DB.items.filter(i => i.lender !== "u0" && !["deg", "chairs", "projector", "tent"].includes(i.id)).map(it => itemCard(it)).join("")}</div></section>
  </div>`;
}
function pulse() {
  const box = $("#pulse"); if (!box) return;
  let i = 0; const add = () => { if (!document.body.contains(box)) return; const [u, v, o, x] = DB.feed[i++ % DB.feed.length];
    const el = document.createElement("div"); el.className = "row"; el.style.cssText = "padding:7px 0;animation:in-up .5s var(--ease) both";
    el.innerHTML = `${av(u, "sm")}<span class="small"><b>${U(u).short}</b> ${v} <b>${o}</b> <span class="faint">${x}</span></span>`;
    box.prepend(el); if (box.children.length > 6) box.lastElementChild.remove(); };
  for (let k = 0; k < 4; k++) add();
  const t = setInterval(add, 3200); return () => clearInterval(t);
}
route("/home", () => ({ title: "Home", nav: "home", html: homeView(false), after() { cleanup = pulse(); scheduleLive(LIVE); } }));
route("/home/new", () => ({ title: "Welcome", nav: "home", html: homeView(true) }));

/* ---------------- W23: borrow / search ---------------- */
const resultRow = (it, ix = 0) => `<a class="card hover spot rv" href="#/item/${it.id}" data-vt style="padding:12px;display:flex;gap:16px;--d:${ix}">
  ${photo(it.photo, { w: 360, alt: it.title }).replace('class="ph-img ', 'style="width:clamp(96px,22vw,150px);flex:none;border-radius:14px" class="ph-img ')}
  <div class="grow" style="display:flex;flex-direction:column;gap:6px;padding:4px 0">
    <div class="between" style="align-items:flex-start"><h3 style="font-size:16px">${it.title}</h3>${saveBtn()}</div>
    <div class="small muted">${it.lane} · ${it.deposit ? rs(it.deposit) + " deposit" : "No deposit"} · up to ${it.max}</div>
    <div class="row-wrap">${evTag(it.lender)}${it.avail.startsWith("Booked") ? `<span class="badge saffron">${icon("calendar-x")}Partly booked</span>` : `<span class="badge">${icon("calendar-check")}${it.avail}</span>`}</div>
    <div class="xs muted row" style="gap:6px;margin-top:auto">${icon("sparkles", "i-sm")}<span><span class="sr">Why this result: </span>${it.why}</span></div></div></a>`;
const sk = n => Array.from({ length: n }, () => `<div class="card" style="padding:12px;display:flex;gap:16px" aria-hidden="true"><div class="sk" style="width:130px;height:100px;border-radius:14px"></div><div class="grow stack"><div class="sk" style="height:16px;width:60%"></div><div class="sk" style="height:12px;width:40%"></div><div class="sk" style="height:22px;width:50%;border-radius:20px"></div></div></div>`).join("");
const filters = () => `<div class="stack-lg">
  <div><div class="label">Category</div><div class="stack" style="gap:2px">${DB.categories.slice(1).map((c, i) => `<label class="check" style="padding:7px 0;border:0"><input type="checkbox" ${i === 0 ? "checked" : ""}><span><span style="color:var(--text)">${c.label}</span></span></label>`).join("")}</div></div>
  <div><div class="label">Dates</div><div class="btns"><span class="badge outline" style="height:34px">${icon("calendar")}Tue 14 – Thu 16 Oct</span></div></div>
  <div><label class="label" for="dep">Highest deposit</label><input class="range" type="range" id="dep" min="0" max="10000" step="500" value="5000"><span class="help" id="depv">Up to Rs 5,000</span></div>
  <div><div class="label">Lender history</div>${seg([["any", "Any"], ["est", "Established"]], 0)}<span class="help">New lenders aren't hidden by default. No history isn't bad history.</span></div>
  <div><div class="label">Condition</div><div class="chips" data-chips style="flex-wrap:wrap">${["Like new", "Very good", "Good", "Fair"].map((c, i) => `<button class="chip" type="button" aria-pressed="${i === 1}">${c}</button>`).join("")}</div></div></div>`;
function borrowView(mode) {
  const q = mode === "empty" ? "pressure washer" : "drill";
  let body;
  if (mode === "loading") body = `<div class="stack" role="status" aria-label="Loading results">${sk(4)}</div>`;
  else if (mode === "empty") body = empty("search-x", "neutral", "No pressure washers in Block C yet", "Nobody has listed one. Try a broader word, or ask the mohalla and we'll match you when someone has one.", `<a class="btn btn-primary" href="#/ask">${icon("megaphone")}Ask the mohalla</a><button class="btn btn-outline" type="button" data-act="save-search">${icon("bell-plus")}Alert me</button>`) + `<h3 class="mt-6 mb-3" style="margin-bottom:12px">Free on your dates anyway</h3><div class="stack">${resultRow(I("ladder"))}</div>`;
  else if (mode === "error") body = empty("wifi-off", "coral", "You're offline", "Your search will run as soon as you're back. Nothing you typed is lost.", `<a class="btn btn-primary" href="#/borrow">${icon("rotate-cw")}Try again</a>`);
  else body = `${mode === "fallback" ? `<div class="card card-2 row mb-4" style="margin-bottom:16px">${tone("zap-off", "saffron", 36)}<div><b class="small">Showing keyword matches only</b><p class="xs muted">Smart search is resting, so results match your exact words. Similar items like “screwdriver” may be missed.</p></div></div>` : ""}
    <div class="stack">${resultRow(I("makita"))}</div><h3 class="mt-8" style="margin-bottom:12px">Also free on your dates</h3><div class="stack">${["ladder", "tent", "deg", "chairs"].map((id, i) => resultRow(I(id), i + 1)).join("")}</div>`;
  return {
    title: "Borrow", nav: "borrow",
    html: `<div class="wrap">${pageHead({ title: "Borrow", sub: "Everything neighbours in Block C are lending. Results are ranked by match, dates and lending history, described in words." })}
      <form class="input-wrap rv" id="sf" role="search">${icon("search")}<input class="input" id="q" value="${q}" style="height:56px;font-size:17px;border-radius:16px;padding-right:130px" aria-label="Search" enterkeyhint="search"><span class="addon btns"><button class="btn btn-outline btn-sm mob" type="button" id="fbtn">${icon("sliders-horizontal")}</button><button class="btn btn-primary btn-sm" type="submit">Search</button></span></form>
      <div class="chips mt-4 rv" data-chips>${DB.categories.map(c => `<button class="chip" type="button" aria-pressed="${c.id === "tools"}">${icon(c.icon)}${c.label}</button>`).join("")}</div>
      <div class="two-col left mt-6"><aside class="aside desk"><div class="card">${filters()}</div><div class="card card-2 mt-4"><b class="small">${icon("lock", "i-sm")} Only Block C</b><p class="xs muted mt-1">No exact addresses are ever shown, so “nearby” means inside your community.</p></div></aside>
        <div><div class="between mb-4" style="margin-bottom:14px;flex-wrap:wrap"><span class="small"><b id="cnt">${mode === "empty" || mode === "error" ? "0 results" : mode === "loading" ? "Searching…" : "1 match · 4 more free"}</b> <span class="faint">· 14–16 Oct</span></span>${seg([["best", "Best match"], ["ev", "Most evidence"], ["new", "Newest"]])}</div>
          <div id="res">${body}</div>
          <div class="card card-2 mt-6 small"><b>Try a state:</b> <span class="row-wrap mt-2">${[["Results", "#/borrow"], ["Keyword only", "#/borrow/fallback"], ["Loading", "#/borrow/loading"], ["No results", "#/borrow/empty"], ["Offline", "#/borrow/error"]].map(([l, h]) => `<a class="chip" href="${h}">${l}</a>`).join("")}</span></div></div></div></div>`,
    after() {
      $("#sf").onsubmit = e => { e.preventDefault(); const v = $("#q").value.toLowerCase(); $("#res").innerHTML = `<div class="stack" role="status" aria-label="Loading">${sk(3)}</div>`; $("#cnt").textContent = "Searching…"; setTimeout(() => { location.hash = v.includes("washer") ? "#/borrow/empty" : "#/borrow"; if (!v.includes("washer")) render(); }, 900); };
      $("#fbtn").onclick = () => { dialog(`<div class="between"><h2>Filters</h2><button class="btn btn-ghost btn-sm" type="button">Reset</button></div><div class="mt-6">${filters()}</div><button class="btn btn-primary btn-block mt-6" data-close type="button">Show 5 items</button>`, "Filters"); bindDep(); };
      bindDep();
      if (mode === "loading") { const t = setTimeout(() => (location.hash = "#/borrow"), 1800); cleanup = () => clearTimeout(t); }
      $$("[data-act='save-search']").forEach(b => b.onclick = () => { b.innerHTML = `${icon("bell-ring")}Alert on`; refreshIcons(); toast("We'll tell you when someone lists a pressure washer"); });
    }
  };
}
function bindDep() { $$("#dep").forEach(r => (r.oninput = e => ($("#depv").textContent = "Up to " + rs(e.target.value)))); }
route("/borrow", () => borrowView("results"));
route("/borrow/:mode", ({ mode }) => borrowView(mode));

/* ---------------- W24: item details ---------------- */
route("/item/:id", ({ id }) => {
  const it = I(id) || I("makita"), u = U(it.lender), ev = DB.lenderEv[it.lender], own = it.lender === "u0", asked = id === "tent";
  const lenderCard = own ? `<div class="card"><div class="between"><h3>Your listing</h3><span class="status green live">Live</span></div><p class="small muted mt-2">2 requests this month · lent 3 times</p><div class="btns mt-4"><a class="btn btn-primary btn-sm" href="#/requests/r1">See Ayesha's request</a><a class="btn btn-outline btn-sm" href="#/lend/edit">${icon("pencil")}Edit</a></div></div>`
    : `<div class="card spot"><div class="between"><div class="row">${av(it.lender, "lg")}<div><div class="xs faint">Lent by</div><b>${u.name}</b><div class="xs faint">${u.lane} · since ${u.since}</div></div></div><a class="icon-btn" href="#/inbox" aria-label="Message ${u.short}">${icon("message-circle")}</a></div>
      <div class="divider"></div><div class="between"><b class="small">Lending history</b>${evTag(it.lender)}</div><p class="small muted mt-2">${ev.line}</p>${miniRange(ev.ab, ev.state)}<p class="xs faint mt-3">${icon("info", "i-sm")} From confirmed, completed loans only. Never a single score.</p></div>`;
  const cta = own ? "" : asked ? `<div class="card card-2 row">${tone("hourglass", "saffron", 36)}<div class="grow"><b class="small">You already asked</b><div class="xs muted">24–27 Oct · waiting for Bilal</div></div><a class="btn btn-outline btn-sm" href="#/activity">View</a></div>`
    : `<div class="card" style="box-shadow:var(--shadow)"><div class="between"><div><div class="xs faint">Deposit, paid in person</div><div class="kpi" style="font-size:1.6rem">${it.deposit ? rs(it.deposit) : "None"}</div></div><span class="badge green">${icon("calendar-check")}${it.avail}</span></div>
      <a class="btn btn-primary btn-lg btn-block mt-4 req" href="#/request/${it.id}">Request to borrow</a><p class="xs faint center mt-2">Nothing is charged. ${u.short} sees an evidence report first.</p></div>`;
  return {
    title: it.title, nav: "borrow",
    html: `<div class="wrap">${pageHead({ crumbs: [["Borrow", "#/borrow"], [DB.categories.find(c => c.id === it.cat)?.label || "Items", "#/borrow"], [it.title]], title: "" }).replace('<h1></h1>', '')}
      <div class="gallery rv">${photo(it.photo, { w: 1400, cls: "main", vt: "hero", eager: true, alt: it.title, tr: `<span class="row" style="gap:8px">${saveBtn()}<button class="save" type="button" aria-label="Report listing" data-act="report">${icon("flag")}</button></span>` })}${photo(it.photo, { w: 600, cls: "side", alt: "" })}${photo(DB.items[(DB.items.indexOf(it) + 3) % DB.items.length].photo, { w: 600, cls: "side", alt: "" })}</div>
      <div class="two-col mt-8"><div>
        <div class="row-wrap rv">${it.restricted ? `<span class="badge violet">${icon("badge-check")}Verified accounts only</span>` : ""}<span class="badge">${icon("map-pin")}${it.lane}, Block C</span><span class="badge">${it.cond}</span></div>
        <h1 class="mt-3 rv" style="font-size:clamp(1.8rem,3.5vw,2.5rem);letter-spacing:-0.04em">${it.title}</h1>
        <div class="facts mt-6" data-stagger><div class="fact">${icon("banknote")}<b>${it.deposit ? rs(it.deposit) : "None"}</b><small>Deposit</small></div><div class="fact">${icon("clock")}<b>${it.max}</b><small>Longest loan</small></div><div class="fact">${icon("handshake")}<b>${it.handover}</b><small>Handover</small></div></div>
        ${it.restricted ? `<div class="card card-2 mt-6 row" id="rx" style="align-items:flex-start">${tone("badge-check", "violet", 36)}<div><b>Verified accounts can request this</b><p class="small muted mt-1">${it.cat === "medical" ? "Medical items" : "High-value electronics"} are limited to members with a verified account. You're verified. <button class="link" type="button" id="unv">See it as an unverified member</button></p></div></div>` : ""}
        <p class="mt-6" style="font-size:17px;max-width:62ch">${it.desc}</p>
        <div class="section"><h2 class="sec-title">Availability</h2><div class="card">${calendar({ blocked: [18, 19, 26], requested: [15, 16] })}</div></div>
        <div class="section"><h2 class="sec-title">${own ? "Your terms" : u.short + "'s terms"}</h2><div class="list">${it.terms.map((t, i) => `<div class="li">${tone(["banknote", "info", "sparkles"][i % 3], ["green", "sky", "saffron"][i % 3], 34)}<span>${t}</span></div>`).join("")}</div>
          <p class="small muted mt-3">${icon("map-pin", "i-sm")} The exact handover spot is shared after ${own ? "you accept" : "the lender accepts"}.</p></div>
        <div class="mob mt-6">${lenderCard}</div></div>
      <aside class="aside stack desk">${cta}${lenderCard}</aside></div>
      ${own ? "" : `<div class="buy-bar">${asked ? cta : `<div class="card"><div class="grow"><div class="xs faint">Deposit</div><b>${it.deposit ? rs(it.deposit) : "None"}</b></div><a class="btn btn-primary req" href="#/request/${it.id}">Request to borrow</a></div>`}</div>`}</div>`,
    after() {
      $("#unv")?.addEventListener("click", () => { $("#rx").innerHTML = `${tone("lock", "violet", 36)}<div><b>Verify your account to request this</b><p class="small muted mt-1">${it.cat === "medical" ? "Medical" : "High-value"} items need a verified phone and community membership. It takes about two minutes. Everything else in Block C is open to you now.</p><a class="btn btn-primary btn-sm mt-3" href="#/settings">Verify my account</a></div>`; $$(".req").forEach(b => { b.setAttribute("aria-disabled", "true"); b.textContent = "Verify to request"; b.href = "#/settings"; }); refreshIcons(); });
      $$("[data-act='report']").forEach(b => b.onclick = () => reportDialog("listing"));
    }
  };
});
function reportDialog(what) {
  dialog(`<h2>Report this ${what}</h2><p class="small muted mt-1">A Block C moderator reviews every report. The person isn't told who reported them.</p>
    <div class="opts mt-6">${[["shield-alert", "Safety concern", "Someone could get hurt"], ["ban", "Prohibited or fake", "Not allowed, or not what it says"], ["copy", "Spam or duplicate", ""], ["circle-help", "Something else", ""]].map(([ic, t, d], i) => `<label class="opt"><input type="radio" name="rr" ${i === 0 ? "checked" : ""}>${tone(ic, "neutral", 34)}<span><strong>${t}</strong>${d ? `<p>${d}</p>` : ""}</span><span class="tick">${icon("check")}</span></label>`).join("")}</div>
    <div class="field mt-4"><label class="label" for="rd">Details (optional)</label><textarea class="textarea" id="rd" style="min-height:80px"></textarea></div>
    <div class="btns mt-4"><button class="btn btn-primary" data-close type="button" onclick="toast('Report sent. Safety reports are reviewed first.')">Send report</button><button class="btn btn-ghost" data-close type="button">Cancel</button></div>`, "Report");
}

/* ---------------- B5: request to borrow ---------------- */
route("/request/:id", ({ id }) => {
  const it = I(id) || I("deg"), u = U(it.lender);
  return {
    title: "Request to borrow", nav: "borrow",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/item/" + it.id, it.title], title: "Request to borrow", sub: `${u.short} gets your request with an evidence report. Nothing is charged.` })}
      <div class="two-col"><div class="stack-lg">
        <div class="card rv"><h3>When do you need it?</h3><p class="small muted mt-1 mb-4" style="margin-bottom:14px">Tap the first day, then the last. Up to ${it.max}.</p>${calendar({ id: "rc", sel: [18, 19], blocked: [24, 25], requested: [19] })}</div>
        <div class="card card-2 row rv" id="ov" style="align-items:flex-start">${tone("users", "saffron", 36)}<div><b class="small">Someone else asked for 19 Oct</b><p class="small muted">You can still ask. Requests don't block dates, and ${u.short} picks one.</p></div></div>
        <div class="card rv"><label class="label" for="msg">Message to ${u.short} <span class="faint" style="font-weight:400">(optional)</span></label><textarea class="textarea" id="msg" maxlength="300">Mehndi at our place on Saturday, cooking for about 35. Can collect after Asr.</textarea><div class="between xs faint mt-1"><span>Say what it's for. It helps.</span><span><span id="cc">72</span>/300</span></div></div>
        <div class="card rv"><h3>Agree to ${u.short}'s terms</h3><div class="mt-2" id="terms">${it.terms.map(t => `<label class="check"><input type="checkbox"><span><span style="color:var(--text)">${t}</span></span></label>`).join("")}</div></div></div>
      <aside class="aside"><div class="card" style="box-shadow:var(--shadow)">
        <div class="row">${photo(it.photo, { w: 200, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:64px;border-radius:14px" class="ph-img ')}<div><b>${it.title}</b><div class="xs faint">${u.name}</div></div></div>
        <div class="divider"></div><div class="between small"><span class="muted">Dates</span><b id="sum">Sat 18 → Sun 19 Oct</b></div><div class="between small mt-2"><span class="muted">Days</span><b id="days">2</b></div><div class="between small mt-2"><span class="muted">Deposit, paid in person</span><b>${it.deposit ? rs(it.deposit) : "None"}</b></div>
        <div class="divider"></div><div class="small" style="font-weight:650;margin-bottom:10px">What happens next</div>${timeline([{ s: "now", t: "We check your membership", d: "Uses your saved result. No new location." }, { s: "todo", t: `${u.short} sees an evidence report`, d: "Replies within 48 hours" }, { s: "todo", t: "You plan the handover in chat" }])}
        <button class="btn btn-primary btn-lg btn-block" id="send" type="button" aria-disabled="true">Send request</button><p class="xs faint center mt-2" id="hint">Tick each term to continue.</p></div></aside></div></div>`,
    after() {
      bindCal("rc", s => { const e = s[1] ?? s[0]; $("#sum").textContent = s.length > 1 ? `${dow(s[0])} ${s[0]} → ${dow(e)} ${e} Oct` : `${dow(s[0])} ${s[0]} Oct…`; $("#days").textContent = e - s[0] + 1; $("#ov").hidden = !(s[0] <= 19 && e >= 19); }, [18, 19]);
      $("#msg").oninput = e => ($("#cc").textContent = e.target.value.length);
      const chk = () => { const ok = $$("#terms input").every(c => c.checked); $("#send").setAttribute("aria-disabled", !ok); $("#hint").textContent = ok ? "Ready to send." : "Tick each term to continue."; };
      $$("#terms input").forEach(c => c.onchange = chk);
      $("#send").onclick = () => { if ($("#send").getAttribute("aria-disabled") === "true") { toast(`Tick each of ${u.short}'s terms first.`, { ic: "info" }); $("#terms input:not(:checked)").focus(); return; } location.hash = `#/request/${it.id}/sent`; };
    }
  };
});
route("/request/:id/sent", ({ id }) => {
  const it = I(id) || I("deg"), u = U(it.lender);
  const st = ["Request created", "Membership confirmed (saved result, no new location)", `Evidence report prepared for ${u.short}`, `Sent to ${u.short}`];
  return {
    title: "Sending request", nav: "activity",
    html: `<div class="wrap wrap-sm"><div id="top" class="center" style="padding-top:48px"><div class="radar on">${icon("send")}</div><h2 class="mt-6">Sending your request…</h2><p class="muted small mt-1">${it.title} · 18–19 Oct</p></div>
      <div class="card mt-8"><ol class="tl" id="steps">${st.map(s => `<li class="todo"><span class="nd"></span><div class="tt">${s}</div></li>`).join("")}</ol></div><div id="out"></div>
      <p class="xs faint center mt-6">Prototype: <button class="link" type="button" id="held">show the “held for review” outcome</button></p></div>`,
    after() {
      const lis = $$("#steps li"); let i = 0, t;
      const tick = () => { if (!document.body.contains(lis[0])) return; lis.forEach((l, j) => { l.className = j < i ? "done" : j === i ? "now" : "todo"; l.querySelector(".nd").innerHTML = j < i ? icon("check") : ""; }); refreshIcons();
        if (i++ < lis.length) { t = setTimeout(tick, 650); return; }
        $("#top").innerHTML = done(`Sent to ${u.short}`, `${u.short} has until Fri 17 Oct, 9 pm to reply. We'll tell you either way.`); $("#out").innerHTML = `<div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="#/activity">Track it in Activity</a><a class="btn btn-outline" href="#/borrow">Keep browsing</a></div>`; refreshIcons(); };
      tick(); cleanup = () => clearTimeout(t);
      $("#held").onclick = () => { clearTimeout(t); $("#top").innerHTML = empty("hourglass", "violet", "A moderator takes a quick look first", `This is a high-value request and there isn't much similar history yet, so a Block C moderator checks it before ${u.short} sees it. It's routine and it's not a rejection. Most reviews finish within a few hours.`); lis.forEach((l, j) => { l.className = j < 2 ? "done" : j === 2 ? "now" : "todo"; }); lis[2].querySelector(".tt").textContent = "Moderator review (Imran or Rabia)"; $("#out").innerHTML = ""; refreshIcons(); };
    }
  };
});

/* ---------------- B9–B11: ask the mohalla (iteration 3) ---------------- */
route("/ask", () => ({
  title: "Ask the mohalla", nav: "borrow",
  html: `<div class="wrap wrap-md">${pageHead({ title: "Ask the mohalla", sub: "Can't find something? Tell neighbours what you need. We suggest fair matches, and nothing is booked until both of you agree." })}${previewBar("Requests, fair matching and saved searches (B9–B11)")}
    <div class="mt-6" data-tabs-scope>${tabs([["post", "New request"], ["matches", "Suggested matches", 2], ["saved", "Saved searches", 3]])}
      <div data-panel="post" class="mt-6"><div class="card card-pad-lg"><div class="field"><label class="label" for="aw">What do you need?</label><input class="input" id="aw" value="Pressure washer"></div>
        <div class="field"><span class="label">When</span><div class="btns"><span class="badge outline" style="height:34px">${icon("calendar")}Wed 22 – Thu 23 Oct</span></div></div>
        <div class="field"><label class="label" for="ad">Details</label><textarea class="textarea" id="ad">To wash the car porch and boundary wall before Eid.</textarea></div>
        <div class="card card-2 mt-4 row" id="dup">${tone("sparkles", "violet", 34)}<div class="grow"><b class="small">Similar already listed</b><div class="xs muted">“Garden hose with spray nozzle” · Kamran J. · free now</div></div><a class="btn btn-outline btn-sm" href="#/item/ladder">View</a></div>
        <button class="btn btn-primary mt-6" type="button" onclick="toast('Posted to Block C. We\\'ll match you fairly.')">Post request</button></div></div>
      <div data-panel="matches" hidden class="mt-6"><div class="card card-2 row mb-4" style="margin-bottom:14px">${tone("scale", "sky", 34)}<p class="small">Matches spread requests across lenders so the same few people aren't asked every time. New members get a small boost. It's only a suggestion until both of you accept.</p></div>
        <div class="stack" data-stagger>${[["makita", "u5", "Same category, free on your dates, 3 min away", "Kamran has 2 other requests this week"], ["ladder", "u5", "Close by, no deposit", "Fairness boost: fewer requests recently"]].map(([iid, uid, w, f]) => `<div class="card row" style="align-items:flex-start">${photo(I(iid).photo, { w: 200, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:72px;border-radius:14px" class="ph-img ')}<div class="grow"><b>${I(iid).title}</b><div class="xs muted mt-1">${icon("sparkles", "i-sm")} ${w}</div><div class="xs faint">${icon("scale", "i-sm")} ${f}</div><div class="btns mt-3"><button class="btn btn-primary btn-sm" type="button" onclick="toast('Match accepted. Waiting for ${U(uid).short}.')">Accept match</button><button class="btn btn-ghost btn-sm" type="button">Not this one</button></div></div></div>`).join("")}</div></div>
      <div data-panel="saved" hidden class="mt-6"><div class="list">${[["Pressure washer", "Alerts on · 0 new"], ["Wedding chairs", "Alerts on · 2 new this week"], ["Kids' bicycle", "Alerts off"]].map(([q, s], i) => `<div class="li">${tone("bell-ring", i === 2 ? "neutral" : "green", 36)}<span class="grow"><span class="t">${q}</span><span class="d">${s}</span></span><label class="switch"><input type="checkbox" ${i < 2 ? "checked" : ""} aria-label="Alerts for ${q}"></label></div>`).join("")}</div></div></div></div>`
}));

screens("Resident · borrowing", [["Home dashboard", "#/home"], ["New member home (cold start)", "#/home/new", "UX-01"], ["Borrow / search (W23)", "#/borrow", "FR-S-01/03"], ["Search: keyword-only (W23)", "#/borrow/fallback", "FR-S-02"], ["Search: loading", "#/borrow/loading", "UX-01"], ["Search: no results", "#/borrow/empty", "UX-01"], ["Search: offline", "#/borrow/error", "UX-01"],
  ["Item details (W24)", "#/item/makita", "FR-S-04"], ["Item: new lender", "#/item/stroller"], ["Item: verified only", "#/item/wheelchair", "FR-B-02"], ["Item: already asked", "#/item/tent", "FR-B-06"], ["Item: your own listing", "#/item/drill"], ["Request to borrow", "#/request/deg", "FR-B-06"], ["Request: live checks", "#/request/deg/sent", "FR-B-07"], ["Ask the mohalla · matches · saved (soon)", "#/ask", "B9–B11"]]);
