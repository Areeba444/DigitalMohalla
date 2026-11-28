/* Public website, registration (W8) and community joining (W9, W10) */

const DEMO = {
  new: { ab: [1, 1], state: "insufficient", t: "New neighbour, no loans yet", d: "The curve is flat: any outcome is possible. Shown neutrally. No history isn't a bad history." },
  some: { ab: [4.2, 2.1], state: "review", t: "Two people you know vouch indirectly", d: "Community paths lift the evidence a little. The lender is asked to take a look." },
  lots: { ab: [16, 1.8], state: "sufficient", t: "Eleven loans, ten on time", d: "Lots of consistent evidence: a narrow, confident shape." }
};

route("/welcome", () => ({
  role: "public", title: "Borrow from your street",
  html: `<div class="wrap">
    <section class="hero-l">
      <a class="pill-link rv" href="#/register"><span class="badge green">${icon("sparkles")}New</span>Iteration 2 preview · Block C pilot ${icon("arrow-right", "i-sm")}</a>
      <h1 class="rv" style="--d:1">Borrow from your street, with evidence.</h1>
      <p class="rv" style="--d:2">Digital Mohalla lets verified neighbours lend and borrow everyday things. Every request comes with an honest evidence report, and uncertain cases go to a person.</p>
      <div class="btns rv" style="--d:3;justify-content:center;margin-top:30px"><a class="btn btn-primary btn-lg" href="#/register">Join your mohalla ${icon("arrow-right")}</a><a class="btn btn-outline btn-lg" href="#/home">${icon("play")}Explore the demo</a></div>
      <p class="xs faint mt-4 rv" style="--d:4">${icon("lock", "i-sm")} No house numbers. No location trails. No single trust score.</p>
    </section>

    <div class="showcase rv"><div class="showcase-in">
      <div class="card" style="padding:0;overflow:hidden">${photo(I("deg").photo, { w: 900, ratio: "16/10", shade: true, eager: true, alt: "A large deg", tl: `<span class="badge glass">${icon("flame")}Booked 9× this season</span>`, bl: `<div class="between"><div><b style="font-size:18px">Large deg for 40 guests</b><div class="xs" style="opacity:.8">Bilal R. · Lane 2 · Rs 1,500 deposit</div></div><span class="btn btn-sm" style="background:#fff;color:#0D0F0E">Request</span></div>` })}</div>
      <div class="card stack"><div class="between"><span class="small" style="font-weight:650">Request from Nadia</span>${cd(300)}</div>${stateChip("review")}${betaCurve(4.2, 2.1, "review").replace('class="curve"', 'class="curve" style="padding:0"')}</div>
      <div class="card stack"><span class="small muted">This month in Block C</span><div class="stat-big" data-count="168">0</div><span class="small muted">loans completed</span>
        <svg class="spark mt-3" viewBox="0 0 200 44" preserveAspectRatio="none"><path class="a" d="M0 40 L20 34 L40 36 L60 28 L80 30 L100 20 L120 24 L140 14 L160 16 L180 8 L200 6 L200 44 L0 44Z"/><path class="l" d="M0 40 L20 34 L40 36 L60 28 L80 30 L100 20 L120 24 L140 14 L160 16 L180 8 L200 6"/></svg>
        <div class="row-wrap mt-2"><span class="badge green">${icon("trending-up")}+18%</span><span class="xs faint">vs last month</span></div></div>
    </div></div>

    <div class="marquee mt-8" aria-label="Recent activity in Block C"><div class="marquee-t">${[...DB.feed, ...DB.feed].map(([u, v, o, x]) => `<span class="feed-chip">${av(u, "sm")}<span><b>${U(u).short}</b> ${v} <b>${o}</b> ${x}</span></span>`).join("")}</div></div>

    <section class="section" id="how"><div class="center rv"><span class="eyebrow">How it works</span><h2 style="font-size:clamp(1.8rem,3.6vw,2.6rem);letter-spacing:-0.04em;margin-top:8px">From request to return in four steps</h2></div>
      <div class="grid-4 mt-8" data-stagger>${[["map-pin-check", "green", "Join your mohalla", "Prove you live there with a one-time location check and an invitation. We keep the result, never the location."], ["hand", "saffron", "Ask to borrow", "Pick dates. The lender gets an evidence report, not a star rating."], ["camera", "sky", "Hand over with a checklist", "Both of you confirm the condition with photos. The loan starts only when both agree."], ["undo-2", "violet", "Return and close", "Compare with the handover record. Problems go to a neighbour-moderator, never to an algorithm."]].map(([ic, t, h, d], i) => `<div class="card spot hover"><div class="between">${tone(ic, t)}<span class="mono faint">0${i + 1}</span></div><h3 class="mt-4">${h}</h3><p class="small muted mt-2">${d}</p></div>`).join("")}</div></section>

    <section class="section"><div class="card card-pad-lg spot" style="padding:clamp(22px,4vw,44px)"><div class="two-col" style="grid-template-columns:1fr;align-items:center">
      <div class="grid-2" style="align-items:center;gap:36px">
        <div class="rv"><span class="eyebrow">${icon("chart-spline", "i-sm")}Evidence, not stars</span><h2 style="font-size:clamp(1.7rem,3.2vw,2.4rem);letter-spacing:-0.04em;margin-top:10px">See how sure we are, not just a number.</h2>
          <p class="muted mt-4">A star average hides how little we know about a new neighbour. Digital Mohalla shows the whole shape of the evidence: flat when there's no history, narrow when there's plenty. Unusual activity is checked separately, and uncertain cases go to a moderator.</p>
          <div class="mt-6">${seg([["new", "New neighbour"], ["some", "Some evidence"], ["lots", "Lots of evidence"]], 0)}</div></div>
        <div id="demo" class="card" style="box-shadow:var(--shadow-lg)"></div></div></div></div></section>

    <section class="section" id="modules"><div class="center rv"><span class="eyebrow">Everything your mohalla needs</span><h2 style="font-size:clamp(1.8rem,3.6vw,2.6rem);letter-spacing:-0.04em;margin-top:8px">One app for the whole neighbourhood</h2><p class="muted mt-3" style="max-width:56ch;margin-inline:auto">Lending, trust and moderation are live in this iteration. The rest of the platform is designed and arriving next.</p></div>
      <div class="bento mt-8" data-stagger>
        <a class="card spot hover b4" href="#/borrow" style="padding:0;overflow:hidden;min-height:260px">${photo(I("chairs").photo, { w: 1000, ratio: "auto", shade: true, alt: "", inner: "", bl: `<span class="badge green">${icon("circle-check")}Live</span><h3 style="font-size:1.5rem;margin-top:8px;color:#fff">Borrow and lend</h3><p style="opacity:.85;max-width:46ch">Search Block C, request dates and track every loan from handover to return.</p>` }).replace('aspect-ratio:auto', 'height:100%;aspect-ratio:auto')}</a>
        <a class="card spot hover b2" href="#/evidence">${tone("shield-check", "green")}<span class="badge green mt-4" style="margin-top:16px">Live</span><h3 class="mt-2">Trust and safety</h3><p class="small muted mt-2">Evidence reports, safeguards, reviews and disputes.</p></a>
        <a class="card spot hover b2" href="#/forum">${tone("messages-square", "violet")}<div class="mt-4">${soon()}</div><h3 class="mt-2">Community forum</h3><p class="small muted mt-2">Ask, recommend, find lost things. Best answers rise.</p></a>
        <a class="card spot hover b2" href="#/events">${tone("calendar-days", "sky")}<div class="mt-4">${soon()}</div><h3 class="mt-2">Events</h3><p class="small muted mt-2">Cleanups, workshops and celebrations with RSVP and QR check-in.</p></a>
        <a class="card spot hover b2" href="#/assistant">${tone("bot", "saffron")}<div class="mt-4">${soon()}</div><h3 class="mt-2">Mohalla assistant</h3><p class="small muted mt-2">Cited answers from community rules and posts, in English or Roman Urdu.</p></a>
        <a class="card spot hover b2" href="#/vendors">${tone("store", "coral")}<div class="mt-4">${soon()}</div><h3 class="mt-2">Local vendors</h3><p class="small muted mt-2">Verified tailors, electricians and tutors nearby.</p></a>
        <a class="card spot hover b2" href="#/kameti">${tone("piggy-bank", "green")}<div class="mt-4">${soon("Later")}</div><h3 class="mt-2">Kameti</h3><p class="small muted mt-2">Savings circles with a clear rotation. Record only, money never moves in the app.</p></a>
        <a class="card spot hover b4" href="#/insights"><div class="between">${tone("chart-no-axes-column", "sky")}${soon("Later")}</div><h3 class="mt-4">Neighbourhood insights</h3><p class="small muted mt-2" style="max-width:52ch">How responsive and active a community is, with weights you choose. Safety rankings are excluded on purpose.</p>
          <div class="bars mt-4">${[["Requests fulfilled", 82, "var(--primary)"], ["Forum answer rate", 74, "var(--violet)"], ["Event attendance", 68, "var(--sky)"]].map(([l, v, c]) => `<div class="br"><span class="small">${l}</span><span class="bt"><i style="width:${v}%;background:${c}"></i></span><b class="small">${v}%</b></div>`).join("")}</div></a>
        <a class="card spot hover b2" href="#/mod">${tone("gavel", "neutral")}<span class="badge green" style="margin-top:16px">Live</span><h3 class="mt-2">Moderation</h3><p class="small muted mt-2">Neighbour-moderators decide with the full evidence trail.</p></a>
      </div></section>

    <section class="section"><div class="grid-3" data-stagger>${[["eye-off", "Privacy first", "We store whether you're in the boundary, never where you are. Exact meeting spots are shared only after both people agree."], ["users-round", "People decide", "Machines flag, neighbours decide. Restricting anyone always needs a moderator's written reason."], ["scroll-text", "Every step recorded", "Each change is an append-only event, so disputes are settled on facts, not memory."]].map(([ic, h, d]) => `<div class="card spot">${tone(ic, "neutral")}<h3 class="mt-4">${h}</h3><p class="small muted mt-2">${d}</p></div>`).join("")}</div></section>

    <section class="section"><div class="card center rv" style="padding:clamp(32px,6vw,64px);background:var(--text);color:var(--bg);border:0">
      <h2 style="font-size:clamp(1.8rem,4vw,2.8rem);letter-spacing:-0.045em">Your neighbours already have what you need.</h2>
      <p style="opacity:.7;margin-top:12px">Join Block C in about two minutes.</p>
      <div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary btn-lg" href="#/register">Get started</a><a class="btn btn-lg" href="#/login" style="border:1px solid rgba(127,127,127,.4)">Log in</a></div></div></section>
    <footer class="footer"><div class="between" style="flex-wrap:wrap"><span class="row">${logo("i-lg")} Digital Mohalla · FYP 2026 · prototype with synthetic data</span><span class="row-wrap"><a href="#/hci">Design notes</a> · <a href="#/mod">Moderator console</a> · <a href="#/admin">Admin</a></span></div></footer>
  </div>`,
  after() {
    const draw = k => { const x = DEMO[k]; $("#demo").innerHTML = `${stateChip(x.state)}<h3 class="mt-4">${x.t}</h3><p class="small muted mt-1">${x.d}</p>${betaCurve(x.ab[0], x.ab[1], x.state).replace('class="curve"', 'class="curve" style="padding:8px 0 0"')}`; refreshIcons(); };
    draw("new");
    $(".seg").addEventListener("click", e => { const b = e.target.closest("[data-v]"); if (b) draw(b.dataset.v); });
    $$("[data-scroll]").forEach(a => a.onclick = e => { e.preventDefault(); $("#" + a.dataset.scroll).scrollIntoView({ behavior: "smooth" }); });
  }
}));

const authShell = (inner, quote = "We lent our deg for three weddings this season, and every time I could see exactly who was asking.", who = "u2", ph = "photo-1621801306185-8c0ccf9c8eb8") =>
  `<div class="auth"><div class="auth-l"><div class="between"><a class="brand" href="#/welcome">${logo()}Digital Mohalla</a><button class="icon-btn" type="button" data-act="theme" aria-label="Toggle dark mode"><span data-theme-icon></span></button></div><div class="inner">${inner}</div></div>
   <div class="auth-r"><img src="${img(ph, 1400)}" alt=""><div class="glass"><p>“${quote}”</p><div class="row mt-4">${av(who, "sm")}<span class="small">${U(who).name} · ${U(who).lane}, Block C</span></div></div></div></div>`;

route("/register", () => ({
  bare: true, title: "Create account",
  html: authShell(`<div class="rv"><span class="eyebrow">Step 1 of 2</span><h1 class="mt-2">Create your account</h1><p class="muted mt-2">You'll join your mohalla right after.</p></div>
    <form id="reg" class="mt-8 rv" style="--d:1" novalidate>
      <div class="field"><label class="label" for="nm">Full name</label><input class="input" id="nm" autocomplete="name" maxlength="200" value="Sana Malik"></div>
      <div class="field"><label class="label" for="em">Email</label><input class="input" id="em" type="email" autocomplete="email" placeholder="you@example.com"></div>
      <div class="field"><label class="label" for="pw">Password</label><div class="input-wrap"><input class="input" id="pw" type="password" autocomplete="new-password" style="padding-right:70px"><button class="btn btn-ghost btn-sm addon" type="button" id="show">Show</button></div>${stepper(0, 4)}<span class="help" id="pwh">At least 8 characters.</span></div>
      <label class="check mt-2"><input type="checkbox" id="tos"><span><span>I agree to the <a class="link" href="#/register">community terms</a> and <a class="link" href="#/register">privacy notice</a>. My exact address is never stored.</span></span></label>
      <div id="rerr" aria-live="polite"></div>
      <button class="btn btn-primary btn-lg btn-block mt-4" type="submit">Create account</button>
      <p class="xs faint mt-4">${icon("smartphone", "i-sm")} Email and phone confirmation (one-time codes) arrive in iteration 3.</p>
      <p class="small muted mt-6 center">Already a member? <a class="link" href="#/login">Log in</a></p></form>`),
  after() {
    $("#show").onclick = e => { const p = $("#pw"); p.type = p.type === "password" ? "text" : "password"; e.target.textContent = p.type === "password" ? "Show" : "Hide"; };
    $("#pw").oninput = e => { const n = Math.min(4, Math.floor(e.target.value.length / 3)); $$("#reg .stepper i").forEach((s, i) => (s.className = i < n ? "on" : "")); $("#pwh").textContent = ["At least 8 characters.", "Keep going.", "Almost there.", "Good.", "Strong password."][n]; };
    $("#reg").onsubmit = e => {
      e.preventDefault(); const errs = [];
      if (!/.+@.+\..+/.test($("#em").value)) errs.push(["em", "Enter an email like name@example.com."]);
      if ($("#pw").value.length < 8) errs.push(["pw", "Use at least 8 characters."]);
      if (!$("#tos").checked) errs.push(["tos", "Accept the terms to continue."]);
      $$("[aria-invalid]").forEach(x => x.removeAttribute("aria-invalid"));
      if (errs.length) { errs.forEach(([id]) => $("#" + id).setAttribute("aria-invalid", "true")); $("#rerr").innerHTML = errs.map(x => `<p class="err">${icon("circle-alert")}${x[1]}</p>`).join(""); refreshIcons(); $("#" + errs[0][0]).focus(); return; }
      location.hash = "#/verify-email";
    };
  }
}));

route("/verify-email", () => ({
  bare: true, title: "Account created",
  html: authShell(`${done("Check your e-mail to finish creating your account.", "We give the same reply whether or not the address already has an account, so nobody can find out who is registered.")}
    <div class="card card-2 row mt-6" style="align-items:flex-start">${tone("flask-conical", "sky", 34)}<p class="small">In this iteration you can sign in straight away. Confirming your e-mail with a one-time code arrives in iteration 3.</p></div>
    <div class="stack mt-6"><a class="btn btn-primary btn-lg btn-block" href="#/login">Sign in</a></div>`)
}));

route("/login", () => ({
  bare: true, title: "Log in",
  html: authShell(`<div class="rv"><h1>Welcome back</h1><p class="muted mt-2">4 things are waiting for you in Block C.</p></div>
    <form id="lg" class="mt-8 rv" style="--d:1" novalidate>
      <div class="field"><label class="label" for="le">Email</label><input class="input" id="le" autocomplete="username" value="sana.malik@example.com"></div>
      <div class="field"><div class="between"><label class="label" for="lp">Password</label><a class="link xs" href="#/login">Forgot?</a></div><input class="input" id="lp" type="password" autocomplete="current-password" value="password1"></div>
      <div id="lerr" aria-live="polite"></div>
      <button class="btn btn-primary btn-lg btn-block mt-6" type="submit">Log in</button></form>
    <div class="divider mt-8"></div><p class="xs faint">Demo</p>
    <div class="btns mt-2"><a class="btn btn-outline btn-sm" href="#/home">${icon("house")}Resident</a><a class="btn btn-outline btn-sm" href="#/mod">${icon("shield-check")}Moderator</a><a class="btn btn-outline btn-sm" href="#/admin">${icon("layout-dashboard")}Admin</a></div>
    <div class="btns mt-2"><button class="btn btn-ghost btn-sm" type="button" id="bad">Wrong password state</button><button class="btn btn-ghost btn-sm" type="button" id="sus">Suspended account state</button></div>`, "The moderator asked both of us for photos and decided in a day. Fair, and nobody had to shout on WhatsApp.", "u6", "photo-1667650708785-2179a8eb2b70"),
  after() {
    $("#lg").onsubmit = e => { e.preventDefault(); location.hash = "#/join"; };
    $("#bad").onclick = () => { $("#lerr").innerHTML = `<p class="err">${icon("circle-alert")}That email and password don't match.</p>`; $("#lp").setAttribute("aria-invalid", "true"); refreshIcons(); };
    $("#sus").onclick = () => { $("#lerr").innerHTML = `<div class="card card-2 mt-4"><div class="row">${tone("shield-alert", "coral")}<div><b>This account is suspended</b><p class="small muted">Reason: repeated no-shows (3 in 30 days). Your active loans continue with a moderator's help.</p></div></div><a class="btn btn-outline btn-sm mt-4" href="#/login">Appeal this decision</a></div>`; refreshIcons(); };
  }
}));

/* ---- W9: find a community (GET /communities: member_count, join_code, methods, has_boundary, your status) ---- */
const commBadge = c => ({ APPROVED: `<span class="badge green">${icon("check")}Member</span>`, PENDING: `<span class="badge saffron">${icon("hourglass")}Pending</span>`, REJECTED: `<span class="badge">${icon("rotate-ccw")}Not approved</span>` })[c.mine] || "";
const methodText = c => c.methods.includes("GEOFENCE_INVITATION") && c.has_boundary ? "Location check + invitation, or a moderator decides" : "A moderator approves every request";
route("/join", () => ({
  title: "Join a community", nav: "community",
  html: `<div class="wrap wrap-md">${pageHead({ back: ["#/home", "Home"], eyebrow: `${icon("map-pin", "i-sm")}Step 1 of 3`, title: "Find your mohalla", sub: "Search by name, or the code a neighbour gave you." })}
    <div class="input-wrap rv">${icon("search")}<input class="input" id="cq" style="height:52px;border-radius:14px" placeholder="e.g. Gulberg or GUL-C" aria-label="Search communities"></div>
    <div class="grid-2 mt-6" id="clist" data-stagger>${DB.communities.map(c => `<a class="card hover" href="#/join/${c.id}" data-n="${(c.name + " " + c.join_code).toLowerCase()}" style="padding:0;overflow:hidden">${photo(c.photo, { w: 700, ratio: "16/8", alt: "", tl: commBadge(c) })}<div style="padding:16px"><div class="between"><h3>${c.name}</h3>${icon("arrow-up-right", "i faint")}</div><p class="small muted mt-1">${c.city} · ${c.member_count} members · code ${c.join_code}</p><p class="xs faint mt-2">${icon("shield-check", "i-sm")} ${methodText(c)}</p></div></a>`).join("")}</div>
    <div id="cempty" hidden>${empty("map-pin-off", "neutral", "No community by that name", "Check the spelling, or ask a neighbour for their community code. Codes look like GUL-C.")}</div></div>`,
  after() { $("#cq").oninput = e => { const q = e.target.value.toLowerCase().trim(); let n = 0; $$("#clist > a").forEach(a => { const h = !q || a.dataset.n.includes(q); a.hidden = !h; n += h; }); $("#cempty").hidden = n > 0; }; }
}));

route("/join/:id", ({ id }) => {
  const c = DB.communities.find(x => x.id === id) || DB.communities[0];
  if (c.mine === "PENDING") return { title: c.name, nav: "community", html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/join", "Communities"], title: c.name })}${empty("hourglass", "saffron", "You've already asked to join", "Your request is with a moderator. Only one open request per community is allowed, so sending another wouldn't speed it up.")}<div class="card">${timeline([{ s: "done", t: "Request sent", d: "9 Oct" }, { s: "now", t: "Moderator review", d: "A person decides when the location result is unclear" }, { s: "todo", t: "Decision", d: "You'll get a notification" }])}</div></div>` };
  return {
    title: c.name, nav: "community",
    html: `<div class="wrap wrap-md">${pageHead({ back: ["#/join", "Communities"], eyebrow: `${icon("map-pin", "i-sm")}Step 2 of 3`, title: c.name, sub: `${c.city} · ${c.member_count} members · moderated by Imran Q. and Rabia S.` })}
      ${c.mine === "REJECTED" ? `<div class="card card-2 row rv" style="align-items:flex-start;margin-bottom:16px">${tone("rotate-ccw", "neutral", 36)}<div><b class="small">Your last request wasn't approved</b><p class="small muted">The moderator's reason: “We couldn't confirm you live in Block K. Ask a neighbour there for an invitation.” You can apply again.</p></div></div>` : ""}
      <div class="rv">${photo(c.photo, { w: 1400, ratio: "21/8", alt: c.name, cls: "", eager: true })}</div>
      <div class="row mt-4 rv"><span class="avs">${["u2", "u5", "u6", "u3", "u7"].map(u => av(u, "sm")).join("")}</span><span class="small muted">Bilal, Kamran and 212 neighbours</span></div>
      <div class="grid-2 mt-8"><div><h2 class="sec-title">House rules</h2><div class="list" data-stagger>${DB.community.rules.map((r, i) => `<div class="li">${tone(["map-pinned", "handshake", "banknote", "message-circle-heart"][i], ["green", "sky", "saffron", "violet"][i], 36)}<span class="small">${r}</span></div>`).join("")}</div></div>
        <div><h2 class="sec-title">How you'll prove you live here</h2><div class="stack" data-stagger>${c.has_boundary ? `<div class="card">${tone("locate-fixed", "green")}<h3 class="mt-3">One-time location check</h3><p class="small muted mt-1">Your phone's position is checked against the boundary once, then dropped. Only the result is kept.</p></div>` : `<div class="card">${tone("map-off", "neutral")}<h3 class="mt-3">No boundary set</h3><p class="small muted mt-1">This community hasn't drawn a boundary, so a moderator reviews every request.</p></div>`}
          <div class="card">${tone("ticket", "saffron")}<h3 class="mt-3">Invitation code</h3><p class="small muted mt-1">Single-use, from an approved member of ${c.name}.</p></div>
          <p class="small muted">${icon("shield-check", "i-sm")} Both together let you in. If either is missing or unclear, a moderator decides. Nobody is rejected automatically.</p></div></div></div>
      <div class="dock"><div class="card between"><label class="check" style="padding:0"><input type="checkbox" checked><span><span>I'll follow the house rules</span></span></label><a class="btn btn-primary" href="#/join/${c.id}/verify">Continue ${icon("arrow-right")}</a></div></div></div>`
  };
});

/* ---- W10: location + invitation (POST /communities/{id}/join -> JoinOut { status, locality: LocalityOut }) ----
   VERIFIED needs INSIDE + a valid invitation; a missing signal is INCONCLUSIVE; OUTSIDE, a mock
   location app or a suspected duplicate is CONFLICTING. The fix is used once in memory, never stored. */
route("/join/:id/verify", ({ id }) => ({
  title: "Prove you live here", nav: "community",
  html: `<div class="wrap wrap-sm">${pageHead({ back: ["#/join/" + id, "Rules"], eyebrow: `${icon("map-pin", "i-sm")}Step 3 of 3`, title: "Prove you live here", sub: "Two quick checks. We keep only the results." })}
    <div class="card card-pad-lg center rv"><div class="radar" id="radar">${icon("locate-fixed")}</div><h2 class="mt-6" id="lh">One-time location check</h2><p class="muted small mt-2" id="lp" style="max-width:42ch;margin-inline:auto">Your phone shares its position once. It's compared with the boundary and dropped. We keep only inside, near the edge, outside or not shared.</p>
      <div class="btns mt-6" id="lb" style="justify-content:center"><button class="btn btn-primary" type="button" id="allow">${icon("locate-fixed")}Allow once</button><button class="btn btn-outline" type="button" id="skip">Don't share</button></div>
      <p class="xs faint mt-4">Prototype: <button class="link" type="button" id="out">simulate “outside the boundary”</button></p></div>
    <div class="card mt-4 rv"><div class="row">${tone("ticket", "saffron")}<div><h3>Invitation code</h3><p class="small muted">From an approved member. Optional, but it helps.</p></div></div>
      <div class="field mt-4"><input class="input mono" id="inv" value="GUL-C-7K2Q" maxlength="32" style="font-size:17px;letter-spacing:.08em;height:52px" aria-label="Invitation code"><span class="help" id="ih">Checked when you send the request.</span></div>
      <p class="xs faint">Prototype: <button class="link" type="button" id="badinv">simulate an invalid code</button></p></div>
    <div class="dock"><div class="card"><a class="btn btn-primary btn-block" id="go" href="#/join/${id}/result/VERIFIED" aria-disabled="true">Send join request</a></div></div></div>`,
  after() {
    const go = $("#go"); let sig = null;
    const set = () => { const code = $("#inv").value.trim(); const r = sig === "OUTSIDE" ? "CONFLICTING" : sig === "INSIDE" && code ? "VERIFIED" : "INCONCLUSIVE"; go.href = `#/join/${id}/result/${r}`; go.removeAttribute("aria-disabled"); };
    $("#allow").onclick = () => { $("#radar").classList.add("on"); $("#lh").textContent = "Checking…"; $("#lb").hidden = true;
      setTimeout(() => { $("#radar").className = "radar ok"; $("#radar").innerHTML = icon("map-pin-check"); refreshIcons(); $("#lh").textContent = "Inside the boundary"; $("#lp").textContent = "Done. Your position was used once and dropped."; sig = "INSIDE"; set(); }, 1800); };
    $("#skip").onclick = () => { $("#lh").textContent = "Not shared, and that's fine"; $("#lp").textContent = "A moderator will look at your request instead. Not sharing never counts against you."; $("#lb").hidden = true; sig = "UNAVAILABLE"; set(); };
    $("#out").onclick = () => { $("#lh").textContent = "Outside the boundary"; $("#lp").textContent = "That can happen near the edge or with weak GPS. A moderator decides; nothing is rejected automatically."; $("#lb").hidden = true; $("#radar").className = "radar"; $("#radar").innerHTML = icon("map-pin-off"); refreshIcons(); sig = "OUTSIDE"; set(); };
    go.onclick = e => { if (go.getAttribute("aria-disabled")) { e.preventDefault(); toast("Allow the location check, or choose not to share it, first.", { ic: "info" }); } };
    $("#inv").oninput = () => { $("#inv").removeAttribute("aria-invalid"); $("#ih").outerHTML = `<span class="help" id="ih">Checked when you send the request.</span>`; if (sig) set(); };
    $("#badinv").onclick = () => { $("#inv").setAttribute("aria-invalid", "true"); $("#ih").outerHTML = `<p class="err" id="ih">${icon("circle-alert")}This invitation code is not valid: retry or continue without.</p>`; refreshIcons(); };
  }
}));
const LOCALITY_WORDS = { VERIFIED: "Your location check and invitation agree.", INCONCLUSIVE: "We could not confirm your location yet. A moderator will look at your request. This is not a negative finding.", CONFLICTING: "Some signals did not match. A moderator will review your request; nothing has been rejected." };
route("/join/:id/result/:r", ({ r }) => {
  r = (r || "").toUpperCase(); if (!LOCALITY_WORDS[r]) r = "INCONCLUSIVE";
  const steps = { VERIFIED: [{ s: "done", t: "Inside the boundary" }, { s: "done", t: "Invitation accepted" }, { s: "now", t: "Moderator approval", d: "Status PENDING. Open communities approve this automatically" }],
    INCONCLUSIVE: [{ s: "now", t: "Location not confirmed", d: "A person decides instead" }, { s: "done", t: "Request saved", d: "Status PENDING" }, { s: "todo", t: "Moderator decision", d: "They may ask you one question" }],
    CONFLICTING: [{ s: "now", t: "Some signals didn't match", d: "Sent to a person" }, { s: "done", t: "Request saved", d: "Status PENDING" }, { s: "todo", t: "Moderator decision" }] }[r];
  return { title: "Join request", nav: "community", html: `<div class="wrap wrap-sm">${r === "VERIFIED" ? done("Request sent to Block C", LOCALITY_WORDS[r]) : empty("user-search", "saffron", "A moderator will take a look", LOCALITY_WORDS[r])}<div class="card mt-4">${timeline(steps)}</div><p class="xs faint center mt-4">Outcome <span class="mono">${r}</span> · only this result is stored, never your position.</p><div class="btns mt-6" style="justify-content:center"><a class="btn btn-primary" href="#/home/new">Look around while you wait</a></div></div>` };
});

screens("Website and onboarding · Module 1", [["Landing website", "#/welcome"], ["Register (W8)", "#/register", "POST /auth/register"], ["Account created (generic reply)", "#/verify-email", "202"], ["Log in + error + suspended", "#/login", "FR-A-04/05"], ["Find a community (W9)", "#/join", "GET /communities"], ["Rules and methods (W9)", "#/join/c1"], ["Duplicate request blocked", "#/join/c2", "FR-A-09"], ["Apply again after rejection", "#/join/c4", "REJECTED"], ["No boundary: moderator only", "#/join/c3", "has_boundary"], ["Location + invitation (W10)", "#/join/c1/verify", "POST /join"], ["Result: verified", "#/join/c1/result/VERIFIED", "LocalityOut"], ["Result: inconclusive", "#/join/c1/result/INCONCLUSIVE", "ES-10"], ["Result: conflicting", "#/join/c1/result/CONFLICTING", "ES-09"]]);
