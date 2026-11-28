/* Lending and the loan lifecycle, aligned to the iteration 2 API (iteration2/slice3):
   activity (GET /requests, /lender/requests), lender decision (W1, W2: GET /requests/{id}, accept, decline),
   counter-offer (W14: /counter-offer, accept, decline), loan journey (GET /transactions/{id}/events),
   handover (W3a, W3b, W17: handover/checklist, handover/confirm, photos), extension (W13), return (W4: return,
   return/confirm), dispute (W5: /dispute, withdraw, GET /dispute), statement (W18), appeal (W20: /cases/{id}/appeal),
   review (W15: /review), listings (W22: POST/PATCH /items, GET /me/items) */

const L = id => DB.loans.find(x => x.id === id) || DB.loans[0];
const T = DB.timers;
const itemHead = (it, sub) => `<div class="card row">${photo(it.photo, { w: 200, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:60px;border-radius:14px" class="ph-img ')}<div class="grow"><b>${it.title}</b><div class="small muted">${sub}</div></div></div>`;
const resultPage = (t, d, href, label) => `<div class="wrap wrap-sm">${done(t, d)}<div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="${href}">${label}</a><a class="btn btn-outline" href="#/activity">Activity</a></div></div>`;
const swap = html => { $("#view").innerHTML = html; hydrate($("#view")); window.scrollTo(0, 0); };
const counter = (id, max) => `<span><span id="${id}">0</span>/${max}</span>`;
const bindCount = (inp, out) => { const el = $(inp); if (!el) return; const f = () => ($(out).textContent = el.value.length); el.addEventListener("input", f); f(); };
/* API end_date is exclusive: [14, 17] means 14, 15 and 16 Oct, back by the 17th */
const span = d => `${d[0]}–${d[1] - 1} Oct`;
const nDays = d => d[1] - d[0];
/* GET /transactions/{id}/events: what the journey timeline is built from */
const evRow = (s, t, d, ev) => ({ s, t, d: `${d}${ev ? ` <span class="mono faint">· ${ev}</span>` : ""}` });

/* ---------------- Activity board ---------------- */
const loanCard = l => { const it = I(l.item), u = U(l.other), ended = l.step < 0 || l.col === "done";
  return `<a class="loan" href="${l.href}"><div class="top">${photo(it.photo, { w: 160, alt: "" })}<div class="grow"><div class="nm">${it.title}</div><div class="who">${av(l.other, "xs")}${l.your_role === "LENDER" ? "To" : "From"} ${u.short} · ${l.dates}</div></div></div>
    ${ended ? "" : `<div class="mt-3">${stepper(l.step, 6, l.tone === "coral")}</div>`}<div class="nx"><span class="status ${l.tone} ${l.col === "action" ? "live" : ""}">${l.label}</span>${l.mins && !ended ? cd(l.mins) : `<span class="xs faint">${LC[l.state] || ""}</span>`}</div></a>`; };
route("/activity", () => {
  const cols = [["action", "Needs you", "bell-ring", "saffron"], ["waiting", "Waiting on others", "hourglass", "sky"], ["active", "Out on loan", "package", "green"], ["done", "History", "history", "neutral"]];
  const board = role => `<div class="board mt-6" data-stagger>${cols.map(([k, t, ic, tn]) => { const ls = DB.loans.filter(l => l.col === k && (role === "all" || l.your_role === role)); return `<div class="col"><div class="col-h">${tone(ic, tn, 26)}${t}<span class="n">${ls.length}</span></div>${ls.map(loanCard).join("") || `<p class="xs faint center" style="padding:24px 0">Nothing here</p>`}</div>`; }).join("")}</div>`;
  const n = r => DB.loans.filter(l => l.your_role === r).length;
  return {
    title: "Activity", nav: "activity",
    html: `<div class="wrap">${pageHead({ title: "Activity", sub: "Every loan you're part of, grouped by what needs doing.", actions: `<a class="btn btn-outline" href="#/listings">${icon("package")}My listings</a><a class="btn btn-primary" href="#/lend">${icon("plus")}Lend an item</a>` })}
      <div data-tabs-scope>${tabs([["all", "All", DB.loans.length], ["b", "Borrowing", n("BORROWER")], ["l", "Lending", n("LENDER")]])}
        <div data-panel="all">${board("all")}</div><div data-panel="b" hidden>${board("BORROWER")}</div><div data-panel="l" hidden>${board("LENDER")}</div></div></div>`
  };
});

/* ---------------- W1, W2: lender decides (RequestOut + AssessmentOut) ---------------- */
route("/requests/:id", ({ id }) => {
  const r = DB.requests[id] || DB.requests.r1, it = I(r.item), u = U(r.borrower), fn = u.short, a = r.assessment;
  const act = `<div class="btns"><button class="btn btn-primary grow" type="button" data-acc>${icon("check")}Accept</button><button class="btn btn-outline grow" type="button" data-dec>Decline</button></div><button class="btn btn-ghost btn-block mt-2" type="button" data-ctr>${icon("calendar-range")}Suggest other dates</button>`;
  return {
    title: "Request from " + fn, nav: "activity",
    html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: `${fn} wants to borrow your ${it.noun}`, sub: `${span(r.dates)} · ${nDays(r.dates)} days · back by ${r.dates[1]} Oct · ${it.deposit ? rs(it.deposit) + " deposit" : "no deposit"}`, actions: cd(r.expires) })}
      <div class="two-col"><div class="stack-lg">
        <div class="card card-pad-lg rv"><div class="row">${av(r.borrower, "xl")}<div><h2 style="font-size:1.3rem">${u.name}</h2><p class="small muted">Block C · member since ${u.since}</p></div></div>${r.message ? `<p class="mt-6" style="font-size:18px;line-height:1.5;letter-spacing:-0.01em">“${r.message}”</p>` : ""}</div>
        ${r.overlap ? `<div class="card card-2 row rv" style="align-items:flex-start">${tone("users", "saffron", 36)}<div><b class="small">${r.overlap.who} also asked for ${r.overlap.dates}</b><p class="small muted">Accepting ${fn} books these dates. ${r.overlap.who}'s request is then declined with “dates taken”.</p></div></div>` : ""}
        <div class="rv">${evidence(r, { name: fn })}</div></div>
      <aside class="aside stack">${itemHead(it, "Your listing")}<div class="card"><h3>Your decision</h3><p class="small muted mt-1" style="margin-bottom:14px">You have ${T.responseWindowH} hours from the request. With no reply it expires and ${fn} is told.</p>${act}</div>
        <div class="card card-2 small">${icon("info", "i-sm")} Requests don't block dates until you accept one.</div></aside></div>
      <div class="dock mob"><div class="card">${act}</div></div></div>`,
    after() {
      const h = e => {
        if (e.target.closest("[data-acc]")) dialog(`<h2>Accept ${fn}'s request?</h2>
          <div class="list mt-6"><div class="li">${tone("calendar-check", "green", 34)}<span class="small">${span(r.dates)} are booked for your ${it.noun}</span></div>${r.overlap ? `<div class="li">${tone("user-x", "saffron", 34)}<span class="small">${r.overlap.who}'s overlapping request is declined: dates taken</span></div>` : ""}<div class="li">${tone("message-circle", "sky", 34)}<span class="small">A chat with ${fn} opens to plan the handover</span></div></div>
          <div class="card card-2 mt-4"><b class="small">Safeguards for this loan</b>${a.safeguards.map(s => `<div class="row small mt-2">${icon("check", "i-sm")}${s.label}</div>`).join("")}<p class="xs faint mt-2">Suggested by the engine (rule ${a.rule_fired}). Recording the deposit and the handover checklist is part of the handover step.</p></div>
          <div class="btns mt-6"><button class="btn btn-primary" type="button" id="ok">Accept request</button><button class="btn btn-ghost" data-close type="button">Not yet</button></div>
          <p class="xs faint mt-4">Prototype: <button class="link" type="button" id="race">simulate “dates already taken” (409)</button></p>`, "Accept");
        if (e.target.closest("[data-dec]")) { dialog(`<h2>Decline ${fn}'s request?</h2><p class="small muted mt-1">${fn} is told the request was declined. A reason is optional.</p>
          <div class="chips mt-6" data-chips style="flex-wrap:wrap">${["Not free then", "Needs repair", "Lending only to people I know"].map(t => `<button class="chip" type="button" aria-pressed="false" data-r="${t}">${t}</button>`).join("")}</div>
          <div class="field mt-4"><label class="label" for="dm">Reason (optional)</label><textarea class="textarea" id="dm" maxlength="200" style="min-height:80px" placeholder="Sorry, we're using it that weekend."></textarea><div class="xs faint mt-1" style="text-align:right">${counter("dmc", 200)}</div></div>
          <div class="btns mt-4"><button class="btn btn-danger" type="button" id="decl">Decline</button><button class="btn btn-ghost" data-close type="button">Keep it open</button></div>`, "Decline"); bindCount("#dm", "#dmc"); }
        if (e.target.dataset?.r) { $("#dm").value = e.target.dataset.r; $("#dmc").textContent = $("#dm").value.length; }
        if (e.target.closest("[data-ctr]")) { dialog(`<h2>Suggest other dates</h2><p class="small muted mt-1">${fn} can take your dates, keep their own, or cancel. Your suggestion expires ${T.responseWindowH} hours from now.</p><div class="mt-4">${calendar({ id: "cc", sel: [17, 19], blocked: it.booked })}</div>
          <div class="field mt-4"><label class="label" for="cm">Message (optional)</label><input class="input" id="cm" maxlength="500" value="We're using it on the 14th. Does the 17th work?"></div><button class="btn btn-primary btn-block mt-4" type="button" id="ctr">Suggest 17–19 Oct</button>`, "Suggest dates"); bindCal("cc", s => ($("#ctr").textContent = s.length > 1 ? `Suggest ${s[0]}–${s[1]} Oct` : "Pick the last day"), [17, 19]); }
        if (e.target.id === "decl") { closeDialog(); swap(resultPage("Request declined", `${fn} has been told. The dates stay free for others.`, "#/activity", "Back to activity")); }
        if (e.target.id === "ctr") { closeDialog(); swap(resultPage(`New dates sent to ${fn}`, `${fn} has ${T.responseWindowH} hours to answer. If they keep their own dates, you can still accept or decline those.`, "#/activity", "Back to activity")); }
        if (e.target.id === "ok") { closeDialog(); swap(`<div class="wrap wrap-sm">${done(`You're lending to ${fn}`, `${span(r.dates)} are booked.${r.overlap ? ` ${r.overlap.who} has been told the dates are taken.` : ""}`)}<div class="card mt-6">${timeline([evRow("done", "Accepted", "Just now", "request_accepted"), evRow("now", "Handover", `Record the checklist and deposit when you meet. ${fn} has until ${T.handoverGraceH} hours after the start date to confirm.`), evRow("todo", `Borrowed, back by ${r.dates[1]} Oct`, ""), evRow("todo", "Return and close", "")])}</div><div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="#/handover/b6/lender">Start handover checklist</a><a class="btn btn-outline" href="#/inbox">${icon("message-circle")}Message ${fn}</a></div></div>`); }
        if (e.target.id === "race") dialog(`${empty("calendar-x", "coral", "These dates are already booked", `Another request for overlapping dates was accepted a moment before, so this one couldn't go through (409). Nothing was double-booked: the database refuses overlapping bookings. ${fn}'s request is declined with “dates taken”.`)}<div class="btns" style="justify-content:center"><button class="btn btn-primary" data-ctr type="button">${icon("calendar-range")}Suggest other dates</button><button class="btn btn-ghost" data-close type="button">Close</button></div>`, "Dates taken");
      };
      document.addEventListener("click", h); cleanup = () => document.removeEventListener("click", h);
    }
  };
});

/* ---------------- W14: borrower answers a counter-offer ----------------
   accept -> the new dates are checked and assessed again; decline -> the original dates stand and the
   lender can still accept or decline them; cancel -> the request ends (POST /requests/{id}/cancel). */
route("/counter/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other), c = l.counter || { start: 21, end: 23, message: "" };
  return { title: "New dates suggested", nav: "activity",
    html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: `${u.short} suggested new dates`, actions: cd(l.mins) })}${itemHead(it, `From ${u.name} · ${it.deposit ? rs(it.deposit) + " deposit" : "no deposit"}`)}
      <div class="card card-pad-lg mt-4 rv">${c.message ? `<div class="row">${av(l.other, "lg")}<p style="font-size:17px">“${c.message}”</p></div>` : ""}
        <div class="grid-2 mt-6"><div class="card card-2" style="opacity:.75"><div class="xs faint">You asked</div><div class="kpi" style="font-size:1.5rem">${l.dates}</div></div><div class="card" style="border:2px solid var(--primary)"><div class="xs" style="color:var(--primary-ink);font-weight:650">${u.short} suggests</div><div class="kpi" style="font-size:1.5rem">${c.start}–${c.end - 1} Oct</div></div></div>
        <p class="small muted mt-4">${icon("clock", "i-sm")} With no answer in ${T.responseWindowH} hours, the request expires and nothing is booked.</p></div>
      <div class="dock"><div class="card"><div class="btns"><button class="btn btn-primary grow" type="button" id="yes">${icon("check")}Take ${c.start}–${c.end - 1} Oct</button><button class="btn btn-outline grow" type="button" id="no">Keep my dates</button></div><button class="btn btn-ghost btn-block mt-2" type="button" id="cx" style="color:var(--coral-ink)">Cancel the request</button></div></div></div>`,
    after() {
      $("#yes").onclick = () => swap(`<div class="wrap wrap-sm">${done("New dates taken", `${c.start}–${c.end - 1} Oct goes back to ${u.short} with a fresh evidence report for those dates.`)}<div class="card mt-6">${timeline([evRow("done", "Counter-offer accepted", "Just now", "counter_accepted"), evRow("done", "Membership confirmed again", "From your saved result", "locality_checked"), evRow("now", "Evidence report for the new dates", `Then ${u.short} decides`, "assessment_generated")])}</div><div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="#/activity">Back to activity</a></div></div>`);
      $("#no").onclick = () => swap(resultPage("You kept your dates", `${u.short} can still accept or decline ${l.dates}. Nothing else changes.`, "#/activity", "Back to activity"));
      $("#cx").onclick = () => dialog(`<h2>Cancel your request?</h2><p class="muted mt-2">${u.short} is told you no longer need it. You can always ask again.</p><div class="btns mt-6"><button class="btn btn-danger" data-close type="button" onclick="location.hash='#/activity';toast('Request cancelled')">Cancel request</button><button class="btn btn-ghost" data-close type="button">Keep it</button></div>`, "Cancel");
    } };
});

/* ---------------- Loan journey (ACTIVE, overdue, NO_SHOW, HELD_FOR_REVIEW) ---------------- */
route("/loan/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  if (l.state === "NO_SHOW") return { title: "No-show", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: it.title })}${empty("user-x", "neutral", "The handover didn't happen", `The handover wasn't confirmed within ${T.handoverGraceH} hours of the start date, so the booking closed as a no-show and the dates were released.`)}<div class="card">${timeline([evRow("done", "Accepted", "30 Sep", "request_accepted"), evRow("done", "Handover reminder", "1 Oct", ""), evRow("alert", "Closed as no-show", `3 Oct · ${T.handoverGraceH} h after the start · dates released`, "no_show")])}</div><p class="small muted mt-4">A no-show is recorded on the loan, not as a judgement of either person. Think it's wrong? Report it within ${T.disputeWindowD} days.</p><div class="btns mt-4"><a class="btn btn-primary" href="#/item/makita">Ask again</a><a class="btn btn-outline" href="#/report/b12">Report a problem</a></div></div>` };
  if (l.state === "HELD_FOR_REVIEW") return { title: "With a moderator", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: it.title, sub: `Your request to ${u.name} · ${l.dates}`, actions: stateChip("held") })}
    ${empty("gem", "violet", "A Block C moderator checks this first", `${HOLD[l.hold_reason]}. This is routine for high-value items when there isn't much similar history yet. It isn't a rejection, and ${u.short} hasn't seen the request yet.`)}
    <div class="card">${timeline([evRow("done", "Request sent", "Today, 10:02 am", "request_created"), evRow("done", "Membership confirmed", "From your saved result", "locality_checked"), evRow("now", "With a moderator", "They can clear it, add safeguards, or restrict it, always with a written reason", `held_for_review · ${l.hold_reason}`), evRow("todo", `${u.short} decides`, `Within ${T.responseWindowH} hours of reaching them`)])}</div>
    <div class="btns mt-4"><button class="btn btn-outline" type="button" onclick="location.hash='#/activity';toast('Request cancelled')">Cancel the request</button></div></div>` };
  const od = !!l.overdue, lend = l.your_role === "LENDER";
  return { title: it.title, nav: "activity",
    html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: it.title, sub: `${lend ? "Lent to" : "Borrowing from"} ${u.name} · ${l.dates}`, actions: `<a class="btn btn-outline" href="#/inbox">${icon("message-circle")}Message ${u.short}</a>` })}
      <div class="two-col"><div class="stack-lg">
        <div class="card card-pad-lg rv" style="${od ? "background:var(--coral-soft);border-color:transparent" : ""}"><div class="between" style="flex-wrap:wrap"><div><div class="small ${od ? "" : "muted"}" style="font-weight:600">${od ? "Overdue since" : "Due back"}</div><div class="stat-big mt-1">${l.due}</div></div>${cd(l.mins)}</div>
          <p class="small mt-4" style="max-width:56ch">${od ? `Please return the books today. ${T.overdueLimitH} hours after the due date, and after at least ${T.minReminders} reminders, a dispute opens automatically and a moderator gets involved. Asking for more days still works.` : `You get a reminder ${T.returnReminderH} hours before. Extensions need ${u.short}'s OK.`}</p><div class="mt-6">${stepsH(3, od)}</div></div>
        <div class="card rv"><div class="between" style="margin-bottom:16px"><h3>Timeline</h3><span class="xs faint">From the loan's event log</span></div>${timeline([evRow("done", "Requested", "10 Oct", "request_created"), evRow("done", "Evidence report prepared", "10 Oct", "assessment_generated"), evRow("done", `Accepted by ${u.short}`, "11 Oct", "request_accepted"), evRow("done", "Handover checklist and deposit recorded", "13 Oct, 6:04 pm · 2 photos", "condition report · HANDOVER"), evRow("done", "You confirmed the handover", "13 Oct, 6:10 pm", "handover_confirmed"),
          od ? evRow("alert", "Overdue since " + l.due, `${T.minReminders} reminders sent`, "reminder_sent") : evRow("now", "Borrowed · due " + l.due, `Reminder ${T.returnReminderH} hours before`), od ? evRow("todo", "Automatic dispute in 22 h", "Only if it's still not returned", "dispute_opened · job overdue_escalation") : evRow("todo", "Return: you start it, the lender checks it", ""), evRow("todo", "Completed, reviews open", `For ${T.reviewWindowD} days`)])}</div></div>
      <aside class="aside stack"><a class="btn btn-primary btn-lg btn-block" href="#/return/${id}">${icon("undo-2")}I'm returning it</a><a class="btn btn-outline btn-block" href="#/extend/${id}">${icon("calendar-plus")}Ask for more days</a>
        <div class="card"><b class="small">Recorded at handover</b><div class="photos mt-3">${[0, 1].map(() => `<div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Handover photo"></div>`).join("")}</div><p class="xs faint mt-3">${it.deposit ? rs(it.deposit) + " deposit recorded" : "No deposit"} · checklist 4 of 4</p></div>
        <a class="btn btn-ghost btn-block" href="#/report/${id}" style="color:var(--coral-ink)">${icon("flag")}Report a problem</a></aside></div></div>` };
});

/* ---------------- W3a, W3b, W17: handover ----------------
   Lender: POST handover/checklist { checklist, deposit_received, notes }, then photos are linked
   (POST /transactions/{id}/photos, JPEG/PNG up to 5 MB). Borrower: POST handover/confirm
   { condition_agreed, notes }. Disagreeing records it and the loan stays ACCEPTED (UC-B7 3a). */
const CHECKS = { drill: ["Powers on and runs smoothly", "Casing has no cracks", "Chuck tightens and holds a bit", "All 13 bits in the case"], deg: ["Base has no dents or holes", "Lid fits", "Handles firm", "Kafgeer included"] };
route("/handover/:id/:side", ({ id, side }) => {
  const l = L(id), it = I(l.item), u = U(l.other), checks = CHECKS[it.noun] || CHECKS.drill;
  if (side === "lender") return { title: "Handover checklist", nav: "activity",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/activity", "Activity"], eyebrow: `${icon("calendar-check", "i-sm")}Tue 14 Oct · ${it.handover_method}`, title: `Check the ${it.noun} with ${u.short}`, sub: `${u.short} sees exactly what you record, and you both compare against it at return.` })}
      <div class="two-col"><div class="stack-lg" id="hl">
        <div class="card rv"><div class="between"><h3>1. Condition checklist</h3><span class="xs faint" id="cc">0 of ${checks.length}</span></div><div class="mt-2" id="hc">${checks.map(c => `<label class="check"><input type="checkbox"><span><strong>${c}</strong></span></label>`).join("")}</div></div>
        ${it.deposit ? `<div class="card rv"><label class="check" style="padding:0"><input type="checkbox" id="dep"><span><strong>I received the ${rs(it.deposit)} deposit in person</strong><span>Recorded only. No money moves through the app.</span></span></label></div>` : ""}
        <div class="card rv"><label class="label" for="hn">Notes (optional)</label><textarea class="textarea" id="hn" maxlength="500" style="min-height:80px" placeholder="e.g. small scratch on the side, already there"></textarea><div class="xs faint mt-1" style="text-align:right">${counter("hnc", 500)}</div></div>
        <div class="card rv" id="phc" style="opacity:.55"><div class="between"><h3>2. Photos</h3><span class="badge green">Suggested safeguard</span></div><p class="small muted mt-1">Added after the checklist is saved. JPEG or PNG, up to ${T.photoMaxMB} MB each.</p><div class="photos mt-4" id="hp">${["Whole item", "Close-up", "Accessories"].map(x => `<button class="photo-add" type="button" data-l="${x}" disabled>${icon("camera")}${x}</button>`).join("")}</div>
          <p class="xs faint mt-3">Camera not working? <button class="link" type="button" id="np" disabled>Continue without photos</button> (marked “reduced evidence”)</p></div></div>
      <aside class="aside"><div class="card" style="box-shadow:var(--shadow)"><h3>Ready?</h3><div class="stack mt-4" id="req">${[["Every check ticked", "ck"], ...(it.deposit ? [["Deposit recorded", "dp"]] : [])].map(([t, k]) => `<div class="row small" data-k="${k}">${tone("circle", "neutral", 26)}${t}</div>`).join("")}</div><button class="btn btn-primary btn-block mt-6" id="hs" type="button" aria-disabled="true">Save checklist</button><p class="xs faint mt-2" id="hsn">${u.short} can confirm once it's saved.</p></div></aside></div></div>`,
    after() {
      let saved = false;
      const s = () => ({ ck: $$("#hc input").every(c => c.checked), dp: !$("#dep") || $("#dep").checked });
      const upd = () => { const v = s(); $("#cc").textContent = `${$$("#hc input:checked").length} of ${checks.length}`;
        $$("#req [data-k]").forEach(r => { r.firstElementChild.outerHTML = tone(v[r.dataset.k] ? "check" : "circle", v[r.dataset.k] ? "green" : "neutral", 26); });
        if (!saved) $("#hs").setAttribute("aria-disabled", !(v.ck && v.dp)); refreshIcons(); };
      $$("#hc input").forEach(c => c.onchange = upd); $("#dep")?.addEventListener("change", upd); bindCount("#hn", "#hnc");
      const waiting = reduced => swap(`<div class="wrap wrap-sm">${empty("smartphone", "sky", `Waiting for ${u.short} to confirm`, `They see your checklist${reduced ? " (reduced evidence: no photos)" : " and photos"}. The loan starts when they confirm.`)}<div class="card">${timeline([evRow("done", "Checklist and deposit recorded", "Just now", "condition report · HANDOVER"), evRow("now", `${u.short} confirms`, `A reminder goes out if they haven't within ${T.confirmationReminderH} hours`), evRow("todo", "Borrowed until 16 Oct", "", "handover_confirmed")])}</div></div>`);
      $("#hs").onclick = () => {
        if (saved) return waiting($$("#hp .done").length === 0);
        if ($("#hs").getAttribute("aria-disabled") === "true") return toast("Tick every check and record the deposit first.", { ic: "info" });
        saved = true; $$("#hc input, #dep").forEach(c => (c.disabled = true)); $("#phc").style.opacity = 1; $$("#hp .photo-add, #np").forEach(b => (b.disabled = false));
        $("#hs").textContent = "Send to " + u.short; $("#hsn").textContent = "Checklist saved. Add photos, or send without them."; toast("Checklist saved");
      };
      $$("#hp .photo-add").forEach(p => p.onclick = () => { p.classList.add("done"); p.innerHTML = `<img src="${img(it.photo, 240, 240)}" alt="${p.dataset.l}"><span class="ok">${icon("check")}</span><span class="cap">${p.dataset.l}</span>`; refreshIcons(); });
      $("#np").onclick = () => waiting(true);
    } };
  return { title: "Confirm handover", nav: "activity",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/activity", "Activity"], eyebrow: `${icon("map-pin", "i-sm")}Today · ${it.handover_method}`, title: `Confirm the ${it.noun} from ${u.short}`, sub: `${u.short} recorded the condition at 5:04 pm. Check it matches what's in front of you.`, actions: cd(l.mins) })}
      <div class="two-col"><div class="stack-lg">${photo(it.photo, { w: 1200, ratio: "16/8", alt: it.title, cls: "rv" })}
        <div class="card rv"><h3>${u.short}'s checklist</h3><div class="mt-3">${checks.map(c => `<div class="row small" style="padding:7px 0">${tone("check", "green", 24)}${c}</div>`).join("")}</div></div>
        <div class="card rv"><h3>Photos</h3><div class="photos mt-3">${["Whole item", "Base", "Lid"].map(x => `<div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="${x}"><span class="cap">${x}</span></div>`).join("")}</div><p class="small mt-4"><b>${u.short}'s note:</b> “Small dent on one handle, already there.”</p></div>
        <div class="card rv"><label class="label" for="bn">Your notes (optional)</label><textarea class="textarea" id="bn" maxlength="500" style="min-height:70px"></textarea></div></div>
      <aside class="aside"><div class="card" style="box-shadow:var(--shadow)"><div class="between"><span class="muted small">Deposit recorded</span><b>${it.deposit ? rs(it.deposit) : "None"}</b></div><div class="between mt-2"><span class="muted small">Back by</span><b>${l.due}</b></div>
        <button class="btn btn-primary btn-block mt-6" type="button" id="ok">${icon("check")}It matches. Start the loan</button><button class="btn btn-ghost btn-block mt-2" type="button" id="no">Something doesn't match</button></div></aside></div></div>`,
    after() {
      $("#ok").onclick = () => swap(resultPage(`Enjoy the ${it.noun}`, `Return it to ${u.short} by ${l.due}. You get a reminder ${T.returnReminderH} hours before.`, "#/loan/b2", "See the loan"));
      $("#no").onclick = () => dialog(`<h2>What doesn't match?</h2><p class="small muted mt-1">Your disagreement is recorded and the loan doesn't start. Sort it out with ${u.short}, or report it.</p>
        <div class="field mt-4"><label class="label" for="nm">What's different?</label><textarea class="textarea" id="nm" maxlength="500" style="min-height:80px">The lid has a crack that isn't in the checklist.</textarea></div>
        <div class="btns mt-6"><button class="btn btn-primary" data-close type="button" onclick="toast('Disagreement recorded. The loan hasn\\'t started.')">Record disagreement</button><a class="btn btn-outline" href="#/report/${id}">${icon("flag")}Report it</a></div>`, "Mismatch");
    } };
});

/* ---------------- W13: extension (POST /transactions/{id}/extension { new_due_date, reason }) ---------------- */
route("/extend/:id", ({ id }) => {
  const l = L(id), u = U(l.other);
  return { title: "Ask for more days", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/loan/" + id, "Loan"], title: "Ask for more days", sub: `Due ${l.due}. ${u.short} decides, and the due date stays the same until then. One request at a time.` })}
    <div class="card rv"><p class="small muted" style="margin-bottom:12px">Tap the new day it comes back.</p>${calendar({ id: "ec", sel: [15, 17], blocked: [19, 20] })}</div>
    <div class="card card-2 mt-4 between rv"><span class="small muted">New return day</span><b id="es">Fri 17 Oct (+2 days)</b></div>
    <div class="card mt-4 rv"><label class="label" for="er">Reason (optional)</label><textarea class="textarea" id="er" maxlength="500" style="min-height:80px">The painter is coming a day late.</textarea></div>
    <div class="dock"><div class="card"><button class="btn btn-primary btn-block" type="button" id="ask">Ask ${u.short}</button></div></div></div>`,
    after() { bindCal("ec", s => { const e = s[1] ?? s[0]; $("#es").textContent = e > 15 ? `${dow(e)} ${e} Oct (+${e - 15} day${e - 15 > 1 ? "s" : ""})` : "Pick a later day"; }, [15, 17]); $("#ask").onclick = () => swap(resultPage(`Asked ${u.short} for more days`, `Keep it past ${l.due} only if ${u.short} approves. You're told either way.`, "#/loan/" + id, "Back to the loan")); } };
});
route("/extend-respond/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other), x = l.extension || { new_due: "Thu 30 Oct", reason: "" };
  return { title: "Extension request", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: `${u.short} asks to keep the ${it.noun} longer`, sub: `Back by ${x.new_due} instead of Tue 28 Oct` })}
    ${x.reason ? `<div class="card card-pad-lg rv"><div class="row">${av(l.other, "lg")}<p style="font-size:17px">“${x.reason}”</p></div></div>` : ""}
    <div class="card mt-4 rv"><div class="between"><h3>Your ${it.noun}'s bookings</h3><span class="badge green">${icon("check")}No conflicts</span></div><div class="mt-4">${calendar({ sel: [24, 29] })}</div><p class="xs faint mt-2">An extension can't run into another accepted booking.</p></div>
    <div class="dock"><div class="card btns"><button class="btn btn-primary grow" type="button" id="y">${icon("check")}Approve</button><button class="btn btn-outline grow" type="button" id="n">Decline</button></div></div></div>`,
    after() { $("#y").onclick = () => swap(resultPage("Extension approved", `${u.short}'s new return day is ${x.new_due}. Reminders move with it.`, "#/activity", "Back to activity")); $("#n").onclick = () => { toast(`${u.short} has been told the due date stays the same`); location.hash = "#/activity"; }; } };
});

/* ---------------- B8: return. Borrower starts it, lender records the return checklist,
   borrower confirms the lender's report (POST /return/confirm { condition_agreed }) -> COMPLETED ---------------- */
route("/return/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Return", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/loan/" + id, "Loan"], title: `Return the ${it.noun}`, sub: l.overdue ? "Late. Starting the return now stops the automatic dispute." : `On time. Due ${l.due}.` })}
    <div class="card rv">${timeline([{ s: "now", t: "You hand it back", d: `Tell ${u.short} it's on its way` }, { s: "todo", t: `${u.short} checks it`, d: "Against the handover checklist and photos" }, { s: "todo", t: `You confirm ${u.short}'s report`, d: "Then the loan completes and reviews open" }])}</div>
    <div class="card mt-4 rv"><h3>Photos of how you're returning it <span class="faint small" style="font-weight:400">(optional)</span></h3><p class="small muted mt-1">They're added to the loan record and protect you too.</p><div class="photos mt-4"><div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Return photo"><span class="ok">${icon("check")}</span></div><button class="photo-add" type="button">${icon("camera")}Close-up</button><button class="photo-add" type="button">${icon("camera")}Extra</button></div></div>
    <div class="dock"><div class="card"><button class="btn btn-primary btn-block" id="b" type="button">Tell ${u.short} it's coming back</button></div></div></div>`,
    after() { $("#b").onclick = () => swap(resultPage(`${u.short} has been told`, `Once ${u.short} records the return checklist, you'll be asked to confirm it.`, "#/activity", "Back to activity")); } };
});
route("/inspect/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  const rows = [["Powers on and runs smoothly", 1], ["Casing has no cracks", 0], ["Chuck tightens and holds a bit", 1], ["All 13 bits in the case", 1]];
  return { title: "Return checklist", nav: "activity", html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: `Check the ${it.noun} from ${u.short}`, sub: "Return started 11 Oct, 7:40 pm · on time" })}
    <div class="two-col"><div class="stack-lg"><div class="card rv"><div class="between"><h3>Then and now</h3><span class="badge green">${icon("clock")}On time</span></div>
      <div class="cmp mt-4"><div><div class="lab">${icon("package-check")}Handover · 9 Oct</div>${photo(it.photo, { w: 600, ratio: "1", alt: "Handover" })}</div><div><div class="lab">${icon("undo-2")}Return · 11 Oct</div>${photo(it.photo, { w: 600, ratio: "1", alt: "Return", cls: "flag", inner: '<span class="pin" style="left:55%;top:42%">1</span>' })}</div></div>
      <p class="small mt-3" style="color:var(--coral-ink)"><b>1</b> Possible crack near the chuck.</p></div>
      <div class="card rv"><h3>Return checklist</h3><p class="small muted mt-1">Tap “Changed” for anything that isn't as it was at handover.</p><div class="mt-2" id="rows">${rows.map(([t, s], i) => `<div class="check-row"><div><b class="small">${t}</b><div class="xs" style="color:var(--primary-ink)">${icon("check", "i-sm")} OK at handover</div></div>${seg([["same", "Same"], ["changed", "Changed"]], s ? 0 : 1, "danger").replace('class="seg', `data-r="${i}" class="seg`)}</div>`).join("")}</div>
        <div class="field mt-4"><label class="label" for="rn">Notes (optional)</label><textarea class="textarea" id="rn" maxlength="500" style="min-height:70px"></textarea></div></div></div>
    <aside class="aside"><div class="card" id="ra" style="box-shadow:var(--shadow)"></div></aside></div></div>`,
    after() {
      const paint = () => { const n = $$('#rows [data-v="changed"][aria-selected="true"]').length;
        $("#ra").innerHTML = n ? `${tone("triangle-alert", "coral")}<h3 class="mt-4">${n} thing${n > 1 ? "s" : ""} changed</h3><p class="small muted mt-2">Recording a difference means the loan can't complete normally. Talk to ${u.short} first, or report it so a moderator decides. Reporting pauses the loan.</p><a class="btn btn-danger btn-block mt-6" href="#/report/b3">${icon("flag")}Report damage</a><a class="btn btn-outline btn-block mt-2" href="#/inbox">${icon("message-circle")}Message ${u.short}</a>`
          : `${tone("circle-check", "green")}<h3 class="mt-4">Everything matches</h3><p class="small muted mt-2">${u.short} is asked to confirm your report. Then the loan completes, the ${rs(it.deposit)} deposit is marked returned and reviews open.</p><button class="btn btn-primary btn-block mt-6" id="cl" type="button">Save return checklist</button>`;
        refreshIcons(); $("#cl")?.addEventListener("click", () => swap(`<div class="wrap wrap-sm">${empty("smartphone", "sky", `Waiting for ${u.short} to confirm`, "Your return report is saved. The loan completes when they confirm it.")}<div class="card">${timeline([evRow("done", "Return started", "11 Oct, 7:40 pm", "return_initiated"), evRow("done", "Your return checklist", "Just now · everything matches", "condition report · RETURN"), evRow("now", `${u.short} confirms`, ""), evRow("todo", "Completed", "", "transaction_closed")])}</div></div>`)); };
      $("#rows").addEventListener("click", e => { if (e.target.closest("[role=tab]")) setTimeout(paint, 0); }); paint();
    } };
});
route("/return-confirm/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Confirm the return", nav: "activity", html: `<div class="wrap wrap-md">${pageHead({ back: ["#/activity", "Activity"], title: `${u.short} checked the ${it.noun}`, sub: "Confirm their report to complete the loan.", actions: cd(l.mins) })}
    <div class="two-col"><div class="stack-lg">
      <div class="card rv"><div class="between"><h3>${u.short}'s return checklist</h3><span class="badge green">${icon("check")}Matches handover</span></div><div class="mt-3">${["Opens and locks fully", "Rungs and feet firm", "No new dents", "Safety catch works"].map(c => `<div class="row small" style="padding:7px 0">${tone("check", "green", 24)}${c}</div>`).join("")}</div><p class="small mt-3"><b>${u.short}'s note:</b> “All good, thanks for wiping it down.”</p></div>
      <div class="card rv">${timeline([evRow("done", "You started the return", "8 Oct, 6:15 pm", "return_initiated"), evRow("done", `${u.short} recorded the return checklist`, "8 Oct, 7:02 pm", "condition report · RETURN"), evRow("now", "You confirm", "Returned on time, so it counts as an on-time return"), evRow("todo", "Completed, reviews open", `For ${T.reviewWindowD} days`, "transaction_closed")])}</div></div>
    <aside class="aside"><div class="card" style="box-shadow:var(--shadow)"><div class="between"><span class="muted small">Deposit</span><b>${it.deposit ? rs(it.deposit) + " returned" : "None"}</b></div>
      <button class="btn btn-primary btn-block mt-6" type="button" id="ok">${icon("check")}Confirm and complete</button><button class="btn btn-ghost btn-block mt-2" type="button" id="no">I don't agree</button></div></aside></div></div>`,
    after() {
      $("#ok").onclick = () => swap(resultPage("Loan complete", `Thanks for returning it on time. It's now part of your verified history. You can review ${u.short} for ${T.reviewWindowD} days.`, "#/review/b4", "Leave a review"));
      $("#no").onclick = () => dialog(`<h2>Don't agree with the report?</h2><p class="small muted mt-1">Your disagreement is recorded, and the loan can't complete until a moderator decides. Say what's different in a report.</p><div class="btns mt-6"><a class="btn btn-danger" href="#/report/${id}">${icon("flag")}Report it</a><button class="btn btn-ghost" data-close type="button">Go back</button></div>`, "Disagree");
    } };
});

/* ---------------- W5: report a problem (POST /transactions/{id}/dispute { reason, description }) ---------------- */
route("/report/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Report a problem", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: "Report a problem", sub: `Problems can be reported up to ${T.disputeWindowD} days after the loan ends.` })}${itemHead(it, `${l.your_role === "LENDER" ? "Lent to" : "Borrowed from"} ${u.short} · ${l.dates}`)}
    <div class="field mt-6 rv"><span class="label">What happened?</span><div class="opts cols-2">${Object.entries(DISPUTE_R).map(([k, [ic, t]], i) => `<label class="opt"><input type="radio" name="t" value="${k}" ${i === 0 ? "checked" : ""}>${tone(ic, "coral", 32)}<span><strong>${t}</strong></span></label>`).join("")}</div></div>
    <div class="field rv"><label class="label" for="dd">Describe it</label><textarea class="textarea" id="dd" maxlength="1000">Hairline crack on the casing next to the chuck. It wasn't there at handover (photo 1).</textarea><div class="between xs faint mt-1"><span>Say what you saw. The moderator sees both checklists and every photo.</span>${counter("ddc", 1000)}</div></div>
    <div class="field rv"><span class="label">Photos (optional)</span><div class="photos"><div class="photo-add done flag"><img src="${img(it.photo, 240, 240)}" alt="Crack"><span class="cap">Crack</span></div><button class="photo-add" type="button">${icon("image-plus")}Photo</button></div><span class="help">JPEG or PNG, up to ${T.photoMaxMB} MB each.</span></div>
    <div class="card card-2 mt-6 row rv" style="align-items:flex-start">${tone("lock", "saffron", 36)}<div><b class="small">The loan pauses while it's reviewed</b><p class="small muted">Nobody can move it forward until a moderator decides. ${u.short} is asked for their side and has ${T.partyResponseH} hours to reply. You can withdraw any time before a decision.</p></div></div>
    <div class="dock"><div class="card"><a class="btn btn-danger btn-block" href="#/case/b3">Send to moderators</a></div></div></div>`,
    after() { bindCount("#dd", "#ddc"); } };
});

/* ---------------- Case progress (b3 raiser) and W18 statement (b5, case D-014) ----------------
   GET /transactions/{id}/dispute -> DisputeTrailOut; POST /cases/{id}/statements { statement <= 2000 } */
route("/case/:id", ({ id }) => {
  const raiser = id === "b3", l = L(id), it = I(l.item), u = U(l.other), c = DB.cases.find(x => x.id === "D-014"), q = c.information_request;
  const stmts = raiser ? [] : c.statements;
  return { title: "Dispute", nav: "activity", html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], eyebrow: raiser ? "Case D-015 · damage" : `Case ${c.id} · ${DISPUTE_R[c.dispute_reason][1].toLowerCase()}`, title: raiser ? "You reported damage" : "Dispute about the chairs", sub: raiser ? `${u.short} has been asked for their side and has ${T.partyResponseH} hours.` : `${U(c.lender).short} raised it at return. A moderator has asked you a question.`, actions: `<span class="status ${CASE_ST[raiser ? "OPEN" : c.status][1]}">${CASE_ST[raiser ? "OPEN" : c.status][0]}</span>` })}
    <div class="two-col"><div class="stack-lg">
      ${!raiser ? `<div class="card card-pad-lg rv" style="border:1.5px solid var(--saffron)" id="qa"><div class="between"><span class="row">${av("mod", "sm")}<b>A Block C moderator asked you</b></span>${cd(q.mins)}</div>
        <p class="mt-4" style="font-size:17px">“${q.question}”</p>
        <p class="xs mt-3" style="color:var(--saffron-ink)">Reply by ${q.deadline}. With no reply in ${T.partyResponseH} hours, the case goes ahead with what's there.</p>
        <div class="field mt-6"><label class="label" for="mr">Your statement</label><textarea class="textarea" id="mr" maxlength="2000">They stayed stacked in our garage. Two already had scratches when we collected them; it's in my pickup photo.</textarea><div class="xs faint mt-1" style="text-align:right">${counter("mrc", 2000)}</div></div>
        <div class="photos mt-2"><div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Pickup"><span class="cap">Pickup</span></div><button class="photo-add" type="button">${icon("image-plus")}Add</button></div>
        <button class="btn btn-primary mt-6" type="button" id="sr">Send statement</button></div>` : ""}
      ${stmts.length ? `<div class="card rv"><h3>Statements so far</h3>${stmts.map(s => `<div style="padding:14px 0;border-top:1px solid var(--border);margin-top:12px"><div class="between"><b class="small">${s.author_name} <span class="faint" style="font-weight:400">· ${cap(s.author_role.toLowerCase())}</span></b><span class="xs faint">${s.at}</span></div><p class="small mt-2">${s.statement}</p></div>`).join("")}</div>` : ""}
      <div class="card rv"><h3 style="margin-bottom:16px">Progress</h3>${timeline(raiser ? [evRow("done", "Report sent", "Just now", "dispute_opened"), evRow("now", `${u.short} gives their side`, `Up to ${T.partyResponseH} h`), evRow("todo", "A moderator reviews both sides", "They may ask either of you a question"), evRow("todo", "Decision with a written reason", `Either side can appeal within ${T.appealWindowD} days`)]
        : [evRow("done", "Dispute raised by the lender", "15 Oct, 6:27 pm", "dispute_opened"), evRow("done", "Hira's statement", c.statements[0].at), evRow("now", "Moderator asked you a question", "Waiting for your statement"), evRow("todo", "Decision with a written reason", `Either side can appeal within ${T.appealWindowD} days`)])}</div></div>
    <aside class="aside stack"><div class="card card-2 row" style="align-items:flex-start">${tone("lock", "saffron", 34)}<div><b class="small">Loan paused</b><p class="xs muted">Nothing moves forward until a decision.</p></div></div><div class="card"><b class="small">Who can see this</b><p class="xs muted mt-1">Both of you and Block C moderators. A moderator who is part of the loan can't decide it.</p></div>
      ${raiser ? `<button class="btn btn-outline btn-block" type="button" id="wd">${icon("rotate-ccw")}Withdraw report</button>` : `<p class="xs faint">Only the person who raised a dispute can withdraw it.</p>`}</aside></div></div>`,
    after() {
      bindCount("#mr", "#mrc");
      $("#sr")?.addEventListener("click", () => { if (!$("#mr").value.trim()) return toast("Write your statement first.", { ic: "info" }); swap(resultPage("Statement sent", "It's part of the case now. The moderator decides with both sides in front of them.", "#/activity", "Back to activity")); });
      $("#wd")?.addEventListener("click", () => dialog(`<h2>Withdraw your report?</h2><p class="muted mt-2">The case closes as withdrawn and the loan goes back to where it was, so the return can finish normally.</p><div class="btns mt-6"><button class="btn btn-primary" data-close type="button" onclick="toast('Report withdrawn. Loan restored.');location.hash='#/inspect/b3'">Withdraw</button><button class="btn btn-ghost" data-close type="button">Keep it open</button></div>`, "Withdraw"));
    } };
});

/* ---------------- W20: decision and appeal (POST /cases/{id}/appeal { reason <= 1000 }) ---------------- */
route("/decision/:id", ({ id }) => {
  const c = DB.cases.find(x => x.id === "A-003"), d = c.decisions[0], it = I(c.item);
  const POSS = { NOT_HANDED_OVER: "Never handed over", WITH_BORROWER: "Still with the borrower", RETURNED: "Back with the lender", LOST: "Lost" };
  return { title: "Decision", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], eyebrow: `Case D-011 · ${it.title}, ${c.period}`, title: "The moderator's decision" })}
    <div class="card card-pad-lg rv"><div class="row">${av("mod2", "sm")}<div><b>${d.decider}</b><div class="xs faint">${d.decided} · recorded in the audit log</div></div></div><p class="mt-4" style="font-size:17px">“${d.reason}”</p>
      <div class="row-wrap mt-4"><span class="badge">${icon("scale")}Responsibility: ${d.at_fault}</span><span class="badge">${icon("package-check")}${POSS[d.possession]}</span></div></div>
    <div class="card card-pad-lg mt-4 rv" id="ab"><div class="between"><h3>Appeal to a second moderator</h3>${cd(5 * 1440)}</div><p class="small muted mt-2">One appeal per case, within ${T.appealWindowD} days. A different moderator, who wasn't part of the first decision, upholds or overturns it. Both decisions stay in the log.</p>
      <div class="field mt-6"><label class="label" for="ap">Why should it be looked at again?</label><textarea class="textarea" id="ap" maxlength="1000">The leg was already split at pickup. It's in my pickup photo, which wasn't attached to the case.</textarea><div class="xs faint mt-1" style="text-align:right">${counter("apc", 1000)}</div></div>
      <button class="btn btn-primary mt-4" type="button" id="send">Send appeal</button></div></div>`,
    after() { bindCount("#ap", "#apc"); $("#send").onclick = () => { if ($("#ap").value.trim().length < 20) { $("#ap").setAttribute("aria-invalid", "true"); return toast("Say why in a sentence or two.", { ic: "info" }); } $("#ab").innerHTML = `<h3>Appeal sent</h3><div class="mt-4">${timeline([evRow("done", "Appeal received", "Case A-003", "APPEALED"), evRow("now", "A second moderator reviews it", "Someone not involved before"), evRow("todo", "Upheld or overturned, with a reason", "If overturned, the loan's outcome is re-evaluated")])}</div>`; refreshIcons(); toast("Appeal sent"); }; } };
});

/* ---------------- W15: review (POST /transactions/{id}/review { ratings: {dim: 1..5}, comment }) ---------------- */
route("/review/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other), dims = DB.reviewDims[l.your_role === "LENDER" ? "BORROWER" : "LENDER"];
  const stars = (k, q) => `<div style="padding:14px 0;border-top:1px solid var(--border)"><div class="between" style="flex-wrap:wrap;gap:8px"><b class="small">${q}</b><span class="row" role="radiogroup" aria-label="${q}" data-dim="${k}" style="gap:2px">${[1, 2, 3, 4, 5].map(n => `<button class="icon-btn" type="button" role="radio" aria-checked="${n === 5}" aria-label="${n} of 5" data-n="${n}" style="width:38px;height:38px;color:${n <= 5 ? "var(--saffron)" : "var(--text-3)"}">${icon("star")}</button>`).join("")}</span></div></div>`;
  return { title: "Review", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: `How was ${l.your_role === "LENDER" ? "lending to" : "borrowing from"} ${u.short}?`, sub: `${it.title} · completed`, actions: cd(12 * 1440 + 200, "calm") })}
    <div class="card card-pad-lg rv"><p class="small muted">Rate each from 1 to 5. Every one is needed.</p>${dims.map(([k, q]) => stars(k, q)).join("")}</div>
    <div class="card mt-4 rv"><label class="label" for="rc">Anything neighbours should know? <span class="faint" style="font-weight:400">(optional)</span></label><textarea class="textarea" id="rc" maxlength="1000">Tent was clean and complete, pegs counted. Bilal showed us how to set up the fly.</textarea><div class="between xs faint mt-1"><span>Describe what happened, not the person.</span>${counter("rcc", 1000)}</div></div>
    <p class="xs faint mt-4">${icon("lock", "i-sm")} One review each, within ${T.reviewWindowD} days of completion. You can edit yours for ${T.reviewEditH} hours. Reviews are checked for patterns like retaliation; they never change the evidence estimate directly.</p>
    <div class="dock"><div class="card"><button class="btn btn-primary btn-block" type="button" id="p">Post review</button></div></div></div>`,
    after() {
      bindCount("#rc", "#rcc");
      $$("[data-dim]").forEach(g => g.addEventListener("click", e => { const b = e.target.closest("[data-n]"); if (!b) return; const n = +b.dataset.n; $$("[data-n]", g).forEach(s => { s.setAttribute("aria-checked", +s.dataset.n === n); s.style.color = +s.dataset.n <= n ? "var(--saffron)" : "var(--text-3)"; }); }));
      $("#p").onclick = () => swap(resultPage("Review saved", `Thanks. You can change it for the next ${T.reviewEditH} hours.`, "#/activity", "Back to activity"));
    } };
});

/* ---------------- W22: listings (POST /items, PATCH /items/{id}, GET /me/items) ----------------
   Fields: title, description, category_id, condition, value_band, deposit, usage_terms, handover_method,
   search_terms, expires (default 60 days). Publishing needs a description and a condition. */
function listingWizard(edit) {
  const steps = [
    ["Photos and title", () => `<div class="photos"><div class="photo-add done"><img src="${img(I("drill").photo, 300, 300)}" alt="Cover"><span class="cap">Cover</span></div><button class="photo-add" type="button">${icon("camera")}Camera</button><button class="photo-add" type="button">${icon("image-plus")}Gallery</button></div><p class="xs faint mt-2">JPEG or PNG, up to ${T.photoMaxMB} MB each.</p>
      <div class="field mt-6"><label class="label" for="lt">Title</label><input class="input" id="lt" value="Bosch impact drill + bits" maxlength="120"><div class="between xs faint mt-1"><span>Say what it is and what comes with it.</span><span><span id="ltc">24</span>/120</span></div></div>
      <div class="field"><label class="label" for="ld">Description</label><textarea class="textarea" id="ld">650W impact drill with a 13-piece bit set and a spare chuck key. Plugs in, no battery needed.</textarea><span class="help">Needed to publish.</span></div>
      <div class="field"><label class="label" for="ls">Other names people search for <span class="faint" style="font-weight:400">(optional)</span></label><input class="input" id="ls" value="barma, drill machine"><span class="help">Roman Urdu or local names, so search finds it.</span></div>`],
    ["Category, condition and value", () => `<div class="label">Category</div><div class="opts cols-2">${DB.categories.slice(1).map(c => `<label class="opt" style="padding:12px"><input type="radio" name="c" ${c.id === 1 ? "checked" : ""}>${tone(c.icon, c.is_restricted ? "violet" : "neutral", 32)}<span><strong class="small">${c.label}</strong>${c.is_restricted ? `<p class="xs">Verified members only</p>` : ""}</span></label>`).join("")}</div>
      <div class="label" style="margin-top:22px">Condition</div><div class="opts cols-2">${Object.entries(CONDITION).map(([k, t], i) => `<label class="opt"><input type="radio" name="cd" value="${k}" ${i === 1 ? "checked" : ""}>${tone(["sparkles", "thumbs-up", "wrench", "history"][i], "green", 32)}<span><strong>${t}</strong></span><span class="tick">${icon("check")}</span></label>`).join("")}</div>
      <div class="label" style="margin-top:22px">Roughly what it's worth</div><div class="opts">${Object.entries(BAND).map(([k, t], i) => `<label class="opt"><input type="radio" name="vb" value="${k}" ${i === 0 ? "checked" : ""}>${tone("gem", ["green", "saffron", "violet"][i], 32)}<span><strong>${BAND_SHORT[k]}</strong><p>${t}</p></span><span class="tick">${icon("check")}</span></label>`).join("")}</div><p class="xs faint mt-2">High-value requests with little similar history are checked by a moderator first.</p>`],
    ["Your terms", () => `<div class="field"><label class="label" for="dp">Deposit</label><div class="input-wrap"><span style="position:absolute;left:14px;color:var(--text-3);font-weight:600">Rs</span><input class="input" id="dp" inputmode="numeric" value="2000" style="padding-left:44px"></div><span class="help">Recorded at handover. Cash changes hands in person; the app never holds money.</span></div>
      <div class="field"><label class="label" for="hm">Handover</label><input class="input" id="hm" value="From my gate, Lane 4"><span class="help">A rough place only. The exact spot is shared in chat after you accept.</span></div>
      <div class="field"><label class="label" for="ru">How to use it</label><textarea class="textarea" id="ru" style="min-height:80px">Masonry bits only for brick and concrete. Return with the bits in the case.</textarea></div>`],
    ["Availability", () => `<div class="card card-2 row" style="align-items:flex-start">${tone("calendar-clock", "sky", 34)}<div><b class="small">Blocking your own dates is coming ${soon("Soon")}</b><p class="xs muted mt-1">For now, dates are blocked only by requests you accept. You can pause the listing any time.</p></div></div>
      <div class="field mt-6"><div class="label">Listing expires</div>${seg([["60", "In 60 days"], ["30", "In 30 days"], ["90", "In 90 days"]])}<span class="help">You're reminded before it expires and can renew it.</span></div>
      <div class="card card-2 mt-6 row">${tone("shield-check", "green", 34)}<div><b class="small">Quick check before it goes live</b><p class="xs muted">Some listings are held as “pending review” for a moderator, for example in restricted categories.</p></div></div>`]
  ];
  return { title: edit ? "Edit listing" : "Lend an item", nav: "activity",
    html: `<div class="wrap wrap-md">${pageHead({ back: [edit ? "#/listings" : "#/home", edit ? "My listings" : "Home"], title: edit ? "Edit listing" : "Lend an item", sub: edit ? "Accepted bookings stay as they are." : "Four short steps. Save a draft at any point.", actions: `<button class="btn btn-ghost" type="button" id="dr">${icon("save")}Save draft</button>` })}
      <div class="two-col"><div><div class="steps-h" id="sh">${steps.map(([t], i) => `<div class="s ${i === 0 ? "cur" : ""}"><i></i><span>${i + 1}. ${t}</span></div>`).join("")}</div><div class="card card-pad-lg mt-6" id="st"></div>
        <div class="btns mt-4" style="justify-content:space-between"><button class="btn btn-outline" id="bk" type="button" hidden>${icon("arrow-left")}Back</button><span></span><button class="btn btn-primary" id="nx" type="button">Continue ${icon("arrow-right")}</button></div></div>
      <aside class="aside desk"><div class="xs faint" style="margin-bottom:10px;font-weight:600">Preview</div>${itemCard(I("drill"))}</aside></div></div>`,
    after() {
      let s = 0;
      const pnt = () => { $("#st").innerHTML = `<h2 style="font-size:1.25rem;margin-bottom:18px">${steps[s][0]}</h2>${steps[s][1]()}`; hydrate($("#st")); $("#bk").hidden = !s; $("#nx").innerHTML = s === 3 ? (edit ? "Save changes" : "Publish listing") : `Continue ${icon("arrow-right")}`; $$("#sh .s").forEach((x, i) => (x.className = "s " + (i < s ? "on" : i === s ? "cur" : ""))); refreshIcons();
        $("#lt")?.addEventListener("input", e => ($("#ltc").textContent = e.target.value.length));
        $$("#st button.photo-add").forEach(p => p.onclick = () => { p.classList.add("done"); p.innerHTML = `<img src="${img(I("drill").photo, 300, 300)}" alt="Photo"><span class="ok">${icon("check")}</span>`; refreshIcons(); }); };
      $("#nx").onclick = () => { if (s === 0 && !$("#lt").value.trim()) { $("#lt").setAttribute("aria-invalid", "true"); return toast("Add a title first.", { ic: "info" }); } if (s === 0 && !$("#ld").value.trim()) { $("#ld").setAttribute("aria-invalid", "true"); return toast("A description is needed to publish. Or save it as a draft.", { ic: "info" }); }
        if (s < 3) { s++; pnt(); window.scrollTo({ top: 0, behavior: "smooth" }); } else swap(resultPage(edit ? "Changes saved" : "Your drill is live in Block C", edit ? "Neighbours see the new details now." : "Requests reach you with an evidence report about the borrower.", "#/item/drill", "View listing")); };
      $("#bk").onclick = () => { s--; pnt(); };
      $("#dr").onclick = () => toast("Saved as a draft. Finish it from My listings.");
      pnt();
    } };
}
route("/lend", () => listingWizard(false));
route("/lend/edit", () => listingWizard(true));
const IST = { PUBLISHED: ["green", "Live"], DRAFT: ["", "Draft"], PENDING_REVIEW: ["violet", "Pending review"], PAUSED: ["", "Paused"], EXPIRED: ["saffron", "Expired"], REMOVED: ["coral", "Removed"] };
route("/listings", () => {
  const card = (id, title, st, sub, btns, ph = true) => `<div class="card" style="padding:0;overflow:hidden">${ph ? photo(I(id).photo, { w: 700, ratio: "16/10", alt: "", tl: `<span class="badge glass">${st === "PUBLISHED" ? '<span class="live"></span>' : ""}${IST[st][1]}</span>` }) : `<div class="ph-img" style="aspect-ratio:16/10;display:grid;place-items:center">${tone("image-plus", "neutral", 52)}</div>`}<div style="padding:16px"><div class="between"><b>${title}</b><span class="status ${IST[st][0]}">${IST[st][1]}</span></div><p class="small muted mt-1">${sub}</p><div class="btns mt-4">${btns}</div></div></div>`;
  return { title: "My listings", nav: "activity", html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: "My listings", sub: "Every listing you own, whatever its status.", actions: `<a class="btn btn-primary" href="#/lend">${icon("plus")}New listing</a>` })}
  <div class="grid-3" data-stagger>
    ${card("drill", "Bosch impact drill + bits", "PUBLISHED", "Expires in 52 days · lent 3 times", `<a class="btn btn-primary btn-sm" href="#/requests/r1">1 request waiting</a><a class="btn btn-outline btn-sm" href="#/lend/edit">Edit</a>`)}
    ${card("drill", "Sewing machine", "DRAFT", "Needs a description and a condition to publish", `<a class="btn btn-outline btn-sm" href="#/lend">Continue</a>`, false)}
    ${card("projector", "Projector + screen", "PENDING_REVIEW", "Restricted category: a moderator checks it first", `<button class="btn btn-ghost btn-sm" type="button" disabled>Waiting</button>`)}
    ${card("books", "Cake tins, set of 3", "PAUSED", "Hidden from search since 2 Oct", `<button class="btn btn-outline btn-sm" type="button" onclick="toast('Listing is live again')">${icon("play")}Resume</button>`)}
    ${card("stroller", "Baby bath tub", "EXPIRED", `Expired after ${T.listingExpiryD} days`, `<button class="btn btn-outline btn-sm" type="button" onclick="toast('Renewed for 60 days')">${icon("rotate-cw")}Renew</button>`)}
    ${card("chairs", "Folding table", "REMOVED", "Removed by a moderator: duplicate listing", `<a class="btn btn-ghost btn-sm" href="#/inbox">Ask why</a>`)}</div></div>` };
});

screens("Resident · lending and loans", [["Activity board", "#/activity", "GET /requests"], ["Request: not enough history (W1)", "#/requests/r1", "R3"], ["Request: community paths", "#/requests/r2", "R9"], ["Request: enough evidence", "#/requests/r3", "R8"], ["Counter-offer: respond (W14)", "#/counter/b9", "ADR-0015"],
  ["Loan journey", "#/loan/b2", "GET /events"], ["Loan overdue → auto-dispute", "#/loan/b7", "overdue_escalation"], ["Loan no-show", "#/loan/b12", "no_show"], ["Request held by a moderator", "#/loan/b14", "HELD_FOR_REVIEW"], ["Handover: lender checklist (W3a, W17)", "#/handover/b6/lender", "handover/checklist"], ["Handover: borrower confirms (W3b)", "#/handover/b1/borrower", "handover/confirm"],
  ["Extension: ask (W13)", "#/extend/b2", "/extension"], ["Extension: respond (W13)", "#/extend-respond/b10", "approve / decline"], ["Return: borrower starts", "#/return/b2", "/return"], ["Return: lender checklist (W4)", "#/inspect/b3", "/return/confirm"], ["Return: borrower confirms", "#/return-confirm/b13", "/return/confirm"], ["Report a problem (W5)", "#/report/b3", "/dispute"],
  ["Your report in progress", "#/case/b3", "dispute/withdraw"], ["Statement to a moderator (W18)", "#/case/b5", "statements"], ["Decision + appeal (W20)", "#/decision/b11", "/appeal"], ["Review (W15)", "#/review/b4", "/review"], ["Lend an item (W22)", "#/lend", "POST /items"], ["Edit listing (W22)", "#/lend/edit", "PATCH /items"], ["My listings, all statuses", "#/listings", "GET /me/items"]]);
