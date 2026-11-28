/* Account: inbox (G1, G2), notifications (W12, G3), profile + impact (J2), my evidence (W16, D2),
   settings (A5, A7, G4, theme), role application (A8), HCI notes */

/* ---------------- G1/G2: inbox ---------------- */
const THREADS = {
  b1: [["sys", "handshake", "Request accepted · 11 Oct"], ["them", "Salaam! You can collect it at the masjid parking after Asr, around 5?", "5:12 pm"], ["me", "Walaikum salaam, 5 works. I'll bring the deposit in cash.", "5:20 pm"], ["them", "Great. Bring a cloth bag, the lid is heavy.", "5:21 pm"], ["sys", "shield", "Pay deposits in person. Never share card or bank details."]],
  e1: [["sys", "users", "Event group · Mehndi rehearsal · 52 members"], ["them", "Hira: Chairs arrive at 6, not 5. Volunteers please come 20 min early.", "4:02 pm"], ["them", "Bilal: Dhol confirmed 🙂", "4:10 pm"]],
  m1: [["sys", "shield-check", "Moderator message · Case D-014"], ["them", "Please add your pickup photo to D-014 so I can compare it with the return photos.", "10:42 am"]],
  b2: [["them", "No rush, Sunday is fine.", "Yesterday"]], b6: [["them", "Is the bit set included?", "Mon"]]
};
function inboxView(sel) {
  const c = DB.conversations.find(x => x.id === sel);
  const list = DB.conversations.map(x => `<a class="li" href="#/inbox/${x.id}" style="${x.id === sel ? "background:var(--surface-2)" : ""}">${x.group ? tone("users", "violet", 40) : av(x.with)}<span class="grow"><span class="between"><span class="t">${x.group ? x.about : U(x.with).name}</span><span class="xs faint">${x.time}</span></span><span class="d" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${x.last}</span><span class="xs faint">${x.kind}${x.about && !x.group ? " · " + I(x.about)?.title : ""}</span></span>${x.unread ? `<span class="badge green" style="min-width:22px;justify-content:center">${x.unread}</span>` : ""}</a>`).join("");
  const thread = c ? `<div class="chat-head"><a class="icon-btn mob" href="#/inbox" aria-label="Back">${icon("arrow-left")}</a>${c.group ? tone("users", "violet", 38) : av(c.with)}<div class="grow"><b>${c.group ? c.about : U(c.with).name}</b><div class="xs faint">${c.kind}${c.about && !c.group ? " · " + I(c.about)?.title : ""}</div></div><button class="icon-btn" type="button" id="more" aria-label="More">${icon("ellipsis")}</button></div>
    <div class="chat-body" id="cb">${(THREADS[c.id] || []).map(([w, a, b]) => w === "sys" ? `<span class="sys">${icon(a)}${b}</span>` : `<div class="msg ${w}">${a}<small>${b}</small></div>`).join("")}</div>
    <form class="composer" id="cf"><button class="icon-btn" type="button" aria-label="Attach photo">${icon("paperclip")}</button><input class="input" id="ci" placeholder="Message" aria-label="Message"><button class="btn btn-primary" aria-label="Send">${icon("arrow-up")}</button></form>`
    : empty("message-circle", "neutral", "Pick a conversation", "Item chats open when a request is accepted. Event groups and moderator messages appear here too.");
  return { title: "Inbox", nav: "inbox", html: `<div class="wrap">${pageHead({ title: "Inbox", sub: "Item chats, event groups and moderator messages. Chats are screened for spam and personal details." })}
    <div class="chat-shell rv"><div class="chat-list ${c ? "desk" : ""}">${list}</div><div class="chat-main ${c ? "" : "desk"}">${thread}</div></div></div>`,
    after() {
      const cb = $("#cb"); if (!cb) return; cb.scrollTop = 1e6;
      $("#cf").onsubmit = e => { e.preventDefault(); const v = $("#ci").value.trim(); if (!v) return; cb.insertAdjacentHTML("beforeend", `<div class="msg me">${esc(v)}<small>now · sent</small></div>`); $("#ci").value = ""; cb.scrollTop = 1e6;
        setTimeout(() => { if (!document.body.contains(cb)) return; cb.insertAdjacentHTML("beforeend", `<div class="typing" id="ty"><i></i><i></i><i></i></div>`); cb.scrollTop = 1e6; setTimeout(() => { $("#ty")?.remove(); cb.insertAdjacentHTML("beforeend", `<div class="msg them">Sounds good 👍<small>now</small></div>`); cb.scrollTop = 1e6; }, 1400); }, 600); };
      $("#more").onclick = () => dialog(`<h2>${c.group ? c.about : U(c.with).name}</h2><div class="list mt-4"><button class="li" type="button" data-close onclick="reportDialog('message')">${icon("flag")}Report a message</button>${c.group ? `<button class="li" type="button" data-close>${icon("bell-off")}Mute group</button>` : `<button class="li" type="button" id="blk">${icon("ban")}Block ${U(c.with).short}</button>`}</div>`, "Options");
      const bl = e => { if (e.target.closest("#blk")) { dialog(`<h2>Block ${U(c.with).short}?</h2><p class="muted mt-2">You'll stop seeing each other's listings and messages. Your active loan with ${U(c.with).short} isn't cancelled. A moderator helps you finish it. ${U(c.with).short} isn't told.</p><div class="btns mt-6"><button class="btn btn-danger" data-close type="button" onclick="toast('Blocked. You can unblock in Settings.')">Block</button><button class="btn btn-ghost" data-close type="button">Cancel</button></div>`, "Block"); } };
      document.addEventListener("click", bl); cleanup = () => document.removeEventListener("click", bl);
    } };
}
route("/inbox", () => inboxView(innerWidth >= 900 ? "b1" : null));
route("/inbox/:id", ({ id }) => inboxView(id));

/* ---------------- W12: notifications (GET /notifications, POST /notifications/read) ---------------- */
route("/notifications", () => {
  const ns = DB.notifications.map(nview), cnt = g => ns.filter(n => n.grp === g).length;
  return {
  title: "Notifications", nav: "inbox",
  html: `<div class="wrap wrap-md">${pageHead({ title: "Notifications", actions: `<button class="btn btn-ghost" type="button" id="ra">${icon("check-check")}Mark all read</button><a class="btn btn-outline" href="#/settings">${icon("settings")}Preferences</a>` })}
    <div data-tabs-scope>${tabs([["all", "All", ns.length], ["requests", "Requests", cnt("requests")], ["loans", "Loans", cnt("loans")], ["moderation", "Moderation", cnt("moderation")], ["community", "Community", cnt("community")]])}
    <div class="mt-6" id="nl">${["Today", "Earlier"].map(g => `<h3 class="xs faint" data-g="${g}" style="margin:16px 0 8px;font-weight:600">${g}</h3><div class="list" data-g="${g}" data-stagger>${ns.filter(n => n.g === g).map(n => `<a class="li" href="${n.href}" data-type="${n.grp}">${tone(n.icon, n.tone, 40)}<span class="grow"><span class="t">${n.t}</span><span class="d">${n.d}</span>${n.mins ? `<span class="mt-2" style="display:inline-block">${cd(n.mins)}</span>` : ""}</span><span class="end"><span class="xs faint">${n.time}</span>${n.unread ? '<span class="status coral u" style="font-size:0" aria-label="Unread"></span>' : ""}</span></a>`).join("")}</div>`).join("")}</div>
    <div id="ne" hidden>${empty("bell-off", "neutral", "Nothing here", "No notifications of this type yet.")}</div></div>
    <p class="xs faint center mt-6">In-app only for now. Each piece of news reaches you once, however often a reminder job runs. Push alerts arrive in iteration 3.</p></div>`,
  after() {
    $("#ra").onclick = () => { $$(".u").forEach(x => x.remove()); toast("All marked as read"); };
    $(".tabs").addEventListener("click", e => { const b = e.target.closest("[data-tab]"); if (!b) return; const f = b.dataset.tab; let n = 0;
      $$("#nl .li").forEach(r => { const h = f === "all" || r.dataset.type === f; r.hidden = !h; n += h; r.classList.add("in"); });
      $$("#nl .list").forEach(l => { l.hidden = !$$(".li:not([hidden])", l).length; $(`h3[data-g="${l.dataset.g}"]`).hidden = l.hidden; }); $("#ne").hidden = n > 0; });
  } };
});

/* ---------------- A11: invite a neighbour (POST /communities/{id}/invitations -> InvitationOut) ---------------- */
route("/invite", () => {
  const T = DB.timers, open = DB.invitations.filter(i => !i.used).length;
  return { title: "Invite a neighbour", nav: "", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/home", "Home"], title: "Invite a neighbour", sub: `A code lets someone you know join ${DB.community.short} with your invitation as one of their signals. A moderator can still review it.` })}
    <div class="card card-pad-lg rv" id="ic">${tone("ticket", "saffron")}<h3 class="mt-4">Make a new code</h3><p class="small muted mt-1">Single-use, for ${DB.community.short} only, and valid for ${T.inviteTtlD} days. You can have up to ${T.maxOpenInvites} unused codes at once. You have ${open}.</p><button class="btn btn-primary mt-6" type="button" id="mk">${icon("plus")}Create invitation</button></div>
    <section class="section"><h2 class="sec-title">Your codes</h2><div class="list" id="il">${DB.invitations.map(i => `<div class="li">${tone(i.used ? "check" : "ticket", i.used ? "neutral" : "green", 36)}<span class="grow"><span class="t mono">${i.used ? "Used" : "••••-" + i.code.slice(-4)}</span><span class="d">${i.used ? "A neighbour joined with it" : "Expires " + i.expires}</span></span><span class="badge ${i.used ? "" : "green"}">${i.used ? "Used" : "Open"}</span></div>`).join("")}</div>
      <p class="xs faint mt-3">${icon("lock", "i-sm")} Only a hash of each code is stored, so it can't be shown again after you close this page.</p></section></div>`,
    after() { $("#mk").onclick = () => { if (open >= T.maxOpenInvites) return toast(`You already have ${T.maxOpenInvites} unused invitations.`, { ic: "info" });
      $("#ic").innerHTML = `${tone("ticket-check", "green")}<h3 class="mt-4">Your code</h3><div class="kpi mono mt-3" style="font-size:clamp(1.6rem,6vw,2.2rem);letter-spacing:.06em">GUL-C-R8TW</div><p class="small muted mt-2">Expires in ${T.inviteTtlD} days. Shown only once: copy it or share it now.</p><div class="btns mt-6"><button class="btn btn-primary" type="button" onclick="toast('Copied')">${icon("copy")}Copy</button><button class="btn btn-outline" type="button" onclick="toast('Share sheet opened')">${icon("share-2")}Share</button></div>`; refreshIcons();
      $("#il").insertAdjacentHTML("afterbegin", `<div class="li">${tone("ticket", "green", 36)}<span class="grow"><span class="t mono">••••-R8TW</span><span class="d">Expires in ${T.inviteTtlD} days</span></span><span class="badge green">Open</span></div>`); refreshIcons(); }; } };
});

/* ---------------- Profile + J2 impact ---------------- */
route("/profile", () => ({
  title: "Profile", nav: "",
  html: `<div class="wrap">${pageHead({ title: "" }).replace("<h1></h1>", "")}
    <div class="card card-pad-lg spot rv" style="padding:clamp(20px,4vw,36px)"><div class="between" style="flex-wrap:wrap;gap:20px"><div class="row" style="gap:20px">${av("u0", "xl", "ring")}<div><h1 style="font-size:clamp(1.6rem,3vw,2.2rem);letter-spacing:-0.035em">Sana Malik</h1><p class="muted">Lane 3, Block C · member since Mar 2026 · household account</p>
      <div class="row-wrap mt-3"><span class="badge green">${icon("user-check")}Approved member</span><span class="badge green">${icon("map-pin-check")}Lives in Block C</span><span class="badge violet">${icon("heart-handshake")}Helpful contributor</span></div></div></div>
      <div class="btns"><a class="btn btn-outline" href="#/settings">${icon("pencil")}Edit profile</a><a class="btn btn-primary" href="#/evidence">${icon("shield-check")}My evidence</a></div></div>
      <p class="mt-6" style="max-width:62ch">Teacher, keen baker. Happy to lend kitchen things and kids' books.</p></div>
    <section class="section"><h2 class="sec-title">Your impact in Block C <span class="soon">${icon("sparkles")}J2 · Soon</span></h2>
      <div class="grid-4" data-stagger>${[["hand", "green", 7, "Things borrowed", "Instead of buying"], ["hand-heart", "sky", 3, "Things lent", "To 3 neighbours"], ["piggy-bank", "saffron", 38500, "Rupees saved", "Rough value of what you didn't buy"], ["calendar-heart", "violet", 2, "Events joined", "1 coming up"]].map(([ic, t, v, l, s]) => `<div class="card spot">${tone(ic, t)}<div class="kpi mt-4" data-count="${v}">0</div><b class="small">${l}</b><p class="xs faint">${s}</p></div>`).join("")}</div></section>
    <section class="section"><h2 class="sec-title">Your contribution history</h2><div class="card">${timeline([{ s: "done", t: "Returned the camping tent to Bilal", d: "2 Oct · on time · reviewed" }, { s: "done", t: "Answered “Best tailor for uniforms?”", d: "28 Sep · marked helpful" }, { s: "done", t: "Lent your drill to Usman", d: "9–11 Oct · being inspected" }, { s: "done", t: "Joined Block C", d: "Mar 2026" }])}</div></section>
    <section class="section grid-2"><a class="card hover spot" href="#/apply-role">${tone("store", "coral")}<div class="mt-4">${soon()}</div><h3 class="mt-2">Become a vendor or moderator</h3><p class="small muted mt-1">Apply for a role. An admin reviews every application.</p></a><a class="card hover spot" href="#/hci">${tone("circle-help", "neutral")}<h3 class="mt-4">How Digital Mohalla decides</h3><p class="small muted mt-1">Evidence curves, safeguards and moderators, explained.</p></a></section></div>`
}));

/* ---------------- W16 / D2: my evidence (GET /me/evidence -> per-role FactorOut lists) ---------------- */
route("/evidence", () => {
  const E = DB.myEvidence, [b, l] = E.roles;
  return {
  title: "My evidence", nav: "",
  html: `<div class="wrap wrap-md">${pageHead({ back: ["#/profile", "Profile"], title: "My evidence", sub: "What the engine has learned from your verified loans, one factor at a time. There's never a single score." })}
    <div class="card card-2 row rv" style="align-items:flex-start">${tone("info", "sky", 36)}<p class="small">${E.note}</p></div>
    <div data-tabs-scope class="mt-6">${tabs([["b", "As a borrower"], ["l", "As a lender"]])}
      <div data-panel="b" class="mt-6"><div class="card card-pad-lg"><div class="between"><h3>As a borrower</h3><span class="xs faint">${b.factors[0].verified_loans} verified loans</span></div><div class="mt-4">${factorList(b.factors)}</div><p class="xs faint mt-4">Ranges are 90% intervals from a recency-weighted Beta posterior. Decision support, not a guarantee.</p></div></div>
      <div data-panel="l" hidden class="mt-6"><div class="card card-pad-lg"><div class="between"><h3>As a lender</h3><span class="xs faint">${l.factors[0].verified_loans} verified loans</span></div><div class="mt-4">${factorList(l.factors)}</div>
        <div class="card card-2 row mt-4" style="align-items:flex-start">${tone("eye-off", "sky", 36)}<div><b class="small">Detail appears with more loans</b><p class="small muted">With only a few loans, a detailed breakdown could reveal who you lent to (FR-T-08).</p></div></div></div></div></div>
    <section class="section"><h2 class="sec-title">What's counted</h2><div class="list" data-stagger>${[["tent", "From Bilal · on time, condition agreed", 1], ["chairs", "From Hira · dispute open", 0, "Not counted yet"], ["ladder", "From Kamran · return being confirmed", 0, "Counts when it completes"], ["deg", "From Bilal · on time, condition agreed", 1]].map(([i, d, ok, n]) => `<div class="li">${photo(I(i).photo, { w: 140, alt: "" })}<span class="grow"><span class="t">${I(i).title}</span><span class="d">${d}</span></span>${ok ? `<span class="badge green">${icon("check")}Counted</span>` : `<span class="badge saffron">${icon("hourglass")}${n}</span>`}</div>`).join("")}</div>
      <div class="card card-2 mt-4 row" style="align-items:flex-start">${tone("lightbulb", "green", 36)}<p class="small">A loan counts once both of you confirm the return. If a moderator later overturns a decision, the affected outcomes are flagged and recalculated.</p></div></section></div>`
  };
});

/* ---------------- Settings ---------------- */
route("/settings", () => {
  const vis = (l, v) => `<div class="between" style="padding:12px 0;border-top:1px solid var(--border)"><span class="small">${l}</span>${seg([["e", "Everyone"], ["c", "Block C"], ["m", "Only me"]], v)}</div>`;
  const al = (l, lock, a = 1, p = 1) => `<div class="between" style="padding:12px 0;border-top:1px solid var(--border)"><span class="small">${l}${lock ? ` <span class="badge">${icon("lock")}Always on</span>` : ""}</span><span class="row"><label class="switch" title="In app"><input type="checkbox" ${a ? "checked" : ""} ${lock ? "disabled" : ""} aria-label="${l}, in app"></label><label class="switch" title="Push"><input type="checkbox" ${p ? "checked" : ""} ${lock ? "disabled" : ""} aria-label="${l}, push"></label></span></div>`;
  return { title: "Settings", nav: "",
    html: `<div class="wrap">${pageHead({ title: "Settings" })}<div class="two-col left"><aside class="aside desk"><div class="card" style="padding:8px">${[["user", "Profile"], ["eye-off", "Privacy"], ["bell", "Notifications"], ["palette", "Appearance"], ["ban", "Blocked people"], ["badge-check", "Verification"]].map(([ic, l], i) => `<a class="li" href="#/settings" style="border:0;border-radius:10px;min-height:40px;padding:8px 12px;${i === 0 ? "background:var(--surface-2)" : ""}">${icon(ic)}${l}</a>`).join("")}</div></aside>
      <div class="stack-lg">
        <div class="card card-pad-lg rv"><h3>Profile</h3><div class="row mt-4">${av("u0", "lg")}<button class="btn btn-outline btn-sm" type="button">Change photo</button></div><div class="field mt-4"><label class="label" for="bio">Bio</label><textarea class="textarea" id="bio" style="min-height:80px">Teacher, keen baker. Happy to lend kitchen things and kids' books.</textarea></div>
          <div class="field"><label class="label" for="ar">Area</label><input class="input" id="ar" value="Lane 3, Block C"><span class="help">Lane or block only. House numbers are removed automatically.</span></div>
          <div class="field"><div class="label">Interests and skills</div><div class="chips" data-chips style="flex-wrap:wrap">${["Baking", "Gardening", "Kids' books", "Sewing", "+ Add"].map(c => `<button class="chip" type="button" aria-pressed="${c !== "+ Add"}">${c}</button>`).join("")}</div></div>
          <div class="field"><div class="label">Account type</div>${seg([["h", "Household"], ["i", "Individual"]])}</div></div>
        <div class="card card-pad-lg rv"><h3>Who can see what</h3><p class="small muted mt-1">People in an active loan with you always see your name and lane, so the handover works.</p><div class="mt-3">${vis("Bio", 1)}${vis("Interests", 0)}${vis("Photo", 1)}</div></div>
        <div class="card card-pad-lg rv"><div class="between"><h3>Notifications</h3><span class="xs faint">In app · Push</span></div><div class="mt-3">${al("New requests for your items")}${al("Handover and return reminders")}${al("Forum replies and event updates", 0, 1, 0)}${al("Disputes and moderator messages", 1)}${al("Account security", 1)}</div><div class="between mt-4"><span class="small">Quiet hours</span><span class="badge outline">${icon("moon")}11:00 pm – 7:00 am</span></div></div>
        <div class="card card-pad-lg rv"><h3>Appearance</h3><div class="opts cols-2 mt-4" id="th">${[["light", "sun", "Light"], ["dark", "moon", "Dark"]].map(([k, ic, l]) => `<label class="opt"><input type="radio" name="th" value="${k}" ${document.documentElement.dataset.theme === k ? "checked" : ""}>${tone(ic, "neutral", 34)}<span><strong>${l}</strong></span><span class="tick">${icon("check")}</span></label>`).join("")}</div>
          <div class="field"><div class="label">Language</div>${seg([["en", "English"], ["ru", "Roman Urdu"], ["ur", "اردو"]])}<span class="help">English for now. Search already understands Roman Urdu item names (deg, charpai, kafgeer).</span></div></div>
        <div class="card card-pad-lg rv"><h3>Blocked people</h3><div class="li" style="padding:12px 0">${tone("user-x", "neutral", 36)}<span class="grow small">Hamza A.</span><button class="btn btn-ghost btn-sm" type="button" onclick="toast('Unblocked Hamza A.')">Unblock</button></div><p class="xs faint">Blocking hides each other's listings and messages. It never cancels an active loan.</p></div>
        <div class="btns"><button class="btn btn-primary" type="button" onclick="toast('Settings saved')">Save changes</button><a class="btn btn-ghost" href="#/welcome">${icon("log-out")}Sign out</a></div></div></div></div>`,
    after() { $("#th").addEventListener("change", e => { if (document.documentElement.dataset.theme !== e.target.value) toggleTheme({ target: e.target }); }); } };
});

/* ---------------- A8: role application (stretch) ---------------- */
route("/apply-role", () => ({ title: "Apply for a role", nav: "", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/profile", "Profile"], title: "Apply for a role", sub: "Applying doesn't grant the role. An admin reviews it first." })}${previewBar("Role applications (A8)", "a later iteration")}
  <div class="opts mt-6">${[["store", "coral", "Vendor", "Offer a service or products to Block C"], ["shield-check", "green", "Moderator", "Review disputes and join requests for your community"], ["calendar-heart", "violet", "Event organizer", "Host events without per-event approval"]].map(([ic, t, n, d], i) => `<label class="opt"><input type="radio" name="r" ${i === 1 ? "checked" : ""}>${tone(ic, t, 38)}<span><strong>${n}</strong><p>${d}</p></span><span class="tick">${icon("check")}</span></label>`).join("")}</div>
  <div class="card mt-4"><b class="small">You're eligible</b><div class="stack mt-3">${[["Approved member of Block C", 1], ["No open disputes", 0]].map(([t, ok]) => `<div class="row small">${tone(ok ? "check" : "x", ok ? "green" : "coral", 24)}${t}${ok ? "" : ' <span class="faint">(case D-014 must close first)</span>'}</div>`).join("")}</div></div>
  <button class="btn btn-primary mt-6" type="button" aria-disabled="true" onclick="toast('You can apply once case D-014 is closed.', {ic:'info'})">Submit application</button></div>` }));

/* ---------------- HCI notes ---------------- */
route("/hci", () => {
  const P = [["eye", "Visibility of system status", "Nielsen 1", "Live countdowns, step bars on every loan card, a live request-check timeline, typing indicators.", "#/request/deg/sent"],
    ["message-square-text", "Match with the real world", "Nielsen 2", "“Not enough history yet”, not INSUFFICIENT_EVIDENCE. Codes stay under Technical details for reviewers.", "#/requests/r1"],
    ["undo-2", "User control and freedom", "Nielsen 3", "Undo on toasts, withdraw a dispute, appeal a decision, cancel an event registration, edit safeguards.", "#/decision/b11"],
    ["shield", "Error prevention", "Nielsen 5", "Overlap warning before accepting, required moderator reasons, terms must be ticked, invitation codes checked as you type.", "#/requests/r1"],
    ["images", "Recognition rather than recall", "Nielsen 6", "Return inspection shows the handover photos next to the return. The command palette lists every destination.", "#/inspect/b3"],
    ["life-buoy", "Help users recover from errors", "Nielsen 9", "“Dates taken” offers the next free dates. Offline search keeps the query. The assistant abstains and offers the forum.", "#/borrow/error"],
    ["mouse-pointer-click", "Fitts's law", "Motor", "Primary actions sit in a floating dock and the bottom tab bar on phones. Targets are at least 44 px.", "#/item/makita"],
    ["list-tree", "Hick's law and progressive disclosure", "Choice", "One decision per step, a four-step listing, evidence detail on demand, filters in a sheet on phones.", "#/lend"],
    ["layout-grid", "Gestalt: proximity and similarity", "Perception", "Bento groups related things. Handover and return share one two-column grid.", "#/home"],
    ["sparkles", "Feedback and motion", "Norman", "Shared-element transitions, a theme reveal from the toggle, springy tabs and checks. Reduced motion is respected.", "#/borrow"],
    ["scale", "Fairness by design", "Project rule", "Never a single trust number. New members are blue with a sprout, never red. Fair matching spreads requests.", "#/evidence"],
    ["accessibility", "Accessibility (WCAG 2.2 AA)", "Standard", "4.5:1 text contrast in both themes, icon plus words for every state, visible focus rings, labelled controls, live regions.", "#/settings"],
    ["lock", "Privacy by default", "Project rule", "No addresses or location trails, one-time checks, per-field visibility, small-number suppression.", "#/join/c1/verify"]];
  return { title: "Design notes", nav: "",
    html: `<div class="wrap wrap-md">${pageHead({ title: "HCI principles in this design", sub: "Where each principle shows up, so the report and the viva can point at a real screen." })}
      <div class="grid-2" data-stagger>${P.map(([ic, h, k, d, l]) => `<a class="card hover spot" href="${l}"><div class="between">${tone(ic, "neutral")}<span class="badge outline">${k}</span></div><h3 class="mt-4">${h}</h3><p class="small muted mt-2">${d}</p></a>`).join("")}</div></div>` };
});

screens("Account and communication", [["Inbox: item chats, event groups, moderators (G1, G2)", "#/inbox", "FR-C-01"], ["Notifications (W12, G3)", "#/notifications", "GET /notifications"], ["Profile + impact (J2)", "#/profile", "FR-N-02"], ["My evidence (W16, D2)", "#/evidence", "GET /me/evidence"], ["Settings: privacy, alerts, theme, block (A5, A7, G4)", "#/settings", "FR-A-12/14, FR-C-03"], ["Invite a neighbour (A11)", "#/invite", "POST /invitations"], ["Apply for a role (A8, soon)", "#/apply-role", "FR-A-15"], ["HCI principles", "#/hci"]]);
