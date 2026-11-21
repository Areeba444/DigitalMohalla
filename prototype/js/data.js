/* Mock data shaped like the Digital Mohalla backend.
   Lifecycle states, assurance output (with recency-weighted Beta posterior parameters),
   hold reasons and event types follow the FR/NFR and use-case baselines.
   Photos are Unsplash (free licence), loaded by id. */

const IMG = (id, w = 800, h) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${w}${h ? "&h=" + h : ""}&q=72`;

window.DB = {
  img: IMG,
  me: "u0",
  community: { id: "c1", name: "Block C, Gulberg III", short: "Block C", city: "Lahore", members: 214, mods: ["mod", "mod2"],
    rules: ["Lend and borrow only inside Block C and the two lanes next to it.", "Hand over in a public spot: the park gate or the masjid parking.", "Record deposits in the app. Money never moves through Digital Mohalla.", "In reviews and posts, describe what happened, not the person."] },
  communities: [
    { id: "c1", name: "Block C, Gulberg III", city: "Lahore", members: 214, code: "GUL-C", photo: "photo-1684323041566-1958d8056e8a", method: "Location check + invitation", state: "member" },
    { id: "c2", name: "Main Market Lanes", city: "Lahore", members: 132, code: "MML", photo: "photo-1667650708785-2179a8eb2b70", method: "Location check + invitation", state: "pending" },
    { id: "c3", name: "Liberty Residency", city: "Lahore", members: 88, code: "LRT", photo: "photo-1655449767937-754b25282108", method: "Open to verified residents", state: "open", open: true },
    { id: "c4", name: "Model Town Block K", city: "Lahore", members: 301, code: "MTK", photo: "photo-1601969700719-d31890dd6b30", method: "Location check + invitation", state: "full" }
  ],
  users: {
    u0: { name: "Sana Malik", short: "Sana", initials: "SM", photo: "photo-1550546094-9835463f9f71", since: "Mar 2026", lane: "Lane 3" },
    u1: { name: "Ayesha Khan", short: "Ayesha", initials: "AK", photo: "photo-1536766768598-e09213fdcf22", since: "Oct 2026", lane: "Lane 4" },
    u2: { name: "Bilal Raza", short: "Bilal", initials: "BR", photo: "photo-1621960883434-e910537c8052", since: "Jan 2026", lane: "Lane 2", badge: "Trusted lender" },
    u3: { name: "Usman Tariq", short: "Usman", initials: "UT", photo: "photo-1711374316403-2bfa31ae9c2a", since: "Jun 2026", lane: "Lane 7" },
    u4: { name: "Hira Aslam", short: "Hira", initials: "HA", since: "Feb 2026", lane: "Lane 1", badge: "Event organizer" },
    u5: { name: "Kamran Javed", short: "Kamran", initials: "KJ", photo: "photo-1618306842557-a2515acf2112", since: "Nov 2025", lane: "Lane 5", badge: "Top answerer" },
    u6: { name: "Nadia Pervez", short: "Nadia", initials: "NP", photo: "photo-1516239482977-b550ba7253f2", since: "Aug 2026", lane: "Lane 3" },
    u7: { name: "Farah Siddiqui", short: "Farah", initials: "FS", photo: "photo-1552113125-81af17f36b57", since: "Apr 2026", lane: "Lane 6", badge: "Verified expert" },
    mod: { name: "Imran Qureshi", short: "Imran", initials: "IQ", photo: "photo-1617817638453-4480d05e0b83", role: "Moderator" },
    mod2: { name: "Rabia Saeed", short: "Rabia", initials: "RS", role: "Moderator" },
    admin: { name: "Saad Ahmed", short: "Saad", initials: "SA", role: "Admin" }
  },
  categories: [
    { id: "all", label: "All", icon: "layout-grid" }, { id: "tools", label: "Tools & DIY", icon: "hammer" }, { id: "party", label: "Party & events", icon: "party-popper" },
    { id: "kitchen", label: "Kitchen", icon: "cooking-pot" }, { id: "kids", label: "Baby & kids", icon: "baby" }, { id: "outdoor", label: "Outdoor & sports", icon: "tent" },
    { id: "electronics", label: "Electronics", icon: "projector" }, { id: "books", label: "Books", icon: "book-open" }, { id: "medical", label: "Medical", icon: "accessibility" }
  ],
  items: [
    { id: "makita", title: "Cordless drill, 2 batteries", noun: "drill", cat: "tools", photo: "photo-1572981779307-38b8cabb2407", lender: "u5", deposit: 3000, cond: "Very good", lane: "Lane 5", avail: "Free from 14 Oct", max: "4 days", handover: "From the lender's gate", desc: "18V cordless drill-driver with two batteries, a charger and a case of wood and metal bits.", terms: ["Rs 3,000 deposit, recorded in the app", "Charge the batteries before returning"], why: "Matches “drill” · 11 completed tool loans · free on your dates", score: 0.91 },
    { id: "deg", title: "Large deg for 40 guests", noun: "deg", cat: "kitchen", photo: "photo-1790008882050-76a602990485", lender: "u2", deposit: 1500, cond: "Very good", lane: "Lane 2", avail: "Free this weekend", max: "2 days", handover: "Masjid parking", desc: "Aluminium deg with lid and a long kafgeer. Enough biryani or haleem for about 40 people.", terms: ["Rs 1,500 deposit", "Return scrubbed, no burnt base"], why: "Popular for weddings · Bilal has lent it 9 times", trend: "Booked 9× this season" },
    { id: "chairs", title: "Plastic chairs, set of 20", noun: "chairs", cat: "party", photo: "photo-1778230501599-90003014460d", lender: "u4", deposit: 3000, cond: "Good · 2 scratched", lane: "Lane 1", avail: "Booked 18–19 Oct", max: "3 days", handover: "Park gate", desc: "Stackable plastic chairs in two bundles of ten. You'll need a car or a rickshaw.", terms: ["Rs 3,000 deposit", "Count all 20 at handover and return"], why: "Some dates already booked", trend: "Wedding season favourite" },
    { id: "ladder", title: "Aluminium ladder, 8 ft", noun: "ladder", cat: "tools", photo: "photo-1617515457325-728e2a50cd87", lender: "u5", deposit: 0, cond: "Good", lane: "Lane 5", avail: "Available now", max: "2 days", handover: "From the lender's gate", desc: "Folding A-frame ladder that holds up to 120 kg. New rubber feet this year.", terms: ["No deposit", "Not for wet floors"], why: "Close by and free today" },
    { id: "tent", title: "4-person camping tent", noun: "tent", cat: "outdoor", photo: "photo-1504280390367-361c6d9f38f4", lender: "u2", deposit: 2500, cond: "Very good", lane: "Lane 2", avail: "Available now", max: "5 days", handover: "From the lender's gate", desc: "Dome tent with rain fly, pegs and carry bag. Used twice in Naran.", terms: ["Rs 2,500 deposit", "Dry it before returning"], why: "14 completed loans", trend: "Northern trips" },
    { id: "projector", title: "Projector + 100-inch screen", noun: "projector", cat: "electronics", photo: "photo-1535016120720-40c646be5580", lender: "u3", deposit: 8000, cond: "Good", lane: "Lane 7", avail: "Free from 20 Oct", max: "2 days", handover: "Park gate", restricted: true, desc: "1080p projector, pull-up screen and HDMI cable. Match nights and mehndi slideshows.", terms: ["Rs 8,000 deposit", "Verified accounts only (high value)"], why: "High value · lender reviews every request", trend: "Match nights" },
    { id: "wheelchair", title: "Folding wheelchair", noun: "wheelchair", cat: "medical", photo: "photo-1619618691037-751d1e6c9ad1", lender: "u6", deposit: 5000, cond: "Very good", lane: "Lane 3", avail: "Available now", max: "14 days", handover: "From the lender's gate", restricted: true, desc: "Lightweight folding wheelchair with footrests. For neighbours after surgery or elderly visitors.", terms: ["Rs 5,000 deposit", "Verified accounts only (medical)"], why: "Medical items need a verified account" },
    { id: "stroller", title: "Reclining baby stroller", noun: "stroller", cat: "kids", photo: "photo-1559135141-2bea6465fccf", lender: "u1", deposit: 1000, cond: "Good", lane: "Lane 4", avail: "Available now", max: "7 days", handover: "From the lender's gate", desc: "Reclining stroller with rain cover; folds one-handed.", terms: ["Rs 1,000 deposit"], why: "New lender, no loans yet" },
    { id: "books", title: "O-level Physics books", noun: "books", cat: "books", photo: "photo-1497633762265-9d179a990aa6", lender: "u5", deposit: 0, cond: "Some highlighting", lane: "Lane 5", avail: "Available now", max: "4 months", handover: "From the lender's gate", desc: "Textbook plus two years of solved past papers.", terms: ["No deposit", "Up to one term"], why: "Matches “books”" },
    { id: "drill", title: "Bosch impact drill + bits", noun: "drill", cat: "tools", photo: "photo-1622044939413-0b829c342434", lender: "u0", deposit: 2000, cond: "Good", lane: "Lane 3", avail: "Free from 14 Oct", max: "3 days", handover: "From your gate", desc: "650W impact drill with a 13-piece bit set and a spare chuck key.", terms: ["Rs 2,000 deposit", "Masonry bits only for brick and concrete"], why: "" }
  ],
  /* Lender history summaries for item pages (FR-S-04): words + range, never a number */
  lenderEv: {
    u0: { state: "review", tag: "Small history", line: "3 loans as a lender, all returned as agreed.", ab: [4, 2] },
    u1: { state: "insufficient", tag: "New lender", line: "New to Block C. No loans as a lender yet.", ab: [1, 1] },
    u2: { state: "sufficient", tag: "Established lender", line: "14 loans as a lender, all completed. No condition disputes.", ab: [15, 1.6] },
    u3: { state: "review", tag: "Small history", line: "5 loans as a lender. One condition dispute in July, resolved.", ab: [5, 2] },
    u4: { state: "sufficient", tag: "Established lender", line: "9 loans. One dispute open now, not counted until resolved.", ab: [9, 1.8] },
    u5: { state: "sufficient", tag: "Established lender", line: "11 loans, 10 handed over on time. Mostly tools.", ab: [11, 2] },
    u6: { state: "review", tag: "Small history", line: "3 loans as a lender, all completed.", ab: [4, 1.6] }
  },
  /* Incoming borrow requests for the lender (W1, W2). ab = recency-weighted Beta posterior (alpha, beta). */
  requests: {
    r1: { id: "r1", item: "drill", borrower: "u1", dates: [14, 16], msg: "Need it to put up shelves in my daughter's room. I'll pick it up after Asr.", expires: 40, overlap: { who: "Hamza A.", dates: "15–17 Oct" },
      a: { state: "insufficient", code: "INSUFFICIENT_EVIDENCE", title: "Not enough history yet", ab: [1, 1], conf: "Low",
        lede: "Ayesha joined Block C in October and hasn't completed a loan yet, as a borrower or a lender.",
        direct: ["No completed loans yet", "Nothing to count yet. That isn't a negative result."], indirect: ["No community paths", "Nobody you've lent to has lent to Ayesha."], risk: ["Nothing unusual", "Checked separately: reciprocal ratings, review text, retaliation."],
        safeguards: [["Record the Rs 2,000 deposit", "Logged at handover. No money moves in the app.", 1], ["Take handover photos", "The drill and the bit case.", 1], ["Fix the return date", "16 Oct, 8 pm. Extensions need your OK.", 1]],
        tech: { "Interval (90%)": "0.05 – 0.95 · Beta(1,1) prior", "k-hop paths": "k ≤ 3 · none found", "Manipulation risk": "8 / 100 · level 0", "Policy rule": "R2 · no history", "Config": "assurance-cfg v1.3" } } },
    r2: { id: "r2", item: "deg", borrower: "u6", dates: [20, 21], msg: "Mehndi at our house on Saturday, cooking for 35.", expires: 300,
      a: { state: "review", code: "REVIEW_RECOMMENDED", title: "Review recommended", ab: [4.2, 2.1], conf: "Low–medium",
        lede: "Nadia has no loans of her own yet, but two neighbours in your circle have lent to her without any problems.",
        direct: ["No completed loans yet", "Joined Block C in August."], indirect: ["2 community paths", "Capped below direct evidence, so it can't reach “enough evidence” on its own."], paths: true, risk: ["Nothing unusual", "Checked separately from trust."],
        safeguards: [["Record the Rs 1,500 deposit", "Logged at handover.", 1], ["Take handover photos", "The base and the lid.", 1], ["Fix the return date", "21 Oct, 9 pm.", 0]],
        tech: { "Interval (90%)": "0.34 – 0.88", "k-hop paths": "2 paths · ρ = 0.41 ≥ ρ_sup 0.30", "Manipulation risk": "4 / 100 · level 0", "Policy rule": "R6 · paths lift sparse evidence (ADR-0008)", "Config": "assurance-cfg v1.3" } } },
    r3: { id: "r3", item: "tent", borrower: "u5", dates: [24, 27], msg: "Family trip to Murree. We'll dry it properly before returning.", expires: 900,
      a: { state: "sufficient", code: "SUFFICIENT_EVIDENCE", title: "Enough evidence", ab: [16, 1.8], conf: "High",
        lede: "Kamran has borrowed 11 times in Block C, 10 on time, all returned as agreed. Most were outdoor and tool items like this one.",
        direct: ["11 completed loans · 10 on time", "Recent, similar loans weigh most."], indirect: ["Not needed", "Direct evidence is strong."], risk: ["Nothing unusual", "Checked separately from trust."],
        safeguards: [["Record the Rs 2,500 deposit", "Standard for this item.", 1]],
        tech: { "Interval (90%)": "0.78 – 0.97", "k-hop paths": "not used", "Manipulation risk": "3 / 100 · level 0", "Policy rule": "R8 · strong similar evidence", "Config": "assurance-cfg v1.3" } } }
  },
  /* Sana's loans; col = activity board column */
  loans: [
    { id: "b6", item: "drill", role: "lender", other: "u1", state: "ASSESSED", col: "action", label: "Decide on request", tone: "saffron", next: "Accept, decline or suggest dates", mins: 40, href: "#/requests/r1", step: 0, dates: "14–16 Oct" },
    { id: "b1", item: "deg", role: "borrower", other: "u2", state: "ACCEPTED", col: "action", label: "Handover today", tone: "saffron", next: "Confirm at 5 pm, masjid parking", mins: 135, href: "#/handover/b1/borrower", step: 2, dates: "18–19 Oct", due: "19 Oct, 9 pm" },
    { id: "b5", item: "chairs", role: "borrower", other: "u4", state: "DISPUTED", col: "action", label: "Moderator asked you", tone: "coral", next: "Reply to Imran by 6 pm", mins: 290, href: "#/case/b5", step: 4, dates: "1–3 Oct" },
    { id: "b3", item: "drill", role: "lender", other: "u3", state: "RETURN_INITIATED", col: "action", label: "Inspect the return", tone: "sky", next: "Compare with handover photos", href: "#/inspect/b3", step: 4, dates: "9–11 Oct" },
    { id: "b9", item: "projector", role: "borrower", other: "u3", state: "ASSESSED", col: "waiting", label: "New dates suggested", tone: "sky", next: "Usman suggests 21–22 Oct", mins: 600, href: "#/counter/b9", step: 0, dates: "20–21 Oct" },
    { id: "b2", item: "ladder", role: "borrower", other: "u5", state: "ACTIVE", col: "active", label: "Due tomorrow", tone: "green", next: "Return by 15 Oct, 8 pm", mins: 1560, href: "#/loan/b2", step: 3, dates: "13–15 Oct", due: "15 Oct, 8 pm" },
    { id: "b7", item: "books", role: "borrower", other: "u5", state: "ACTIVE", col: "active", label: "Overdue 1 day", tone: "coral", next: "Auto-dispute 14 Oct, 8 pm", mins: 1320, href: "#/loan/b7", step: 3, dates: "1–12 Oct", due: "12 Oct, 8 pm", overdue: true },
    { id: "b10", item: "tent", role: "lender", other: "u5", state: "ACTIVE", col: "action", label: "Wants 2 more days", tone: "sky", next: "Approve or keep 27 Oct", href: "#/extend-respond/b10", step: 3, dates: "24–27 Oct" },
    { id: "b4", item: "tent", role: "borrower", other: "u2", state: "COMPLETED", col: "done", label: "Leave a review", tone: "green", next: "Reviews close in 5 days", href: "#/review/b4", step: 5, dates: "28 Sep–2 Oct" },
    { id: "b11", item: "chairs", role: "borrower", other: "u4", state: "COMPLETED", col: "done", label: "Decision made", tone: "violet", next: "You can appeal for 5 days", href: "#/decision/b11", step: 5, dates: "5–6 Sep" },
    { id: "b8", item: "stroller", role: "borrower", other: "u1", state: "EXPIRED", col: "done", label: "Expired", tone: "neutral", next: "Ayesha didn't reply in 48 h", href: "#/item/stroller", step: -1, dates: "7–9 Oct" },
    { id: "b12", item: "makita", role: "borrower", other: "u5", state: "NO_SHOW", col: "done", label: "No-show", tone: "neutral", next: "Handover missed · dates released", href: "#/loan/b12", step: -1, dates: "2–3 Oct" }
  ],
  notifications: [
    { g: "Today", type: "requests", icon: "inbox", tone: "sky", t: "Ayesha wants to borrow your drill", d: "14–16 Oct · Not enough history yet", time: "10m", href: "#/requests/r1", unread: 1, mins: 40 },
    { g: "Today", type: "loans", icon: "package-check", tone: "green", t: "Handover today at 5:00 pm", d: "Large deg from Bilal · masjid parking", time: "1h", href: "#/handover/b1/borrower", unread: 1 },
    { g: "Today", type: "loans", icon: "calendar-range", tone: "sky", t: "Usman suggested new dates", d: "Projector · 21–22 Oct instead of 20–21", time: "2h", href: "#/counter/b9", unread: 1 },
    { g: "Today", type: "moderation", icon: "message-square-text", tone: "saffron", t: "A moderator needs your reply", d: "Case D-014 · plastic chairs", time: "3h", href: "#/case/b5", unread: 1, mins: 290 },
    { g: "Today", type: "community", icon: "message-circle-reply", tone: "violet", t: "Farah answered your question", d: "“Best tailor for school uniforms?”", time: "4h", href: "#/forum/p2", unread: 0 },
    { g: "Today", type: "loans", icon: "alarm-clock", tone: "coral", t: "Physics books are 1 day overdue", d: "Return today or a dispute opens on 14 Oct", time: "8am", href: "#/loan/b7", unread: 0 },
    { g: "Earlier", type: "community", icon: "calendar-check", tone: "violet", t: "You're off the waitlist", d: "Sunday park cleanup · 19 Oct", time: "1d", href: "#/event/e2", unread: 0 },
    { g: "Earlier", type: "moderation", icon: "scale", tone: "neutral", t: "Decision on case D-011", d: "Rabia decided for the lender · you can appeal", time: "2d", href: "#/decision/b11", unread: 0 },
    { g: "Earlier", type: "loans", icon: "star", tone: "green", t: "Review your loan from Bilal", d: "Reviews close in 5 days", time: "3d", href: "#/review/b4", unread: 0 }
  ],
  conversations: [
    { id: "b1", with: "u2", kind: "Item chat", about: "deg", last: "Bring a cloth bag, the lid is heavy.", time: "5:21 pm", unread: 1 },
    { id: "e1", with: "u4", kind: "Event group", about: "Mehndi rehearsal", group: true, last: "Hira: Chairs arrive at 6, not 5.", time: "4:02 pm", unread: 3 },
    { id: "m1", with: "mod", kind: "Moderator", last: "Please add your pickup photo to D-014.", time: "10:42 am", unread: 0 },
    { id: "b2", with: "u5", kind: "Item chat", about: "ladder", last: "No rush, Sunday is fine.", time: "Yesterday", unread: 0 },
    { id: "b6", with: "u1", kind: "Item chat", about: "drill", last: "Is the bit set included?", time: "Mon", unread: 0 }
  ],
  forumCats: [["all", "All"], ["ask", "Ask the community"], ["recs", "Local recommendations"], ["skills", "Skill sharing"], ["lost", "Lost and found"], ["parenting", "Parenting"], ["garden", "Gardening"], ["diy", "DIY & home"], ["projects", "Community projects"], ["trade", "Buy, sell or trade"], ["services", "Local services"], ["events", "Event announcements"]],
  posts: [
    { id: "p1", cat: "ask", catL: "Ask the community", author: "u6", t: "Water tanker rates this summer — who do you call?", ex: "Our line has been dry three days. What are neighbours paying for a 1,000 gallon tanker, and is anyone sharing deliveries?", votes: 42, comments: 18, solved: true, time: "2h", tags: ["water", "summer"], photo: null },
    { id: "p2", cat: "recs", catL: "Local recommendations", author: "u0", t: "Best tailor for school uniforms near Lane 3?", ex: "Need six shirts and two trousers stitched before the term starts. Who's quick and doesn't overcharge?", votes: 27, comments: 9, solved: true, time: "5h", tags: ["tailor", "school"] },
    { id: "p3", cat: "lost", catL: "Lost and found", author: "u3", t: "Found: grey cat with a red collar near the park gate", ex: "Very friendly, seems well fed. She's in our porch for now. Message me if she's yours.", votes: 61, comments: 12, time: "8h", photo: "photo-1514888286974-6c03e2ca1dba" },
    { id: "p4", cat: "projects", catL: "Community projects", author: "u4", t: "Plant 50 neem trees along the main road — volunteers?", ex: "The parks department will give saplings for free if we arrange watering for three months. Looking for 12 households.", votes: 88, comments: 31, time: "1d", photo: "photo-1466692476868-aef1dfb1e735" },
    { id: "p5", cat: "diy", catL: "DIY & home", author: "u5", t: "How to fix a dripping mixer tap without calling a plumber", ex: "Step by step with photos. All you need is a 10 mm spanner, a new washer (Rs 40) and twenty minutes.", votes: 54, comments: 7, time: "2d", tags: ["plumbing", "guide"] },
    { id: "p6", cat: "parenting", catL: "Parenting", author: "u7", t: "Swap circle for outgrown kids' clothes, ages 2 to 8", ex: "Instead of buying, let's swap every second Sunday. I'll host the first one in my garage.", votes: 33, comments: 14, time: "3d" }
  ],
  comments: {
    p1: [
      { id: "c1", by: "u7", text: "We pay Rs 2,800 for 1,000 gallons from the Model Town filling point. Ask for Rashid, he comes within 2 hours. If three of us on Lane 3 order together, he does Rs 2,500 each.", votes: 24, best: true, time: "1h",
        replies: [{ by: "u6", text: "Thank you! I'm in for the shared order on Thursday.", votes: 3, time: "50m" }, { by: "u2", text: "Count Lane 2 in as well.", votes: 2, time: "40m" }] },
      { id: "c2", by: "u3", text: "WASA's own tankers are cheaper (Rs 1,900) but you need to book a day ahead on the helpline.", votes: 11, time: "1h" },
      { id: "c3", by: "u5", text: "Check the float valve in your overhead tank too. Ours was stuck and we thought the line was dry.", votes: 7, time: "30m" }
    ]
  },
  badges: [
    ["Helpful contributor", "heart-handshake", "green", "10 answers marked helpful by 5 different neighbours"],
    ["Top answerer", "award", "saffron", "Most best answers in Block C this month, minimum 5"],
    ["Verified expert", "badge-check", "sky", "Granted by an admin after checking a qualification (tailor, electrician, doctor…)"],
    ["Event organizer", "calendar-heart", "violet", "Hosted 3 events with at least 70% attendance"],
    ["Community volunteer", "hand-helping", "coral", "Volunteered at 3 community projects or cleanups"],
    ["Trusted advisor", "shield-check", "green", "Moderator-nominated after 6 months of consistent, respectful answers"]
  ],
  events: [
    { id: "e1", t: "Mehndi rehearsal & dholki night", type: "Local celebration", photo: "photo-1621801306185-8c0ccf9c8eb8", day: 18, mon: "OCT", dow: "Sat", time: "7:00 – 10:30 pm", where: "Lane 1 community hall", org: "u4", cap: 60, reg: 52, fee: "Free", mode: "In person", vis: "Community only", why: [["Matches your interests", "celebrations, cooking", 30], ["Near you", "Lane 1, 3 min walk", 25], ["Organizer history", "Hira hosted 4 events", 18], ["Fits your evenings", "you joined 2 evening events", 12]], status: "registered" },
    { id: "e2", t: "Sunday park cleanup", type: "Cleanup", photo: "photo-1532996122724-e3c354a0b15b", day: 19, mon: "OCT", dow: "Sun", time: "8:00 – 10:00 am", where: "Block C park", org: "u7", cap: 40, reg: 40, fee: "Free", mode: "In person", vis: "Public", why: [["New for you", "you haven't joined a cleanup yet", 5], ["Near you", "park gate", 25]], status: "waitlist", pos: 2 },
    { id: "e3", t: "Kitchen garden workshop", type: "Workshop", photo: "photo-1466692476868-aef1dfb1e735", day: 22, mon: "OCT", dow: "Wed", time: "5:00 – 6:30 pm", where: "Farah's rooftop, Lane 6", org: "u7", cap: 15, reg: 9, fee: "Rs 200 materials", mode: "In person", vis: "Community only", why: [["Matches your interests", "gardening", 30]] },
    { id: "e4", t: "Kids' cricket morning", type: "Sports", photo: "photo-1531415074968-036ba1b575da", day: 26, mon: "OCT", dow: "Sun", time: "9:00 – 11:00 am", where: "School ground", org: "u2", cap: 24, reg: 17, fee: "Free", mode: "In person", vis: "Public", why: [["Popular nearby", "17 neighbours going", 20]] },
    { id: "e5", t: "Kameti members' monthly meet", type: "Savings gathering", photo: "photo-1556761175-5973dc0f32e7", day: 1, mon: "NOV", dow: "Sat", time: "4:00 – 5:00 pm", where: "Online (video call)", org: "u6", cap: 12, reg: 12, fee: "Free", mode: "Online", vis: "Invitation only", why: [["You're a member", "Lane 3 kameti", 30]] }
  ],
  vendors: [
    { id: "v1", name: "Rashid Tailors", cat: "Tailor", icon: "scissors", photo: "photo-1558769132-cb1aea458c5e", lane: "Main Market", hours: "10 am – 9 pm", open: true, verified: true, reviews: 38, line: "School uniforms, shalwar kameez, alterations in 48 h", services: [["School uniform shirt", "Rs 650"], ["Shalwar kameez stitching", "Rs 1,800"], ["Hemming / alteration", "from Rs 200"]] },
    { id: "v2", name: "Asif Electric Works", cat: "Electrician", icon: "zap", photo: "photo-1621905251189-08b45d6a269e", lane: "Lane 9", hours: "9 am – 7 pm", open: true, verified: true, reviews: 52, line: "UPS and inverter installs, wiring, fans", services: [["Ceiling fan install", "Rs 800"], ["UPS battery check", "Rs 500"]] },
    { id: "v3", name: "Ammi's Kitchen", cat: "Home chef", icon: "chef-hat", photo: "photo-1631515243349-e0cb75fb8d3a", lane: "Lane 4", hours: "Orders by 11 am", open: false, verified: false, reviews: 14, line: "Home-cooked lunch boxes, biryani by the deg on order", services: [["Lunch box", "Rs 450"], ["Chicken biryani, 1 deg", "Rs 14,000"]] },
    { id: "v4", name: "Bright Minds Tuition", cat: "Tutor", icon: "graduation-cap", photo: "photo-1509062522246-3755977927d7", lane: "Lane 6", hours: "4 pm – 8 pm", open: true, verified: true, reviews: 21, line: "O and A level maths and physics, small groups", services: [["Group class / month", "Rs 6,000"]] },
    { id: "v5", name: "Green Leaf Nursery", cat: "Plants", icon: "sprout", photo: "photo-1466692476868-aef1dfb1e735", lane: "Canal Road", hours: "8 am – 6 pm", open: true, verified: false, reviews: 9, line: "Seedlings, pots and soil, delivery in Block C", services: [["Tomato seedlings ×6", "Rs 300"]] }
  ],
  feed: [
    ["u2", "lent a", "deg", "to Nadia"], ["u5", "returned a", "ladder", "on time"], ["u7", "answered", "a water tanker question", ""], ["u4", "is hosting", "a mehndi rehearsal", "Sat"],
    ["u3", "listed a", "projector", "in Electronics"], ["u6", "joined", "Block C", "welcome!"], ["u1", "borrowed", "books", "for exams"], ["u5", "earned", "Top answerer", "badge"]
  ],
  cases: [
    { id: "D-014", kind: "dispute", prio: "high", title: "Condition dispute · plastic chairs", sub: "Hira (lender) vs Sana (borrower)", age: "2h", state: "DISPUTED", item: "chairs" },
    { id: "H-221", kind: "hold", prio: "high", title: "Held · projector request", sub: "Faisal N. · high value, weak evidence", age: "35m", state: "HELD_FOR_REVIEW", trigger: "high_value_low_confidence", item: "projector" },
    { id: "A-003", kind: "appeal", prio: "med", title: "Appeal · decision on D-011", sub: "Sana appeals Rabia's decision", age: "1h", state: "APPEALED", item: "chairs" },
    { id: "H-219", kind: "hold", prio: "med", title: "Held · unusual rating pattern", sub: "Zain M. · 2 signals corroborated", age: "4h", state: "HELD_FOR_REVIEW", trigger: "manipulation_risk", item: "tent" },
    { id: "D-016", kind: "dispute", prio: "med", title: "Overdue · books not returned", sub: "Opened by the scheduler after 2 reminders", age: "5h", state: "DISPUTED", trigger: "overdue", item: "books" },
    { id: "H-217", kind: "hold", prio: "low", title: "Held · assessment didn't finish", sub: "Mariam S. · engine timeout", age: "6h", state: "HELD_FOR_REVIEW", trigger: "engine_failure", item: "deg" }
  ],
  joinRequests: [
    { id: "M-88", name: "Omar Farooq", initials: "OF", result: "inconclusive", detail: "Location skipped · invited by Bilal", age: "1h", flags: [] },
    { id: "M-87", name: "Zara Ali", initials: "ZA", result: "conflicting", detail: "Outside the boundary · invited by Usman", age: "5h", flags: ["Same device as an existing account"] },
    { id: "M-86", name: "Tariq Mehmood", initials: "TM", result: "verified", detail: "Inside the boundary · invited by Kamran", age: "1d", flags: [], taken: "Rabia" }
  ],
  reports: [
    { id: "R-41", what: "Forum post", t: "“Selling cheap gold, DM me”", why: "Spam · suspicious link", by: "Automatic flag + 3 members", prio: "high" },
    { id: "R-40", what: "Comment", t: "Mixed Urdu/English reply in DIY thread", why: "Uncertain language, sent to a person", by: "Automatic flag", prio: "low" },
    { id: "R-39", what: "User", t: "Repeated no-shows by one account", why: "Reported by 2 lenders", by: "Members", prio: "med" }
  ],
  audit: [
    [1284, "16 Oct 10:42:18", "Imran Q.", "Moderator", "info_requested", "Case D-014", "DISPUTED", "DISPUTED", "Asked borrower for pickup photos", "mod:c1", "9f2c…e81a"],
    [1283, "16 Oct 09:15:02", "System", "Engine", "held_for_review", "Txn T-5531", "LOCALITY_CHECKED", "HELD_FOR_REVIEW", "high_value_low_confidence (R4)", "svc:assurance", "41ab…07cd"],
    [1282, "16 Oct 08:00:04", "System", "Scheduler", "dispute_opened", "Txn T-5470", "ACTIVE", "DISPUTED", "Overdue after 2 reminders (run 3f1e)", "svc:scheduler", "b902…44c1"],
    [1281, "15 Oct 21:03:44", "Rabia S.", "Moderator", "membership_approved", "T•••q M.", "PENDING", "APPROVED", "Inside boundary, invitation valid", "mod:c1", "c7d0…9b12"],
    [1280, "15 Oct 18:27:10", "Hira A.", "Member", "dispute_opened", "Txn T-5490", "RETURN_INITIATED", "DISPUTED", "Damage: 2 chairs cracked", "party:lender", "5e19…a4f0"],
    [1279, "15 Oct 12:55:31", "Bilal R.", "Member", "request_accepted", "Txn T-5512", "ASSESSED", "ACCEPTED", "", "party:lender", "aa30…11e7"],
    [1278, "15 Oct 12:55:31", "System", "Lifecycle", "request_declined", "Txn T-5513", "ASSESSED", "DECLINED", "dates taken (overlap constraint)", "svc:lifecycle", "0b77…d3c9"],
    [1277, "14 Oct 20:00:00", "System", "Scheduler", "no_show", "Txn T-5466", "ACCEPTED", "NO_SHOW", "Grace period passed (run 2c9a)", "svc:scheduler", "e4c2…5f68"],
    [1276, "13 Oct 16:20:09", "Saad A.", "Admin", "audit_viewed", "Filter: disputes", "", "", "Weekly review", "admin", "7713…ab02"]
  ]
};
