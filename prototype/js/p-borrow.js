/* Resident: home, borrow / search (W23, GET /search), item (W24, GET /items/{id}),
   request (B5, POST /requests), ask the mohalla (B9–B11, iteration 3) */

const LIVE = [
  { who: "u2", t: "Request accepted", d: "Bilal accepted your request for the large deg (18–19 Oct).", href: "#/handover/b1/borrower" },
  { who: "u5", t: "Return reminder", d: "The aluminium ladder is due back tomorrow.", href: "#/loan/b2" }
];
const needs = () => DB.loans.filter(l => l.col === "action").map(l => ({ ...l, it: I(l.item), u: U(l.other) }));

function homeView(isNew) {
  const hr = new Date().getHours(), greet = hr < 12 ? "Good morning" : hr < 17 ? "Good afternoon" : "Good evening";
  const n = needs(), bev = DB.myEvidence.roles[0].factors;
  return `<div class="wrap">
    <section class="ph" style="padding-bottom:8px"><div class="between rv">
      <div><button class="badge outline" type="button" data-act="cmdk" style="height:30px">${icon("map-pin")}Block C, Gulberg III${icon("chevron-down")}</button>
        <h1 class="mt-3" style="font-size:clamp(1.9rem,4vw,2.9rem)">${isNew ? "Welcome to Block C, Sana" : `${greet}, Sana`}</h1>
        <p>${isNew ? "Your membership is approved. Here's how to get going." : `${n.length} things need you today · ${new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}`}</p></div>
      <div class="btns desk"><a class="btn btn-outline" href="#/borrow">${icon("search")}Borrow something</a><a class="btn btn-primary" href="#/lend">${icon("plus")}Lend an item</a></div></div></section>

    ${isNew ? `<div class="bento mt-4" data-stagger>
      <div class="card card-pad-lg b4"><div class="between"><h3>Get started</h3><span class="badge green">1 of 3 done</span></div>${stepper(1, 3)}
        <div class="mt-6">${timeline([{ s: "done", t: "Joined Block C", d: "Approved by a moderator after your location check and invitation" }, { s: "now", t: "Borrow something small first", d: "A ladder or books. Each completed loan becomes verified evidence." }, { s: "todo", t: "List one thing you rarely use", d: "Lending gives neighbours more paths to vouch for you." }])}</div>
        <div class="btns"><a class="btn btn-primary" href="#/borrow">Browse Block C</a><a class="btn btn-outline" href="#/invite">${icon("ticket")}Invite a neighbour</a></div></div>
      <div class="card b2 spot">${stateChip("INSUFFICIENT_EVIDENCE")}<h3 class="mt-4">New here isn't bad</h3><p class="small muted mt-2">Lenders see that you have no verified history yet, shown in neutral blue, never red. The engine calls it “not a negative finding”.</p><a class="link small mt-4" style="display:inline-block" href="#/evidence">See my evidence</a></div>
    </div>` : `<div class="bento mt-4" data-stagger>
      <div class="card b4" style="padding:8px"><div class="card-head" style="padding:12px 12px 0"><h3>${icon("bell-ring", "i")}Needs you</h3><a href="#/activity">All activity ${icon("arrow-right", "i-sm")}</a></div>
        <div>${n.map(l => `<a class="li" href="${l.href}" style="border-radius:14px;border:0">${photo(l.it.photo, { w: 140, alt: "" })}<span class="grow"><span class="t">${l.label}</span><span class="d">${l.it.title} · ${l.your_role === "LENDER" ? "to" : "from"} ${l.u.short}. ${l.next}</span></span>${l.mins ? cd(l.mins) : `<span class="badge ${l.tone}">${icon("arrow-right")}</span>`}</a>`).join("")}</div></div>
      <a class="card b2 spot hover" href="#/evidence"><div class="between"><h3>Your evidence</h3>${icon("arrow-up-right", "i faint")}</div><p class="xs faint mt-1">As a borrower · 7 verified loans</p>${factorList(bev.slice(0, 2))}</a>
      <a class="card b2 spot hover" href="#/loan/b2"><div class="between"><h3>Out with you</h3><span class="badge green">2 items</span></div><div class="row mt-4">${photo(I("ladder").photo, { w: 140, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:52px;border-radius:12px" class="ph-img ')}<div class="grow"><b class="small">Aluminium ladder</b><div class="xs faint">Return by Wed 15 Oct</div></div></div><div class="mt-4">${stepper(3)}</div><p class="xs faint mt-3">${icon("alarm-clock", "i-sm")} Physics books are 1 day overdue</p></a>
      <div class="card b2"><div class="between"><h3>Community pulse</h3><span class="badge green"><span class="live"></span>Live</span></div><div id="pulse" class="mt-3" style="height:172px;overflow:hidden;mask-image:linear-gradient(#000 70%,transparent);-webkit-mask-image:linear-gradient(#000 70%,transparent)"></div></div>
      <a class="card b2 hover" href="#/event/e1" style="padding:0;overflow:hidden">${photo(DB.events[0].photo, { w: 600, ratio: "16/9", alt: "", tl: soon(), shade: true, bl: `<b>${DB.events[0].t}</b><div class="xs" style="opacity:.85">Sat 18 Oct · ${DB.events[0].where}</div>` })}<div style="padding:12px 16px" class="between"><span class="small muted">Events arrive in iteration 3</span>${icon("arrow-up-right", "i faint")}</div></a>
      <a class="card b2 hover spot" href="#/invite"><div class="between">${tone("ticket", "saffron")}<span class="badge">${DB.invitations.filter(i => !i.used).length} of 3 open</span></div><h3 class="mt-4">Invite a neighbour</h3><p class="small muted mt-2">Invitations are one of the two signals that let a neighbour join Block C.</p></a>
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

/* ---------------- W23: borrow / search ----------------
   GET /search?q&category&community&from&to&max_deposit&condition&sort&page -> SearchOut.
   mode HYBRID | KEYWORD_ONLY; each SearchResultOut has a plain-words `reason`, `same_community`,
   `available` (when dates are given) and the lender's evidence. Scores are never returned. */
const resultRow = (it, ix = 0, other = false) => `<a class="card hover spot rv" href="#/item/${it.id}" data-vt style="padding:12px;display:flex;gap:16px;--d:${ix}">
  ${photo(it.photo, { w: 360, alt: it.title }).replace('class="ph-img ', 'style="width:clamp(96px,22vw,150px);flex:none;border-radius:14px" class="ph-img ')}
  <div class="grow" style="display:flex;flex-direction:column;gap:6px;padding:4px 0">
    <div class="between" style="align-items:flex-start"><h3 style="font-size:16px">${it.title}</h3>${saveBtn()}</div>
    <div class="small muted">${cat(it.category_id).label} · ${CONDITION[it.condition]} · ${it.deposit ? rs(it.deposit) + " deposit" : "No deposit"}</div>
    <div class="row-wrap">${evTag(it.lender)}${other ? `<span class="badge outline">${icon("map")}Main Market Lanes</span>` : ""}${it.booked.length ? `<span class="badge saffron">${icon("calendar-x")}${availText(it)}</span>` : `<span class="badge">${icon("calendar-check")}Free on your dates</span>`}</div>
    <div class="xs muted row" style="gap:6px;margin-top:auto">${icon("sparkles", "i-sm")}<span><span class="sr">Why this result: </span>${it.reason}</span></div></div></a>`;
const sk = n => Array.from({ length: n }, () => `<div class="card" style="padding:12px;display:flex;gap:16px" aria-hidden="true"><div class="sk" style="width:130px;height:100px;border-radius:14px"></div><div class="grow stack"><div class="sk" style="height:16px;width:60%"></div><div class="sk" style="height:12px;width:40%"></div><div class="sk" style="height:22px;width:50%;border-radius:20px"></div></div></div>`).join("");
const filters = () => `<div class="stack-lg">
  <div><div class="label">Category</div><div class="stack" style="gap:2px">${DB.categories.slice(1).map((c, i) => `<label class="check" style="padding:7px 0;border:0"><input type="radio" name="fc" ${i === 0 ? "checked" : ""}><span><span style="color:var(--text)">${c.label}</span>${c.is_restricted ? ' <span class="xs faint">· verified only</span>' : ""}</span></label>`).join("")}</div></div>
  <div><div class="label">Dates you need it</div><div class="grid-2" style="gap:8px"><input class="input" type="date" value="2026-10-14" aria-label="From"><input class="input" type="date" value="2026-10-17" aria-label="Return by"></div><span class="help">Booked items are left out when you give dates.</span></div>
  <div><label class="label" for="dep">Highest deposit</label><input class="range" type="range" id="dep" min="0" max="10000" step="500" value="5000"><span class="help" id="depv">Up to Rs 5,000</span></div>
  <div><div class="label">Condition</div><div class="chips" data-chips style="flex-wrap:wrap"><button class="chip" type="button" aria-pressed="true">Any</button>${Object.values(CONDITION).map(c => `<button class="chip" type="button" aria-pressed="false">${c}</button>`).join("")}</div></div>
  <div><div class="label">Community</div>${seg([["mine", "Block C"], ["all", "All mine"]])}<span class="help">Items from other communities you belong to are marked.</span></div></div>`;
function borrowView(mode) {
  const q = mode === "empty" ? "pressure washer" : "drill";
  let body;
  if (mode === "loading") body = `<div class="stack" role="status" aria-label="Loading results">${sk(4)}</div>`;
  else if (mode === "empty") body = empty("search-x", "neutral", "No pressure washers in Block C yet", "Nobody has listed one. Try a broader word. Asking the mohalla for something, and alerts for new listings, arrive in iteration 3.", `<a class="btn btn-outline" href="#/ask">${icon("megaphone")}Ask the mohalla ${soon("Soon")}</a>`) + `<h3 class="mt-6" style="margin-bottom:12px">Free on your dates anyway</h3><div class="stack">${resultRow(I("ladder"))}</div>`;
  else if (mode === "error") body = empty("wifi-off", "coral", "You're offline", "Your search runs again as soon as you're back. Nothing you typed is lost.", `<a class="btn btn-primary" href="#/borrow">${icon("rotate-cw")}Try again</a>`);
  else body = `${mode === "fallback" ? `<div class="card card-2 row" style="margin-bottom:16px">${tone("zap-off", "saffron", 36)}<div><b class="small">Showing keyword matches only</b><p class="xs muted">Meaning-based search is unavailable right now (mode KEYWORD_ONLY), so results match your exact words. Similar items like “screwdriver” may be missed.</p></div></div>` : ""}
    <div class="stack">${resultRow(I("makita"))}</div><h3 class="mt-8" style="margin-bottom:12px">Also free on your dates</h3><div class="stack">${["ladder", "tent", "chairs"].map((id, i) => resultRow(I(id), i + 1)).join("")}${resultRow(I("books"), 4, true)}</div>`;
  return {
    title: "Borrow", nav: "borrow",
    html: `<div class="wrap">${pageHead({ title: "Borrow", sub: "Ranked by how well it matches, whether it's free on your dates, and the lender's history in words. New lenders are shown at the community baseline, never pushed down." })}
      <form class="input-wrap rv" id="sf" role="search">${icon("search")}<input class="input" id="q" value="${q}" maxlength="200" style="height:56px;font-size:17px;border-radius:16px;padding-right:130px" aria-label="Search" enterkeyhint="search"><span class="addon btns"><button class="btn btn-outline btn-sm mob" type="button" id="fbtn" aria-label="Filters">${icon("sliders-horizontal")}</button><button class="btn btn-primary btn-sm" type="submit">Search</button></span></form>
      <p class="xs faint mt-2 rv">Roman Urdu works too, for example “deg”, “seedhi” or “barma”.</p>
      <div class="two-col left mt-6"><aside class="aside desk"><div class="card">${filters()}</div><div class="card card-2 mt-4"><b class="small">${icon("lock", "i-sm")} No exact locations</b><p class="xs muted mt-1">Results say whether an item is in your community, never how far away it is.</p></div></aside>
        <div><div class="between" style="margin-bottom:14px;flex-wrap:wrap"><span class="small"><b id="cnt">${mode === "empty" || mode === "error" ? "0 results" : mode === "loading" ? "Searching…" : "5 results"}</b> <span class="faint">· 14–16 Oct${mode === "fallback" ? " · keyword only" : ""}</span></span>${seg([["relevance", "Best match"], ["evidence", "Lender history"], ["newest", "Newest"]])}</div>
          <div id="res">${body}</div>
          <div class="card card-2 mt-6 small"><b>Try a state:</b> <span class="row-wrap mt-2">${[["Results", "#/borrow"], ["Keyword only", "#/borrow/fallback"], ["Loading", "#/borrow/loading"], ["No results", "#/borrow/empty"], ["Offline", "#/borrow/error"]].map(([l, h]) => `<a class="chip" href="${h}">${l}</a>`).join("")}</span></div></div></div></div>`,
    after() {
      $("#sf").onsubmit = e => { e.preventDefault(); const v = $("#q").value.toLowerCase(); $("#res").innerHTML = `<div class="stack" role="status" aria-label="Loading">${sk(3)}</div>`; $("#cnt").textContent = "Searching…"; setTimeout(() => { location.hash = v.includes("washer") ? "#/borrow/empty" : "#/borrow"; if (!v.includes("washer")) render(); }, 900); };
      $("#fbtn").onclick = () => { dialog(`<div class="between"><h2>Filters</h2><button class="btn btn-ghost btn-sm" type="button">Reset</button></div><div class="mt-6">${filters()}</div><button class="btn btn-primary btn-block mt-6" data-close type="button">Show results</button>`, "Filters"); bindDep(); };
      bindDep();
      if (mode === "loading") { const t = setTimeout(() => (location.hash = "#/borrow"), 1800); cleanup = () => clearTimeout(t); }
    }
  };
}
function bindDep() { $$("#dep").forEach(r => (r.oninput = e => ($("#depv").textContent = "Up to " + rs(e.target.value)))); }
route("/borrow", () => borrowView("results"));
route("/borrow/:mode", ({ mode }) => borrowView(mode));

/* ---------------- W24: item details (GET /items/{id} -> ItemOut) ---------------- */
route("/item/:id", ({ id }) => {
  const it = I(id) || I("makita"), u = U(it.lender), ev = DB.lenderEv[it.lender], own = it.lender === "u0", asked = id === "wheelchair";
  const lenderCard = own ? `<div class="card"><div class="between"><h3>Your listing</h3><span class="status green live">Published</span></div><p class="small muted mt-2">Expires in 52 days · 1 request waiting</p><div class="btns mt-4"><a class="btn btn-primary btn-sm" href="#/requests/r1">See Ayesha's request</a><a class="btn btn-outline btn-sm" href="#/lend/edit">${icon("pencil")}Edit</a></div></div>`
    : `<div class="card spot"><div class="between"><div class="row">${av(it.lender, "lg")}<div><div class="xs faint">Lent by</div><b>${u.name}</b><div class="xs faint">Block C · since ${u.since}</div></div></div><a class="icon-btn" href="#/inbox" aria-label="Message ${u.short}">${icon("message-circle")}</a></div>
      <div class="divider"></div><div class="between"><b class="small">Lending history</b>${evTag(it.lender)}</div><p class="small muted mt-2">${ev.summary}</p>${factorList(ev.factors)}
      <p class="xs faint mt-3">${icon("info", "i-sm")} From verified, completed loans only. Each factor on its own, never one score.</p></div>`;
  const cta = own ? "" : asked ? `<div class="card card-2 row">${tone("hourglass", "violet", 36)}<div class="grow"><b class="small">You already asked</b><div class="xs muted">25 Oct–1 Nov · with a moderator</div></div><a class="btn btn-outline btn-sm" href="#/loan/b14">View</a></div>`
    : `<div class="card" style="box-shadow:var(--shadow)"><div class="between"><div><div class="xs faint">Deposit, paid in person</div><div class="kpi" style="font-size:1.6rem">${it.deposit ? rs(it.deposit) : "None"}</div></div><span class="badge green">${icon("calendar-check")}${availText(it)}</span></div>
      <a class="btn btn-primary btn-lg btn-block mt-4 req" href="#/request/${it.id}">Request to borrow</a><p class="xs faint center mt-2">Nothing is charged. ${u.short} sees an evidence report first.</p></div>`;
  return {
    title: it.title, nav: "borrow",
    html: `<div class="wrap">${pageHead({ crumbs: [["Borrow", "#/borrow"], [cat(it.category_id).label, "#/borrow"], [it.title]], title: "" }).replace("<h1></h1>", "")}
      <div class="gallery rv">${photo(it.photo, { w: 1400, cls: "main", vt: "hero", eager: true, alt: it.title, tr: `<span class="row" style="gap:8px">${saveBtn()}<button class="save" type="button" aria-label="Report listing" data-rep>${icon("flag")}</button></span>` })}${photo(it.photo, { w: 600, cls: "side", alt: "" })}${photo(DB.items[(DB.items.indexOf(it) + 3) % DB.items.length].photo, { w: 600, cls: "side", alt: "" })}</div>
      <div class="two-col mt-8"><div>
        <div class="row-wrap rv">${restricted(it) ? `<span class="badge violet">${icon("badge-check")}Community-verified members only</span>` : ""}<span class="badge">${icon("map-pin")}Block C</span><span class="badge">${cat(it.category_id).label}</span></div>
        <h1 class="mt-3 rv" style="font-size:clamp(1.8rem,3.5vw,2.5rem);letter-spacing:-0.04em">${it.title}</h1>
        <div class="facts mt-6" data-stagger><div class="fact">${icon("banknote")}<b>${it.deposit ? rs(it.deposit) : "None"}</b><small>Deposit</small></div><div class="fact">${icon("gem")}<b>${BAND_SHORT[it.value_band]}</b><small>${BAND[it.value_band]}</small></div><div class="fact">${icon("sparkle")}<b>${CONDITION[it.condition]}</b><small>Condition</small></div></div>
        ${restricted(it) ? `<div class="card card-2 mt-6 row" id="rx" style="align-items:flex-start">${tone("badge-check", "violet", 36)}<div><b>Community-verified members can request this</b><p class="small muted mt-1">${cat(it.category_id).label} is a restricted category (FR-B-02). Your membership is approved, so you can ask. <button class="link" type="button" id="unv">See it as a member who isn't verified yet</button></p></div></div>` : ""}
        <p class="mt-6" style="font-size:17px;max-width:62ch">${it.desc}</p>
        <div class="section"><h2 class="sec-title">Already booked</h2><div class="card">${calendar({ blocked: it.booked })}</div><p class="xs faint mt-2">Dates others asked for but the lender hasn't accepted stay free: requests never block dates until accepted.</p></div>
        <div class="section"><h2 class="sec-title">${own ? "Your terms" : u.short + "'s terms"}</h2><div class="list"><div class="li">${tone("scroll-text", "sky", 34)}<span><span class="t">How to use it</span><span class="d">${it.usage_terms}</span></span></div><div class="li">${tone("handshake", "green", 34)}<span><span class="t">Handover</span><span class="d">${it.handover_method}. The exact spot is shared in chat after ${own ? "you accept" : "the lender accepts"}.</span></span></div>${it.deposit ? `<div class="li">${tone("banknote", "saffron", 34)}<span><span class="t">Deposit</span><span class="d">${rs(it.deposit)}, paid in person and recorded in the app at handover. The app never holds money.</span></span></div>` : ""}</div></div>
        <div class="mob mt-6">${lenderCard}</div></div>
      <aside class="aside stack desk">${cta}${lenderCard}</aside></div>
      ${own ? "" : `<div class="buy-bar">${asked ? cta : `<div class="card"><div class="grow"><div class="xs faint">Deposit</div><b>${it.deposit ? rs(it.deposit) : "None"}</b></div><a class="btn btn-primary req" href="#/request/${it.id}">Request to borrow</a></div>`}</div>`}</div>`,
    after() {
      $("#unv")?.addEventListener("click", () => { $("#rx").innerHTML = `${tone("lock", "violet", 36)}<div><b>Join request still pending</b><p class="small muted mt-1">Restricted categories need a community-verified member. Your request to join Block C is with a moderator. Everything else is open to you once you're approved.</p></div>`; $$(".req").forEach(b => { b.setAttribute("aria-disabled", "true"); b.textContent = "Needs an approved membership"; b.removeAttribute("href"); }); refreshIcons(); });
      $("[data-rep]")?.addEventListener("click", () => reportDialog("listing"));
    }
  };
});
function reportDialog(what) {
  dialog(`<h2>Report this ${what}</h2>${previewBar("Reporting (D7)")}<p class="small muted mt-4">A Block C moderator reviews every report. The person isn't told who reported them.</p>
    <div class="opts mt-4">${[["shield-alert", "Safety concern", "Someone could get hurt"], ["ban", "Prohibited or fake", "Not allowed, or not what it says"], ["copy", "Spam or duplicate", ""], ["circle-help", "Something else", ""]].map(([ic, t, d], i) => `<label class="opt"><input type="radio" name="rr" ${i === 0 ? "checked" : ""}>${tone(ic, "neutral", 34)}<span><strong>${t}</strong>${d ? `<p>${d}</p>` : ""}</span><span class="tick">${icon("check")}</span></label>`).join("")}</div>
    <div class="btns mt-6"><button class="btn btn-primary" data-close type="button" onclick="toast('Report sent. Safety reports are reviewed first.')">Send report</button><button class="btn btn-ghost" data-close type="button">Cancel</button></div>`, "Report");
}

/* ---------------- B5: request to borrow (POST /requests: item_id, start_date, end_date, message) ----------------
   end_date is exclusive: the item is back by that day. message up to 500 characters. */
route("/request/:id", ({ id }) => {
  const it = I(id) || I("deg"), u = U(it.lender);
  return {
    title: "Request to borrow", nav: "borrow",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/item/" + it.id, it.title], title: "Request to borrow", sub: `${u.short} gets your request with an evidence report. Nothing is charged.` })}
      <div class="two-col"><div class="stack-lg">
        <div class="card rv"><h3>When do you need it?</h3><p class="small muted mt-1" style="margin-bottom:14px">Tap the day you collect it, then the day it comes back.</p>${calendar({ id: "rc", sel: [21, 23], blocked: it.booked })}</div>
        <div class="card card-2 row rv" style="align-items:flex-start">${tone("info", "sky", 36)}<div><b class="small">Requests don't block dates</b><p class="small muted">Others may ask for the same days. Whoever ${u.short} accepts first gets them, and the rest are told the dates are taken.</p></div></div>
        <div class="card rv"><label class="label" for="msg">Message to ${u.short} <span class="faint" style="font-weight:400">(optional)</span></label><textarea class="textarea" id="msg" maxlength="500">Mehndi at our place on Wednesday, cooking for about 35. Can collect after Asr.</textarea><div class="between xs faint mt-1"><span>Say what it's for. No phone numbers or addresses.</span><span><span id="cc">74</span>/500</span></div></div>
        <div class="card rv"><h3>${u.short}'s terms</h3><p class="small mt-2">${it.usage_terms}</p><p class="small muted mt-2">${it.handover_method}${it.deposit ? ` · ${rs(it.deposit)} deposit in person` : ""}</p><label class="check mt-2"><input type="checkbox" id="ok"><span><span style="color:var(--text)">I've read the terms</span></span></label></div></div>
      <aside class="aside"><div class="card" style="box-shadow:var(--shadow)">
        <div class="row">${photo(it.photo, { w: 200, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:64px;border-radius:14px" class="ph-img ')}<div><b>${it.title}</b><div class="xs faint">${u.name}</div></div></div>
        <div class="divider"></div><div class="between small"><span class="muted">Collect</span><b id="s1">Tue 21 Oct</b></div><div class="between small mt-2"><span class="muted">Back by</span><b id="s2">Thu 23 Oct</b></div><div class="between small mt-2"><span class="muted">Deposit, in person</span><b>${it.deposit ? rs(it.deposit) : "None"}</b></div>
        <div class="divider"></div><div class="small" style="font-weight:650;margin-bottom:10px">What happens next</div>${timeline([{ s: "now", t: "Your membership is checked", d: "From your saved result. No new location is taken." }, { s: "todo", t: "The engine prepares an evidence report", d: `Or a moderator checks it first, for some requests` }, { s: "todo", t: `${u.short} replies within 72 hours`, d: "Accept, decline or suggest other dates" }])}
        <button class="btn btn-primary btn-lg btn-block" id="send" type="button" aria-disabled="true">Send request</button><p class="xs faint center mt-2" id="hint">Tick “I've read the terms” to continue.</p></div></aside></div></div>`,
    after() {
      bindCal("rc", s => { const e = s[1] ?? s[0]; $("#s1").textContent = `${dow(s[0])} ${s[0]} Oct`; $("#s2").textContent = s.length > 1 ? `${dow(e)} ${e} Oct` : "Pick a day"; }, [21, 23]);
      $("#msg").oninput = e => ($("#cc").textContent = e.target.value.length);
      $("#ok").onchange = e => { $("#send").setAttribute("aria-disabled", !e.target.checked); $("#hint").textContent = e.target.checked ? "Ready to send." : "Tick “I've read the terms” to continue."; };
      $("#send").onclick = () => { if ($("#send").getAttribute("aria-disabled") === "true") { toast("Tick “I've read the terms” first.", { ic: "info" }); return; } location.hash = `#/request/${it.id}/sent`; };
    }
  };
});
/* POST /requests -> CommandOut { state, hold_reason }. ASSESSED reaches the lender; HELD_FOR_REVIEW waits
   for a moderator with one of five hold reasons (ADR-0003). Never an automatic rejection. */
const HELD_TEXT = {
  high_value_low_confidence: ["gem", "This is a high-value item and there isn't much similar history yet, so a Block C moderator checks the request first."],
  manipulation_risk: ["radar", "Two automatic checks found an unusual rating pattern. A moderator looks at it before the lender does. A signal is not proof of anything."],
  locality_inconclusive: ["map-pin", "Your saved location result is unclear, so a moderator confirms your membership first."],
  locality_conflict: ["map-pin-off", "Your saved location result conflicts with the community, so a moderator confirms your membership first."],
  engine_failure: ["server-crash", "The evidence report couldn't be prepared in time. A moderator will run it again. Nothing was assumed about you."]
};
route("/request/:id/sent", ({ id }) => {
  const it = I(id) || I("deg"), u = U(it.lender);
  const st = [["REQUEST_CREATED", "Request created"], ["LOCALITY_CHECKED", "Membership confirmed from your saved result"], ["ASSESSED", `Evidence report prepared for ${u.short}`]];
  return {
    title: "Sending request", nav: "activity",
    html: `<div class="wrap wrap-sm"><div id="top" class="center" style="padding-top:48px"><div class="radar on">${icon("send")}</div><h2 class="mt-6">Sending your request…</h2><p class="muted small mt-1">${it.title} · 21–23 Oct</p></div>
      <div class="card mt-8"><ol class="tl" id="steps">${st.map(([k, s]) => `<li class="todo"><span class="nd"></span><div class="tt">${s}</div><div class="td mono">${k}</div></li>`).join("")}</ol></div><div id="out"></div>
      <div class="card card-2 mt-6"><b class="small">Prototype: other outcomes (HELD_FOR_REVIEW)</b><div class="row-wrap mt-3">${Object.keys(HELD_TEXT).map(k => `<button class="chip" type="button" data-hold="${k}">${k}</button>`).join("")}</div></div></div>`,
    after() {
      const lis = $$("#steps li"); let i = 0, t;
      const tick = () => { if (!document.body.contains(lis[0])) return; lis.forEach((l, j) => { l.className = j < i ? "done" : j === i ? "now" : "todo"; l.querySelector(".nd").innerHTML = j < i ? icon("check") : ""; }); refreshIcons();
        if (i++ < lis.length) { t = setTimeout(tick, 650); return; }
        $("#top").innerHTML = done(`Sent to ${u.short}`, `${u.short} has 72 hours to reply. If there's no reply, the request expires and you're told.`); $("#out").innerHTML = `<div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="#/activity">Track it in Activity</a><a class="btn btn-outline" href="#/borrow">Keep browsing</a></div>`; refreshIcons(); };
      tick(); cleanup = () => clearTimeout(t);
      $$("[data-hold]").forEach(b => b.onclick = () => { clearTimeout(t); const [ic, txt] = HELD_TEXT[b.dataset.hold];
        $("#top").innerHTML = empty(ic, "violet", "A moderator takes a look first", `${txt} It's routine and it isn't a rejection. You can still cancel the request while you wait.`);
        lis.forEach((l, j) => { l.className = j < 1 ? "done" : j === 1 ? "now" : "todo"; }); lis[1].querySelector(".tt").textContent = "With a Block C moderator"; lis[1].querySelector(".td").textContent = `HELD_FOR_REVIEW · ${b.dataset.hold}`;
        $("#out").innerHTML = `<div class="btns mt-6" style="justify-content:center"><a class="btn btn-outline" href="#/activity">Back to Activity</a></div>`; refreshIcons(); });
    }
  };
});

/* ---------------- B9–B11: ask the mohalla (iteration 3; no endpoints yet) ---------------- */
route("/ask", () => ({
  title: "Ask the mohalla", nav: "borrow",
  html: `<div class="wrap wrap-md">${pageHead({ title: "Ask the mohalla", sub: "Can't find something? Tell neighbours what you need. Fair matches are suggested, and nothing is booked until both of you agree." })}${previewBar("Item requests, fair matching and saved searches (B9–B11, FR-S-06 to S-09)")}
    <div class="mt-6" data-tabs-scope>${tabs([["post", "New request"], ["matches", "Suggested matches", 2], ["saved", "Saved searches", 3]])}
      <div data-panel="post" class="mt-6"><div class="card card-pad-lg"><div class="field"><label class="label" for="aw">What do you need?</label><input class="input" id="aw" value="Pressure washer"></div>
        <div class="field"><label class="label" for="ad">Details</label><textarea class="textarea" id="ad">To wash the car porch and boundary wall before Eid.</textarea></div>
        <button class="btn btn-primary mt-6" type="button" onclick="toast('Posted to Block C')">Post request</button></div></div>
      <div data-panel="matches" hidden class="mt-6"><div class="card card-2 row" style="margin-bottom:14px">${tone("scale", "sky", 34)}<p class="small">Matching spreads requests across lenders so the same few people aren't asked every time. It's only a suggestion until both of you accept.</p></div>
        <div class="stack">${[["makita", "u5", "Same category and free on your dates"], ["ladder", "u5", "In your community, no deposit"]].map(([iid, uid, w]) => `<div class="card row" style="align-items:flex-start">${photo(I(iid).photo, { w: 200, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:72px;border-radius:14px" class="ph-img ')}<div class="grow"><b>${I(iid).title}</b><div class="xs muted mt-1">${icon("sparkles", "i-sm")} ${w}</div><div class="btns mt-3"><button class="btn btn-primary btn-sm" type="button" onclick="toast('Match accepted. Waiting for ${U(uid).short}.')">Accept match</button><button class="btn btn-ghost btn-sm" type="button">Not this one</button></div></div></div>`).join("")}</div></div>
      <div data-panel="saved" hidden class="mt-6"><div class="list">${[["Pressure washer", "Alerts on"], ["Wedding chairs", "Alerts on · 2 new"], ["Kids' bicycle", "Alerts off"]].map(([q, s], i) => `<div class="li">${tone("bell-ring", i === 2 ? "neutral" : "green", 36)}<span class="grow"><span class="t">${q}</span><span class="d">${s}</span></span><label class="switch"><input type="checkbox" ${i < 2 ? "checked" : ""} aria-label="Alerts for ${q}"></label></div>`).join("")}</div></div></div></div>`
}));

screens("Resident · borrowing", [["Home", "#/home"], ["New member home", "#/home/new", "UX-01"], ["Borrow / search (W23)", "#/borrow", "GET /search"], ["Search: keyword only", "#/borrow/fallback", "mode KEYWORD_ONLY"], ["Search: loading", "#/borrow/loading", "UX-01"], ["Search: no results", "#/borrow/empty", "UX-01"], ["Search: offline", "#/borrow/error", "UX-01"],
  ["Item details (W24)", "#/item/makita", "GET /items/{id}"], ["Item: new lender", "#/item/stroller", "LenderEvidenceOut"], ["Item: too few loans", "#/item/wheelchair", "FR-T-08"], ["Item: restricted category", "#/item/projector", "FR-B-02"], ["Item: your own listing", "#/item/drill", "is_yours"], ["Request to borrow", "#/request/deg", "POST /requests"], ["Request sent / held (5 hold reasons)", "#/request/deg/sent", "ADR-0003"], ["Ask the mohalla (soon)", "#/ask", "B9–B11"]]);
