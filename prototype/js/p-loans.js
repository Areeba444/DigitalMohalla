/* Lending and the loan lifecycle: activity board, lender decision (W1, W2, W14), counter-offer (W14),
   loan journey (+ overdue B-14, no-show B-12), handover (W3a, W3b, W17), extension (W13), return (W4),
   dispute (W5), info request (W18), decision and appeal (W20), review (W15), listings (W22) */

const L = id => DB.loans.find(x => x.id === id) || DB.loans[0];
const itemHead = (it, sub) => `<div class="card row">${photo(it.photo, { w: 200, ratio: "1", alt: "" }).replace('class="ph-img ', 'style="width:60px;border-radius:14px" class="ph-img ')}<div class="grow"><b>${it.title}</b><div class="small muted">${sub}</div></div></div>`;
const resultPage = (t, d, href, label) => `<div class="wrap wrap-sm">${done(t, d)}<div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="${href}">${label}</a><a class="btn btn-outline" href="#/activity">Activity</a></div></div>`;
const swap = html => { $("#view").innerHTML = html; hydrate($("#view")); window.scrollTo(0, 0); };

/* ---------------- Activity board ---------------- */
const loanCard = l => { const it = I(l.item), u = U(l.other), ended = l.step < 0 || l.col === "done";
  return `<a class="loan" href="${l.href}"><div class="top">${photo(it.photo, { w: 160, alt: "" })}<div class="grow"><div class="nm">${it.title}</div><div class="who">${av(l.other, "xs")}${l.role === "lender" ? "To" : "From"} ${u.short} · ${l.dates}</div></div></div>
    ${ended ? "" : `<div class="mt-3">${stepper(l.step, 6, l.tone === "coral")}</div>`}<div class="nx"><span class="status ${l.tone} ${l.col === "action" ? "live" : ""}">${l.label}</span>${l.mins && !ended ? cd(l.mins) : `<span class="xs faint">${LC[l.state] || ""}</span>`}</div></a>`; };
route("/activity", () => {
  const cols = [["action", "Needs you", "bell-ring", "saffron"], ["waiting", "Waiting on others", "hourglass", "sky"], ["active", "Out on loan", "package", "green"], ["done", "History", "history", "neutral"]];
  const board = role => `<div class="board mt-6" data-stagger>${cols.map(([k, t, ic, tn]) => { const ls = DB.loans.filter(l => l.col === k && (role === "all" || l.role === role)); return `<div class="col"><div class="col-h">${tone(ic, tn, 26)}${t}<span class="n">${ls.length}</span></div>${ls.map(loanCard).join("") || `<p class="xs faint center" style="padding:24px 0">Nothing here</p>`}</div>`; }).join("")}</div>`;
  return {
    title: "Activity", nav: "activity",
    html: `<div class="wrap">${pageHead({ title: "Activity", sub: "Every loan you're part of, grouped by what needs doing.", actions: `<a class="btn btn-outline" href="#/listings">${icon("package")}My listings</a><a class="btn btn-primary" href="#/lend">${icon("plus")}Lend an item</a>` })}
      <div data-tabs-scope>${tabs([["all", "All", DB.loans.length], ["b", "Borrowing", DB.loans.filter(l => l.role === "borrower").length], ["l", "Lending", DB.loans.filter(l => l.role === "lender").length]])}
        <div data-panel="all">${board("all")}</div><div data-panel="b" hidden>${board("borrower")}</div><div data-panel="l" hidden>${board("lender")}</div></div></div>`
  };
});

/* ---------------- W1, W2, W14: lender decides ---------------- */
route("/requests/:id", ({ id }) => {
  const r = DB.requests[id] || DB.requests.r1, it = I(r.item), u = U(r.borrower), fn = u.short;
  const act = `<div class="btns"><button class="btn btn-primary grow" type="button" data-acc>${icon("check")}Accept</button><button class="btn btn-outline grow" type="button" data-dec>Decline</button></div><button class="btn btn-ghost btn-block mt-2" type="button" data-ctr>${icon("calendar-range")}Suggest other dates</button>`;
  return {
    title: "Request from " + fn, nav: "activity",
    html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: `${fn} wants to borrow your ${it.noun}`, sub: `${r.dates[0]}–${r.dates[1]} Oct · ${r.dates[1] - r.dates[0] + 1} days · ${it.deposit ? rs(it.deposit) + " deposit" : "no deposit"}`, actions: cd(r.expires) })}
      <div class="two-col"><div class="stack-lg">
        <div class="card card-pad-lg rv"><div class="row">${av(r.borrower, "xl")}<div><h2 style="font-size:1.3rem">${u.name}</h2><p class="small muted">${u.lane}, Block C · member since ${u.since}</p></div></div>${r.msg ? `<p class="mt-6" style="font-size:18px;line-height:1.5;letter-spacing:-0.01em">“${r.msg}”</p>` : ""}</div>
        ${r.overlap ? `<div class="card card-2 row rv" style="align-items:flex-start">${tone("users", "saffron", 36)}<div><b class="small">${r.overlap.who} also asked for ${r.overlap.dates}</b><p class="small muted">Accepting ${fn} declines ${r.overlap.who} automatically and tells them the dates are taken.</p></div></div>` : ""}
        <div class="rv">${evidence(r.a, { name: fn })}</div></div>
      <aside class="aside stack">${itemHead(it, "Your listing")}<div class="card"><h3>Your decision</h3><p class="small muted mt-1 mb-4" style="margin-bottom:14px">Reply before the timer runs out, or the request expires and ${fn} is told.</p>${act}</div>
        <div class="card card-2 small">${icon("info", "i-sm")} Requests don't block dates until you accept one.</div></aside></div>
      <div class="dock mob"><div class="card">${act}</div></div></div>`,
    after() {
      const h = e => {
        if (e.target.closest("[data-acc]")) dialog(`<h2>Accept ${fn}'s request?</h2>
          <div class="list mt-6"><div class="li">${tone("calendar-check", "green", 34)}<span class="small">${r.dates[0]}–${r.dates[1]} Oct are blocked for your ${it.noun}</span></div>${r.overlap ? `<div class="li">${tone("user-x", "saffron", 34)}<span class="small">${r.overlap.who}'s request (${r.overlap.dates}) is declined automatically</span></div>` : ""}<div class="li">${tone("message-circle", "sky", 34)}<span class="small">A chat with ${fn} opens to plan the handover</span></div></div>
          <div class="card card-2 mt-4"><b class="small">Safeguards</b>${$$(".sg input").filter(c => c.checked).map(c => `<div class="row small mt-2">${icon("check", "i-sm")}${c.closest("label").querySelector("strong").textContent}</div>`).join("") || '<p class="small muted">None selected</p>'}</div>
          <div class="btns mt-6"><button class="btn btn-primary" type="button" id="ok">Accept request</button><button class="btn btn-ghost" data-close type="button">Not yet</button></div>
          <p class="xs faint mt-4">Prototype: <button class="link" type="button" id="race">simulate “someone accepted first”</button></p>`, "Accept");
        if (e.target.closest("[data-dec]")) dialog(`<h2>Decline ${fn}'s request?</h2><p class="small muted mt-1">${fn} sees “The lender can't lend on these dates.” Your reason stays private unless you add a message.</p>
          <div class="chips mt-6" data-chips style="flex-wrap:wrap">${["Not free then", "Needs repair", "Lending only to people I know", "Other"].map(t => `<button class="chip" type="button" aria-pressed="false">${t}</button>`).join("")}</div>
          <div class="field mt-4"><label class="label" for="dm">Message (optional)</label><textarea class="textarea" id="dm" style="min-height:80px" placeholder="Sorry, we're using it that weekend."></textarea></div>
          <div class="btns mt-4"><button class="btn btn-danger" type="button" id="decl">Decline</button><button class="btn btn-ghost" data-close type="button">Keep it open</button></div>`, "Decline");
        if (e.target.closest("[data-ctr]")) { dialog(`<h2>Suggest other dates</h2><p class="small muted mt-1">${fn} can take your dates or withdraw. Your suggestion expires in 24 hours.</p><div class="mt-4">${calendar({ id: "cc", sel: [17, 19], blocked: [14, 15] })}</div><button class="btn btn-primary btn-block mt-4" type="button" id="ctr">Suggest 17–19 Oct</button>`, "Suggest dates"); bindCal("cc", s => ($("#ctr").textContent = s.length > 1 ? `Suggest ${s[0]}–${s[1]} Oct` : "Pick the last day"), [17, 19]); }
        if (e.target.id === "decl") { closeDialog(); toast(`Declined. ${fn} has been told.`, { undo: () => toast("Request restored") }); }
        if (e.target.id === "ctr") { closeDialog(); toast(`New dates sent to ${fn}`); }
        if (e.target.id === "ok") { closeDialog(); swap(`<div class="wrap wrap-sm">${done(`You're lending to ${fn}`, `${r.dates[0]}–${r.dates[1]} Oct are blocked.${r.overlap ? ` ${r.overlap.who} has been told the dates are taken.` : ""}`)}<div class="card mt-6">${timeline([{ s: "done", t: "Accepted", d: "Just now" }, { s: "now", t: "Handover", d: "Do the checklist and photos when you meet" }, { s: "todo", t: "Borrowed until " + r.dates[1] + " Oct" }, { s: "todo", t: "Return and close" }])}</div><div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="#/handover/b6/lender">Start handover checklist</a><a class="btn btn-outline" href="#/inbox">${icon("message-circle")}Message ${fn}</a></div></div>`); }
        if (e.target.id === "race") dialog(`${empty("calendar-x", "coral", "These dates were just taken", `Another acceptance for overlapping dates was saved a moment before yours, so ${fn}'s request couldn't go through. Nothing was double-booked, and ${fn} will be told.`)}<div class="label">Suggest the next free dates</div><div class="chips" style="flex-wrap:wrap">${["17–19 Oct", "21–23 Oct", "24–26 Oct"].map(d => `<button class="chip" type="button" data-close onclick="toast('Suggested ${d} to ${fn}')">${icon("calendar")}${d}</button>`).join("")}</div>`, "Dates taken");
      };
      document.addEventListener("click", h); cleanup = () => document.removeEventListener("click", h);
    }
  };
});

/* ---------------- W14: borrower answers a counter-offer ---------------- */
route("/counter/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "New dates suggested", nav: "activity",
    html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: `${u.short} suggested new dates`, actions: cd(l.mins) })}${itemHead(it, `From ${u.name} · ${rs(it.deposit)} deposit`)}
      <div class="card card-pad-lg mt-4 rv"><div class="row">${av(l.other, "lg")}<p style="font-size:17px">“The 20th we're out of town. Can you take it on the 21st instead?”</p></div>
        <div class="grid-2 mt-6"><div class="card card-2" style="opacity:.7"><div class="xs faint">You asked</div><div class="kpi" style="text-decoration:line-through;font-size:1.5rem">20–21 Oct</div></div><div class="card" style="border:2px solid var(--primary)"><div class="xs" style="color:var(--primary-ink);font-weight:650">${u.short} suggests</div><div class="kpi" style="font-size:1.5rem">21–22 Oct</div></div></div>
        <p class="small muted mt-4">${icon("clock", "i-sm")} If you don't answer in time, it expires and nothing is booked.</p></div>
      <div class="dock"><div class="card btns"><button class="btn btn-primary grow" type="button" id="yes">${icon("check")}Take 21–22 Oct</button><button class="btn btn-outline grow" type="button" id="no">Withdraw</button></div></div></div>`,
    after() { $("#yes").onclick = () => swap(resultPage("Request updated", `21–22 Oct goes back to ${u.short} with your evidence report.`, "#/activity", "Back to activity")); $("#no").onclick = () => dialog(`<h2>Withdraw your request?</h2><p class="muted mt-2">${u.short} is told you no longer need it. You can always ask again.</p><div class="btns mt-6"><button class="btn btn-danger" data-close type="button" onclick="location.hash='#/activity';toast('Request withdrawn')">Withdraw</button><button class="btn btn-ghost" data-close type="button">Keep it</button></div>`, "Withdraw"); } };
});

/* ---------------- Loan journey (active, overdue, no-show) ---------------- */
route("/loan/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  if (l.state === "NO_SHOW") return { title: "No-show", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: it.title })}${empty("user-x", "neutral", "The handover didn't happen", "Neither of you confirmed the handover on 2 Oct. After two reminders and a 6-hour grace period, the booking closed as a no-show and the dates were released.")}<div class="card">${timeline([{ s: "done", t: "Accepted", d: "30 Sep" }, { s: "done", t: "Two reminders sent", d: "2 Oct, 9 am and 3 pm" }, { s: "alert", t: "Closed as no-show", d: "2 Oct, 11 pm · dates released" }])}</div><p class="small muted mt-4">A no-show is recorded on the loan, not as a judgement of either person. Think it's wrong? You can report it within 7 days.</p><div class="btns mt-4"><a class="btn btn-primary" href="#/item/makita">Ask again</a><a class="btn btn-outline" href="#/report/b12">Report a problem</a></div></div>` };
  const od = !!l.overdue;
  return { title: it.title, nav: "activity",
    html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: it.title, sub: `Borrowing from ${u.name} · ${l.dates}`, actions: `<a class="btn btn-outline" href="#/inbox">${icon("message-circle")}Message ${u.short}</a>` })}
      <div class="two-col"><div class="stack-lg">
        <div class="card card-pad-lg rv" style="${od ? "background:var(--coral-soft);border-color:transparent" : ""}"><div class="between" style="flex-wrap:wrap"><div><div class="small ${od ? "" : "muted"}" style="font-weight:600">${od ? "Overdue" : "Due back"}</div><div class="stat-big mt-1">${l.due}</div></div>${cd(l.mins)}</div>
          <p class="small mt-4" style="max-width:56ch">${od ? "Return the books today. If they're not back by 14 Oct, 8 pm, a dispute opens automatically and a moderator gets involved. Asking for more days still works." : `${u.short} gets a reminder too. Extensions need ${u.short}'s OK.`}</p><div class="mt-6">${stepsH(3, od)}</div></div>
        <div class="card rv"><h3 class="mb-4" style="margin-bottom:16px">Timeline</h3>${timeline([{ s: "done", t: "Requested", d: "10 Oct" }, { s: "done", t: `Accepted by ${u.short}`, d: "11 Oct" }, { s: "done", t: "Handover confirmed by both", d: "13 Oct, 6:10 pm · 2 photos · checklist 4/4" }, od ? { s: "alert", t: "Overdue since " + l.due, d: "Reminders sent 12 Oct 8 pm and 13 Oct 8 am" } : { s: "now", t: "Borrowed · due " + l.due, d: "Reminder 24 hours before" }, od ? { s: "todo", t: "Automatic dispute 14 Oct, 8 pm", d: "Only if it's still not back" } : { s: "todo", t: "Return and inspection" }, { s: "todo", t: "Completed, reviews open" }])}</div></div>
      <aside class="aside stack"><a class="btn btn-primary btn-lg btn-block" href="#/return/${id}">${icon("undo-2")}I've returned it</a><a class="btn btn-outline btn-block" href="#/extend/${id}">${icon("calendar-plus")}Ask for more days</a>
        <div class="card"><b class="small">Recorded at handover</b><div class="photos mt-3">${[0, 1].map(() => `<div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Handover photo"></div>`).join("")}</div><p class="xs faint mt-3">${it.deposit ? rs(it.deposit) + " deposit recorded" : "No deposit"} · checklist 4/4</p></div>
        <a class="btn btn-ghost btn-block" href="#/report/${id}" style="color:var(--coral-ink)">${icon("flag")}Report a problem</a></aside></div></div>` };
});

/* ---------------- W3a, W3b, W17: handover ---------------- */
const CHECKS = { drill: ["Powers on and runs smoothly", "Casing has no cracks", "Chuck tightens and holds a bit", "All 13 bits in the case"], deg: ["Base has no dents or holes", "Lid fits", "Handles firm", "Kafgeer included"] };
route("/handover/:id/:side", ({ id, side }) => {
  const l = L(id), it = I(l.item), u = U(l.other), checks = CHECKS[it.noun] || CHECKS.drill;
  if (side === "lender") return { title: "Handover checklist", nav: "activity",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/activity", "Activity"], eyebrow: `${icon("calendar-check", "i-sm")}Tue 14 Oct · 5:00 pm · your gate`, title: `Check the ${it.noun} with ${u.short}`, sub: `${u.short} sees exactly what you record, and you'll both compare against it at return.` })}
      <div class="two-col"><div class="stack-lg">
        <div class="card rv"><div class="between"><h3>Condition checklist</h3><span class="xs faint" id="cc">0 of ${checks.length}</span></div><div class="mt-2" id="hc">${checks.map(c => `<label class="check"><input type="checkbox"><span><strong>${c}</strong></span></label>`).join("")}</div></div>
        <div class="card rv"><div class="between"><h3>Photos</h3><span class="badge green">Suggested safeguard</span></div><div class="photos mt-4" id="hp">${["Whole item", "Close-up", "Accessories"].map(x => `<button class="photo-add" type="button" data-l="${x}">${icon("camera")}${x}</button>`).join("")}</div>
          <p class="xs faint mt-3">Camera not working? <button class="link" type="button" id="np">Use the checklist only</button> (marked “reduced evidence”)</p></div>
        <div class="card rv"><label class="label" for="hn">Anything to note?</label><textarea class="textarea" id="hn" style="min-height:80px" placeholder="e.g. small scratch on the side, already there"></textarea></div>
        <div class="card rv"><label class="check" style="padding:0"><input type="checkbox" id="dep"><span><strong>I received the ${rs(it.deposit || 2000)} deposit in cash</strong><span>Recorded only. No money moves through the app.</span></span></label></div></div>
      <aside class="aside"><div class="card" style="box-shadow:var(--shadow)"><h3>Ready to send?</h3><div class="stack mt-4" id="req">${[["Every check ticked", "ck"], ["2 photos added", "ph"], ["Deposit recorded", "dp"]].map(([t, k]) => `<div class="row small" data-k="${k}">${tone("circle", "neutral", 26)}${t}</div>`).join("")}</div><button class="btn btn-primary btn-block mt-6" id="hs" type="button" aria-disabled="true">Send to ${u.short}</button></div></aside></div></div>`,
    after() {
      let reduced = false;
      const upd = () => { const s = { ck: $$("#hc input").every(c => c.checked), ph: $$("#hp .done").length >= 2 || reduced, dp: $("#dep").checked };
        $("#cc").textContent = `${$$("#hc input:checked").length} of ${checks.length}`;
        $$("#req [data-k]").forEach(r => { r.firstElementChild.outerHTML = tone(s[r.dataset.k] ? "check" : "circle", s[r.dataset.k] ? "green" : "neutral", 26); });
        $("#hs").setAttribute("aria-disabled", !(s.ck && s.ph && s.dp)); refreshIcons(); };
      $$("#hp .photo-add").forEach(p => p.onclick = () => { p.classList.add("done"); p.innerHTML = `<img src="${img(it.photo, 240, 240)}" alt="${p.dataset.l}"><span class="ok">${icon("check")}</span><span class="cap">${p.dataset.l}</span>`; upd(); });
      $$("#hc input, #dep").forEach(c => c.onchange = upd);
      $("#np").onclick = () => { reduced = true; toast("This handover will be marked “reduced evidence”.", { ic: "info" }); upd(); };
      $("#hs").onclick = () => { if ($("#hs").getAttribute("aria-disabled") === "true") return toast("Finish the three items on the right first.", { ic: "info" });
        swap(`<div class="wrap wrap-sm">${empty("smartphone", "sky", `Waiting for ${u.short} to confirm`, `They'll see your checklist${reduced ? "" : " and photos"}. The loan starts when they confirm.`)}<div class="card">${timeline([{ s: "done", t: "You recorded the condition", d: "Just now" }, { s: "now", t: `${u.short} confirms` }, { s: "todo", t: "Borrowed until 16 Oct, 8 pm" }])}</div></div>`); };
    } };
  return { title: "Confirm handover", nav: "activity",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/activity", "Activity"], eyebrow: `${icon("map-pin", "i-sm")}Today · 5:00 pm · masjid parking`, title: `Confirm the ${it.noun} from ${u.short}`, sub: `${u.short} recorded the condition at 5:04 pm. Check it matches what's in front of you.`, actions: cd(l.mins) })}
      <div class="two-col"><div class="stack-lg">${photo(it.photo, { w: 1200, ratio: "16/8", alt: it.title, cls: "rv" })}
        <div class="card rv"><h3>${u.short}'s checklist</h3><div class="mt-3">${checks.map(c => `<div class="row small" style="padding:7px 0">${tone("check", "green", 24)}${c}</div>`).join("")}</div></div>
        <div class="card rv"><h3>Photos</h3><div class="photos mt-3">${["Whole item", "Base", "Lid"].map(x => `<div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="${x}"><span class="cap">${x}</span></div>`).join("")}</div><p class="small mt-4"><b>Note:</b> “Small dent on one handle, already there.”</p></div>
        <div class="card rv"><label class="label" for="bn">Your remarks (optional)</label><textarea class="textarea" id="bn" style="min-height:70px"></textarea></div></div>
      <aside class="aside"><div class="card" style="box-shadow:var(--shadow)"><div class="between"><span class="muted small">Deposit recorded</span><b>${rs(it.deposit)}</b></div><div class="between mt-2"><span class="muted small">Return by</span><b>${l.due}</b></div>
        <button class="btn btn-primary btn-block mt-6" type="button" id="ok">${icon("check")}It matches. Start the loan</button><button class="btn btn-ghost btn-block mt-2" type="button" id="no">Something doesn't match</button></div></aside></div></div>`,
    after() {
      $("#ok").onclick = () => swap(resultPage(`Enjoy the ${it.noun}`, `Return it to ${u.short} by ${l.due}. We'll remind you a day before.`, "#/loan/b2", "See the loan"));
      $("#no").onclick = () => dialog(`<h2>What doesn't match?</h2><p class="small muted mt-1">The loan won't start until it's sorted.</p><div class="opts mt-6"><label class="opt"><input type="radio" name="w" checked>${tone("message-square-text", "sky", 34)}<span><strong>Add a note and take it</strong><p>For small things. ${u.short} sees it.</p></span><span class="tick">${icon("check")}</span></label><label class="opt"><input type="radio" name="w">${tone("scale", "coral", 34)}<span><strong>Raise a condition dispute</strong><p>A Block C moderator reviews both records.</p></span><span class="tick">${icon("check")}</span></label></div><button class="btn btn-primary btn-block mt-6" data-close type="button" onclick="toast('Note added for ${u.short}')">Continue</button>`, "Mismatch");
    } };
});

/* ---------------- W13: extension ---------------- */
route("/extend/:id", ({ id }) => {
  const l = L(id), u = U(l.other);
  return { title: "Ask for more days", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/loan/" + id, "Loan"], title: "Ask for more days", sub: `Due ${l.due}. ${u.short} decides, and the due date stays the same until then.` })}
    <div class="card rv">${calendar({ id: "ec", sel: [15, 17], blocked: [19, 20] })}</div>
    <div class="card card-2 mt-4 between rv"><span class="small muted">You're asking for</span><b id="es">+2 days · until Fri 17 Oct</b></div>
    <div class="card mt-4 rv"><label class="label" for="er">Reason</label><textarea class="textarea" id="er" style="min-height:80px">The painter is coming a day late.</textarea></div>
    <div class="dock"><div class="card"><button class="btn btn-primary btn-block" type="button" id="ask">Ask ${u.short}</button></div></div></div>`,
    after() { bindCal("ec", s => { const e = s[1] ?? s[0]; $("#es").textContent = e > 15 ? `+${e - 15} day${e - 15 > 1 ? "s" : ""} · until ${dow(e)} ${e} Oct` : "Pick a later day"; }, [15, 17]); $("#ask").onclick = () => swap(resultPage(`Asked ${u.short} for 2 more days`, `Keep it past ${l.due} only if ${u.short} says yes.`, "#/loan/" + id, "Back to the loan")); } };
});
route("/extend-respond/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Extension request", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: `${u.short} asks to keep the ${it.noun} 2 more days`, sub: "From 27 Oct to Wed 29 Oct" })}
    <div class="card card-pad-lg rv"><div class="row">${av(l.other, "lg")}<p style="font-size:17px">“Rain in Murree, we're back two days later. Will dry it before returning.”</p></div></div>
    <div class="card mt-4 rv"><div class="between"><h3>Your ${it.noun}'s calendar</h3><span class="badge green">${icon("check")}No conflicts</span></div><div class="mt-4">${calendar({ sel: [24, 29] })}</div></div>
    <div class="dock"><div class="card btns"><button class="btn btn-primary grow" type="button" id="y">${icon("check")}Approve</button><button class="btn btn-outline grow" type="button" id="n">Keep 27 Oct</button></div></div></div>`,
    after() { $("#y").onclick = () => swap(resultPage("Extension approved", `${u.short}'s new due date is 29 Oct. Reminders move with it.`, "#/activity", "Back to activity")); $("#n").onclick = () => { toast(`${u.short} has been told the due date stays 27 Oct`); location.hash = "#/activity"; }; } };
});

/* ---------------- Return (borrower) and W4 inspection (lender) ---------------- */
route("/return/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Return", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/loan/" + id, "Loan"], title: `Return the ${it.noun}`, sub: l.overdue ? "1 day late. Returning now stops the automatic dispute." : `On time. Due ${l.due}.` })}
    <div class="opts rv"><label class="opt"><input type="radio" name="h" checked>${tone("handshake", "green", 36)}<span><strong>Hand it to ${u.short}</strong><p>You check it together</p></span><span class="tick">${icon("check")}</span></label><label class="opt"><input type="radio" name="h">${tone("house", "sky", 36)}<span><strong>Leave it at ${u.short}'s gate</strong><p>${u.short} inspects it later</p></span><span class="tick">${icon("check")}</span></label></div>
    <div class="card mt-4 rv"><h3>Photos of how you're returning it</h3><p class="small muted mt-1">They match the handover photos and protect you too.</p><div class="photos mt-4"><div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Return photo"><span class="ok">${icon("check")}</span></div><button class="photo-add" type="button">${icon("camera")}Close-up</button><button class="photo-add" type="button">${icon("camera")}Extra</button></div></div>
    <div class="card mt-4 rv"><label class="label" for="rn">Note for ${u.short}</label><input class="input" id="rn" value="Thanks! Wiped the feet clean."></div>
    <div class="dock"><div class="card"><button class="btn btn-primary btn-block" id="b" type="button">Tell ${u.short} it's back</button></div></div></div>`,
    after() { $("#b").onclick = () => swap(resultPage(`${u.short} has been told`, `They'll compare it with the handover photos. Reviews open once they confirm.`, "#/activity", "Back to activity")); } };
});
route("/inspect/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  const rows = [["Powers on and runs smoothly", 1], ["Casing has no cracks", 0], ["Chuck tightens and holds a bit", 1], ["All 13 bits in the case", 1]];
  return { title: "Inspect the return", nav: "activity", html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: `Inspect the ${it.noun} from ${u.short}`, sub: "Returned 11 Oct, 7:40 pm · left at your gate · on time" })}
    <div class="two-col"><div class="stack-lg"><div class="card rv"><div class="between"><h3>Then and now</h3><span class="badge green">${icon("clock")}On time</span></div>
      <div class="cmp mt-4"><div><div class="lab">${icon("package-check")}Handover · 9 Oct</div>${photo(it.photo, { w: 600, ratio: "1", alt: "Handover" })}</div><div><div class="lab">${icon("undo-2")}Return · 11 Oct</div>${photo(it.photo, { w: 600, ratio: "1", alt: "Return", cls: "flag", inner: '<span class="pin" style="left:55%;top:42%">1</span>' })}</div></div>
      <p class="small mt-3" style="color:var(--coral-ink)"><b>1</b> You marked a possible crack near the chuck.</p></div>
      <div class="card rv"><h3>Checklist</h3><p class="small muted mt-1">Tap “Changed” for anything that isn't as it was.</p><div class="mt-2" id="rows">${rows.map(([t, s], i) => `<div class="check-row"><div><b class="small">${t}</b><div class="xs" style="color:var(--primary-ink)">${icon("check", "i-sm")} OK at handover</div></div>${seg([["same", "Same"], ["changed", "Changed"]], s ? 0 : 1, "danger").replace('class="seg', `data-r="${i}" class="seg`)}</div>`).join("")}</div></div></div>
    <aside class="aside"><div class="card" id="ra" style="box-shadow:var(--shadow)"></div></aside></div></div>`,
    after() {
      const paint = () => { const n = $$('#rows [data-v="changed"][aria-selected="true"]').length;
        $("#ra").innerHTML = n ? `${tone("triangle-alert", "coral")}<h3 class="mt-4">${n} thing${n > 1 ? "s" : ""} changed</h3><p class="small muted mt-2">Talk to ${u.short} first, or report it. Reporting pauses the loan and the deposit record until a moderator decides.</p><a class="btn btn-danger btn-block mt-6" href="#/report/b3">${icon("flag")}Report damage</a><a class="btn btn-outline btn-block mt-2" href="#/inbox">${icon("message-circle")}Message ${u.short}</a>`
          : `${tone("circle-check", "green")}<h3 class="mt-4">Everything matches</h3><p class="small muted mt-2">Closing marks the ${rs(2000)} deposit returned and opens reviews for both of you.</p><button class="btn btn-primary btn-block mt-6" id="cl" type="button">Close the loan</button>`;
        refreshIcons(); $("#cl")?.addEventListener("click", () => swap(resultPage("Loan complete", `Deposit marked returned. You and ${u.short} can review each other now.`, "#/review/b4", "Leave a review"))); };
      $("#rows").addEventListener("click", e => { if (e.target.closest("[role=tab]")) setTimeout(paint, 0); }); paint();
    } };
});

/* ---------------- W5: report a problem ---------------- */
route("/report/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Report a problem", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: "Report a problem", sub: "You can report a problem with this loan until 18 Oct." })}${itemHead(it, `${l.role === "lender" ? "Lent to" : "Borrowed from"} ${u.short} · ${l.dates}`)}
    <div class="field mt-6 rv"><span class="label">What happened?</span><div class="opts cols-2">${[["hammer", "Damage"], ["package-x", "Not returned"], ["file-diff", "Condition doesn't match"], ["user-x", "No-show"]].map(([ic, t], i) => `<label class="opt"><input type="radio" name="t" ${i === 0 ? "checked" : ""}>${tone(ic, "coral", 32)}<span><strong>${t}</strong></span></label>`).join("")}</div></div>
    <div class="field rv"><label class="label" for="dd">Describe it</label><textarea class="textarea" id="dd">Hairline crack on the casing next to the chuck. It wasn't there at handover (photo 1).</textarea><span class="help">Say what you saw. The moderator sees both checklists and every photo too.</span></div>
    <div class="field rv"><span class="label">Evidence</span><div class="photos"><div class="photo-add done flag"><img src="${img(it.photo, 240, 240)}" alt="Crack"><span class="cap">Crack</span></div><button class="photo-add" type="button">${icon("image-plus")}Photo</button><button class="photo-add" type="button">${icon("paperclip")}File</button></div></div>
    <div class="card card-2 mt-6 row rv" style="align-items:flex-start">${tone("lock", "saffron", 36)}<div><b class="small">The loan pauses while it's reviewed</b><p class="small muted">Nobody can move it forward and the deposit record is frozen. ${u.short} has 48 hours to reply. You can withdraw any time.</p></div></div>
    <div class="dock"><div class="card"><a class="btn btn-danger btn-block" href="#/case/b3">Send to moderators</a></div></div></div>` };
});

/* ---------------- Case progress (b3 raiser) and W18 info request (b5) ---------------- */
route("/case/:id", ({ id }) => {
  const raiser = id === "b3", l = L(id), it = I(l.item), u = U(l.other);
  return { title: "Dispute", nav: "activity", html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], eyebrow: raiser ? "Case D-015" : "Case D-014", title: raiser ? "Damage reported" : "Condition dispute", sub: raiser ? `You reported a crack near the chuck. ${u.short} has 48 hours to reply.` : "Hira reported 2 cracked chairs at return. The moderator wants your side.", actions: stateChip("dispute", "Under review") })}
    <div class="two-col"><div class="stack-lg">
      ${!raiser ? `<div class="card card-pad-lg rv" style="border:1.5px solid var(--saffron)"><div class="between">${`<span class="row">${av("mod", "sm")}<b>Imran (moderator) asked you</b></span>`}${cd(l.mins)}</div>
        <p class="mt-4" style="font-size:17px">“Do you have photos from when you collected the chairs? Please also say where they were stored.”</p>
        <p class="xs mt-3" style="color:var(--saffron-ink)">Reply by 16 Oct, 6 pm. With no reply, the case is marked “no response” and decided with what's there.</p>
        <div class="field mt-6"><label class="label" for="mr">Your reply</label><textarea class="textarea" id="mr">They stayed stacked in our garage. Two already had scratches. Here's my pickup photo.</textarea></div>
        <div class="photos mt-2"><div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Pickup"><span class="cap">Pickup</span></div><button class="photo-add" type="button">${icon("image-plus")}Add</button></div>
        <button class="btn btn-primary mt-6" type="button" id="sr">Send reply</button></div>` : ""}
      <div class="card rv"><h3 style="margin-bottom:16px">Progress</h3>${timeline([{ s: "done", t: "Report sent", d: raiser ? "Just now" : "15 Oct, 6:27 pm by Hira" }, { s: raiser ? "now" : "done", t: `${raiser ? u.short : "You"} replied`, d: raiser ? "Up to 48 h" : "15 Oct, 9:10 pm" }, { s: raiser ? "todo" : "now", t: "Moderator reviews both sides", d: raiser ? "" : "More information requested" }, { s: "todo", t: "Decision with a written reason", d: "Either side can appeal to a second moderator" }])}</div></div>
    <aside class="aside stack"><div class="card card-2 row" style="align-items:flex-start">${tone("lock", "saffron", 34)}<div><b class="small">Loan paused</b><p class="xs muted">Frozen until a decision.</p></div></div><div class="card"><b class="small">Who can see this</b><p class="xs muted mt-1">Both of you and Block C moderators. Your chat on this loan is visible to them only while a dispute is open.</p></div>
      ${raiser ? `<button class="btn btn-outline btn-block" type="button" id="wd">${icon("rotate-ccw")}Withdraw report</button>` : `<p class="xs faint">Only Hira can withdraw this report.</p>`}</aside></div></div>`,
    after() { $("#sr")?.addEventListener("click", () => swap(resultPage("Reply sent to Imran", "Your reply and photo are part of the case now.", "#/activity", "Back to activity"))); $("#wd")?.addEventListener("click", () => dialog(`<h2>Withdraw your report?</h2><p class="muted mt-2">The loan goes back to “Being returned” and you can close it normally.</p><div class="btns mt-6"><button class="btn btn-primary" data-close type="button" onclick="toast('Report withdrawn. Loan restored.');location.hash='#/inspect/b3'">Withdraw</button><button class="btn btn-ghost" data-close type="button">Keep it open</button></div>`, "Withdraw")); } };
});

/* ---------------- W20: decision and appeal ---------------- */
route("/decision/:id", ({ id }) => {
  const it = I(L(id).item);
  return { title: "Decision on D-011", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], eyebrow: "Case D-011 · plastic chairs, 5–6 Sep", title: "Decided in favour of the lender" })}
    <div class="card card-pad-lg rv"><div class="row">${av("mod2", "sm")}<div><b>Rabia S.</b><div class="xs faint">12 Oct, 4:10 pm · signed and logged</div></div></div><p class="mt-4" style="font-size:17px">“The return photo shows a split leg that isn't in the handover photo. Rs 600 deduction from the recorded deposit, agreed in person.”</p>
      <div class="row-wrap mt-4"><span class="badge">${icon("package-check")}Item with the lender</span><span class="badge">${icon("banknote")}Rs 600 deduction recorded</span></div></div>
    <div class="card card-pad-lg mt-4 rv" id="ab"><div class="between"><h3>Appeal to a second moderator</h3>${cd(7200)}</div><p class="small muted mt-2">A different moderator reviews the whole case again. If they reverse it, both decisions stay in the log and your evidence is corrected.</p>
      <div class="field mt-6"><label class="label" for="ap">Why should it be looked at again?</label><textarea class="textarea" id="ap">The leg was already split at pickup. It's in my pickup photo, which wasn't attached to the case.</textarea></div>
      <div class="photos mt-2"><div class="photo-add done"><img src="${img(it.photo, 240, 240)}" alt="Pickup"><span class="cap">Pickup photo</span></div><button class="photo-add" type="button">${icon("image-plus")}Add</button></div>
      <button class="btn btn-primary mt-6" type="button" id="send">Send appeal</button></div></div>`,
    after() { $("#send").onclick = () => { if ($("#ap").value.trim().length < 20) { $("#ap").setAttribute("aria-invalid", "true"); return toast("Say why in a sentence or two.", { ic: "info" }); } $("#ab").innerHTML = `<h3>Appeal sent</h3><div class="mt-4">${timeline([{ s: "done", t: "Appeal received", d: "Case A-003" }, { s: "now", t: "Second moderator review", d: "Imran Q., not involved before" }, { s: "todo", t: "Upheld or reversed, with a reason" }])}</div>`; refreshIcons(); toast("Appeal sent to a second moderator"); }; } };
});

/* ---------------- W15: review ---------------- */
route("/review/:id", ({ id }) => {
  const l = L(id), it = I(l.item), u = U(l.other);
  const dim = (q, o) => `<div style="padding:14px 0;border-top:1px solid var(--border)"><b class="small">${q}</b><div class="chips mt-3" data-chips style="flex-wrap:wrap">${o.map(([t, ic], i) => `<button class="chip" type="button" aria-pressed="${i === o.length - 1}">${icon(ic)}${t}</button>`).join("")}</div></div>`;
  return { title: "Review", nav: "activity", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/activity", "Activity"], title: `How was borrowing from ${u.short}?`, sub: `${it.title} · returned on time`, actions: cd(5 * 1440 + 200, "calm") })}
    <div class="card card-pad-lg rv">${dim("Was the item as described?", [["No", "thumbs-down"], ["Mostly", "minus"], ["Yes", "thumbs-up"]])}${dim(`Was ${u.short} on time for handover?`, [["Late", "clock-alert"], ["A bit late", "clock"], ["On time", "timer"]])}${dim("How was communication?", [["Hard", "message-circle-x"], ["OK", "message-circle"], ["Easy", "message-circle-heart"]])}${dim(`Borrow from ${u.short} again?`, [["No", "x"], ["Maybe", "circle-help"], ["Yes", "heart"]])}</div>
    <div class="card mt-4 rv"><label class="label" for="rc">Anything neighbours should know? <span class="faint" style="font-weight:400">(optional)</span></label><textarea class="textarea" id="rc" maxlength="280">Tent was clean and complete, pegs counted. Bilal showed us how to set up the fly.</textarea><span class="help">Describe what happened, not the person. Reviews that look like retaliation are held for a moderator.</span></div>
    <p class="xs faint mt-4">${icon("lock", "i-sm")} One review each. You both see them at the same time. You can edit yours for 48 hours.</p>
    <div class="dock"><div class="card"><button class="btn btn-primary btn-block" type="button" id="p">Post review</button></div></div></div>`,
    after() { $("#p").onclick = () => swap(resultPage("Review saved", `It appears when ${u.short} posts theirs, or in 5 days, whichever is first.`, "#/activity", "Back to activity")); } };
});

/* ---------------- W22: listings ---------------- */
function listingWizard(edit) {
  const steps = [
    ["Photos and title", () => `<div class="photos"><div class="photo-add done"><img src="${img(I("drill").photo, 300, 300)}" alt="Cover"><span class="cap">Cover</span></div><button class="photo-add" type="button">${icon("camera")}Camera</button><button class="photo-add" type="button">${icon("image-plus")}Gallery</button></div>
      <div class="field mt-6"><label class="label" for="lt">Title</label><input class="input" id="lt" value="Bosch impact drill + bits" maxlength="60"><div class="between xs faint mt-1"><span>Say what it is and what comes with it.</span><span><span id="ltc">24</span>/60</span></div></div>
      <div class="field"><label class="label" for="ld">Description</label><textarea class="textarea" id="ld">650W impact drill with a 13-piece bit set and a spare chuck key. Plugs in, no battery needed.</textarea><span class="help">Roman Urdu names like “deg” or “charpai” are fine. Search understands them.</span></div>`],
    ["Category and condition", () => `<div class="label">Category</div><div class="opts cols-2">${DB.categories.slice(1).map(c => `<label class="opt" style="padding:12px"><input type="radio" name="c" ${c.id === "tools" ? "checked" : ""}>${tone(c.icon, c.id === "medical" ? "violet" : "neutral", 32)}<span><strong class="small">${c.label}</strong></span></label>`).join("")}</div><p class="xs faint mt-2">${icon("badge-check", "i-sm")} Medical, vehicle and high-value electronics are for verified accounts only.</p>
      <div class="label mt-6" style="margin-top:22px">Condition</div><div class="opts">${[["sparkles", "Like new", "No marks, all parts"], ["thumbs-up", "Good", "Light wear, works perfectly"], ["wrench", "Fair", "Visible wear, works fine"]].map(([ic, t, d], i) => `<label class="opt"><input type="radio" name="cd" ${i === 1 ? "checked" : ""}>${tone(ic, "green", 34)}<span><strong>${t}</strong><p>${d}</p></span><span class="tick">${icon("check")}</span></label>`).join("")}</div>`],
    ["Your terms", () => `<div class="field"><label class="label" for="dp">Deposit</label><div class="input-wrap"><span style="position:absolute;left:14px;color:var(--text-3);font-weight:600">Rs</span><input class="input" id="dp" value="2,000" style="padding-left:44px"></div><span class="help">Recorded in the app at handover. Cash changes hands in person.</span></div>
      <div class="field"><div class="label">Longest loan</div><div class="chips" data-chips style="flex-wrap:wrap">${["1 day", "2 days", "3 days", "1 week", "2 weeks"].map((d, i) => `<button class="chip" type="button" aria-pressed="${i === 2}">${d}</button>`).join("")}</div></div>
      <div class="field"><div class="label">Handover</div><div class="opts cols-2">${[["house", "From my gate"], ["map-pin", "A public spot"]].map(([ic, t], i) => `<label class="opt"><input type="radio" name="ho" ${i === 0 ? "checked" : ""}>${tone(ic, "sky", 32)}<span><strong>${t}</strong></span></label>`).join("")}</div></div>
      <div class="field"><label class="label" for="ru">Rules for borrowers</label><textarea class="textarea" id="ru" style="min-height:80px">Masonry bits only for brick and concrete.</textarea></div>`],
    ["Availability", () => `<p class="muted small mb-4" style="margin-bottom:14px">Tap days to block them. Dates you've accepted can't change.</p>${calendar({ blocked: [20, 21], sel: edit ? [14, 16] : [] })}
      <div class="card card-2 mt-6 row">${tone("shield-check", "green", 34)}<div><b class="small">Quick automatic check</b><p class="xs muted">New listings are screened for duplicates and banned items. Most go live in under a minute.</p></div></div>`]
  ];
  return { title: edit ? "Edit listing" : "Lend an item", nav: "activity",
    html: `<div class="wrap wrap-md">${pageHead({ back: [edit ? "#/listings" : "#/home", edit ? "My listings" : "Home"], title: edit ? "Edit listing" : "Lend an item", sub: edit ? "Booking for 14–16 Oct is accepted. Those dates stay fixed." : "Four short steps. You can save a draft at any point.", actions: `<button class="btn btn-ghost" type="button" id="dr">${icon("save")}Save draft</button>` })}
      <div class="two-col"><div><div class="steps-h" id="sh">${steps.map(([t], i) => `<div class="s ${i === 0 ? "cur" : ""}"><i></i><span>${i + 1}. ${t}</span></div>`).join("")}</div><div class="card card-pad-lg mt-6" id="st"></div>
        <div class="btns mt-4" style="justify-content:space-between"><button class="btn btn-outline" id="bk" type="button" hidden>${icon("arrow-left")}Back</button><span></span><button class="btn btn-primary" id="nx" type="button">Continue ${icon("arrow-right")}</button></div></div>
      <aside class="aside desk"><div class="xs faint" style="margin-bottom:10px;font-weight:600">Live preview</div>${itemCard(I("drill"))}<div class="card card-2 mt-4 small">${icon("lightbulb", "i-sm")} Listings with 3+ photos get twice as many requests.</div></aside></div></div>`,
    after() {
      let s = 0;
      const pnt = () => { $("#st").innerHTML = `<h2 style="font-size:1.25rem;margin-bottom:18px">${steps[s][0]}</h2>${steps[s][1]()}`; hydrate($("#st")); $("#bk").hidden = !s; $("#nx").innerHTML = s === 3 ? (edit ? "Save changes" : "Publish listing") : `Continue ${icon("arrow-right")}`; $$("#sh .s").forEach((x, i) => (x.className = "s " + (i < s ? "on" : i === s ? "cur" : ""))); refreshIcons();
        $("#lt")?.addEventListener("input", e => ($("#ltc").textContent = e.target.value.length));
        $$("#st button.photo-add").forEach(p => p.onclick = () => { p.classList.add("done"); p.innerHTML = `<img src="${img(I("drill").photo, 300, 300)}" alt="Photo"><span class="ok">${icon("check")}</span>`; refreshIcons(); }); };
      $("#nx").onclick = () => { if (s === 0 && !$("#lt").value.trim()) { $("#lt").setAttribute("aria-invalid", "true"); return toast("Add a title first.", { ic: "info" }); } if (s < 3) { s++; pnt(); window.scrollTo({ top: 0, behavior: "smooth" }); } else swap(resultPage(edit ? "Changes saved" : "Your drill is live in Block C", edit ? "Neighbours see the new details now." : "It passed the automatic check. Requests arrive with an evidence report.", "#/item/drill", "View listing")); };
      $("#bk").onclick = () => { s--; pnt(); };
      $("#dr").onclick = () => toast("Draft saved. Finish it from My listings.");
      pnt();
    } };
}
route("/lend", () => listingWizard(false));
route("/lend/edit", () => listingWizard(true));
route("/listings", () => ({ title: "My listings", nav: "activity", html: `<div class="wrap">${pageHead({ back: ["#/activity", "Activity"], title: "My listings", actions: `<a class="btn btn-primary" href="#/lend">${icon("plus")}New listing</a>` })}
  <div class="grid-3" data-stagger>
    <div class="card" style="padding:0;overflow:hidden">${photo(I("drill").photo, { w: 700, ratio: "16/10", alt: "", tl: `<span class="badge glass"><span class="live"></span>Live</span>` })}<div style="padding:16px"><b>Bosch impact drill + bits</b><p class="small muted mt-1">2 requests this month · lent 3 times</p><div class="btns mt-4"><a class="btn btn-primary btn-sm" href="#/requests/r1">1 request waiting</a><a class="btn btn-outline btn-sm" href="#/lend/edit">Edit</a></div></div></div>
    <div class="card" style="padding:0;overflow:hidden"><div class="ph-img" style="aspect-ratio:16/10;display:grid;place-items:center">${tone("image-plus", "neutral", 52)}</div><div style="padding:16px"><div class="between"><b>Sewing machine</b><span class="badge">Draft</span></div><p class="small muted mt-1">Missing photos and condition</p><div class="mt-3">${stepper(1, 4)}</div><a class="btn btn-outline btn-sm mt-4" href="#/lend">Continue</a></div></div>
    <div class="card" style="padding:0;overflow:hidden">${photo(I("books").photo, { w: 700, ratio: "16/10", alt: "", tl: `<span class="badge glass">Paused</span>` })}<div style="padding:16px"><b>Cake tins, set of 3</b><p class="small muted mt-1">Hidden from search since 2 Oct</p><button class="btn btn-outline btn-sm mt-4" type="button" onclick="toast('Listing is live again')">${icon("play")}Resume</button></div></div></div></div>` }));

screens("Resident · lending and loans", [["Activity board", "#/activity"], ["Request: not enough history (W1)", "#/requests/r1", "ES-01"], ["Request: community paths", "#/requests/r2", "ES-13"], ["Request: enough evidence", "#/requests/r3", "ES-02"], ["Counter-offer: respond (W14)", "#/counter/b9", "FR-B-10"],
  ["Loan journey", "#/loan/b2", "FR-B-08"], ["Loan overdue → auto-dispute", "#/loan/b7", "FR-B-14"], ["Loan no-show", "#/loan/b12", "FR-B-12"], ["Handover: lender checklist (W3a, W17)", "#/handover/b6/lender", "FR-B-11"], ["Handover: borrower confirms (W3b)", "#/handover/b1/borrower"],
  ["Extension: ask (W13)", "#/extend/b2", "FR-B-14"], ["Extension: respond (W13)", "#/extend-respond/b10"], ["Return it", "#/return/b2", "FR-B-13"], ["Return inspection (W4)", "#/inspect/b3", "FR-B-13"], ["Report a problem (W5)", "#/report/b3", "FR-B-16"],
  ["Your report in progress", "#/case/b3", "ADR-0004"], ["Reply to moderator (W18)", "#/case/b5", "FR-B-17"], ["Decision + appeal (W20)", "#/decision/b11", "FR-T-11"], ["Review (W15)", "#/review/b4", "FR-T-09"], ["Lend an item (W22)", "#/lend", "FR-B-01"], ["Edit listing (W22)", "#/lend/edit"], ["My listings + drafts", "#/listings"]]);
