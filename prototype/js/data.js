/* Mock data for the prototype, shaped like the Digital Mohalla REST API on branch
   iteration2/slice3 (backend/app/api/schemas.py). Field names, enums and status lists follow the
   API and docs/design/06_data_model/schema.sql; timers follow backend/config/engine.json
   (config 1.3.7-iteration2-draft). ALL PEOPLE, ITEMS AND NUMBERS ARE SYNTHETIC.
   Fields a screen only needs for looks (photo, lane, icon) are marked "UI". */

const IMG = (id, w = 800, h) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${w}${h ? "&h=" + h : ""}&q=72`;

/* decision_policy_alg4 safeguard codes and their labels (domain/assurance/policy/decision.py) */
const SAFEGUARDS = {
  STANDARD_RETURN_REMINDER: "Send the standard return reminder",
  CONDITION_PHOTOS_CHECKLIST: "Photograph the item and complete the condition checklist",
  DEPOSIT_RECORD: "Record the deposit before handover",
  EXPLICIT_RETURN_REMINDER: "Agree the return date explicitly and send a reminder",
  MEDIUM_VALUE_DEPOSIT_RECORD: "Record a deposit suited to a medium-value item",
  HIGH_VALUE_DEPOSIT_RECORD: "Record a deposit suited to a high-value item",
  HANDOVER_PHOTOS: "Take item photos at handover",
  HANDOVER_CHECKLIST: "Complete the handover checklist together",
  FIXED_RETURN_DATE: "Agree a fixed return date"
};
const sg = (...codes) => codes.map(code => ({ code, label: SAFEGUARDS[code] }));

window.DB = {
  img: IMG,
  me: "u0",
  configVersion: "1.3.7-iteration2-draft",
  safeguards: SAFEGUARDS,
  /* scheduler_b13, reviews_d1, moderation_i4, locality_a11, decision_policy_alg4.value_bands_pkr */
  timers: { responseWindowH: 72, handoverGraceH: 24, returnReminderH: 24, overdueLimitH: 72, minReminders: 2, confirmationReminderH: 24, disputeWindowD: 7, partyResponseH: 72, listingExpiryD: 60, reviewWindowD: 14, reviewEditH: 24, appealWindowD: 7, inviteTtlD: 7, maxOpenInvites: 3, lowMax: 5000, mediumMax: 15000, photoMaxMB: 5, photoLinkMin: 10 },
  /* reviews_d1.dimensions: what you rate, by the other party's role */
  reviewDims: {
    LENDER: [["condition_accuracy", "Item was as described"], ["fair_terms", "Terms were fair"], ["responsiveness", "Replied and turned up on time"], ["dispute_fairness", "Fair if anything went wrong"]],
    BORROWER: [["punctuality", "On time for handover and return"], ["care_for_item", "Took care of the item"], ["communication", "Easy to talk to"], ["follow_terms", "Followed the terms"]]
  },

  /* CommunityListOut (+ photo: UI). methods: verification_method enum */
  community: { id: "c1", name: "Block C, Gulberg III", short: "Block C", city: "Lahore", members: 214, join_code: "GUL-C",
    rules: ["Lend and borrow only inside Block C and the two lanes next to it.", "Hand over in a public spot: the park gate or the masjid parking.", "Record deposits in the app. Money never moves through Digital Mohalla.", "In reviews and posts, describe what happened, not the person."] },
  communities: [
    { id: "c1", name: "Block C, Gulberg III", city: "Lahore", member_count: 214, join_code: "GUL-C", methods: ["GEOFENCE_INVITATION", "MODERATOR_APPROVAL"], has_boundary: true, photo: "photo-1684323041566-1958d8056e8a", mine: "APPROVED" },
    { id: "c2", name: "Main Market Lanes", city: "Lahore", member_count: 132, join_code: "MML", methods: ["GEOFENCE_INVITATION", "MODERATOR_APPROVAL"], has_boundary: true, photo: "photo-1667650708785-2179a8eb2b70", mine: "PENDING" },
    { id: "c3", name: "Liberty Residency", city: "Lahore", member_count: 88, join_code: "LRT", methods: ["MODERATOR_APPROVAL"], has_boundary: false, photo: "photo-1655449767937-754b25282108", mine: null },
    { id: "c4", name: "Model Town Block K", city: "Lahore", member_count: 301, join_code: "MTK", methods: ["GEOFENCE_INVITATION", "MODERATOR_APPROVAL"], has_boundary: true, photo: "photo-1601969700719-d31890dd6b30", mine: "REJECTED" }
  ],
  /* POST /communities/{id}/invitations: code shown once, invite_ttl_days 7, max_open_invites 3 */
  invitations: [{ code: "GUL-C-7K2Q", expires: "30 Oct", used: false }, { code: "GUL-C-M4XB", expires: "24 Oct", used: true }],

  users: {
    u0: { name: "Sana Malik", short: "Sana", initials: "SM", photo: "photo-1550546094-9835463f9f71", since: "Mar 2026", lane: "Lane 3" },
    u1: { name: "Ayesha Khan", short: "Ayesha", initials: "AK", photo: "photo-1536766768598-e09213fdcf22", since: "Oct 2026", lane: "Lane 4" },
    u2: { name: "Bilal Raza", short: "Bilal", initials: "BR", photo: "photo-1621960883434-e910537c8052", since: "Jan 2026", lane: "Lane 2", badge: "Trusted lender" },
    u3: { name: "Usman Tariq", short: "Usman", initials: "UT", photo: "photo-1711374316403-2bfa31ae9c2a", since: "Jun 2026", lane: "Lane 7" },
    u4: { name: "Hira Aslam", short: "Hira", initials: "HA", since: "Feb 2026", lane: "Lane 1", badge: "Event organizer" },
    u5: { name: "Kamran Javed", short: "Kamran", initials: "KJ", photo: "photo-1618306842557-a2515acf2112", since: "Nov 2025", lane: "Lane 5", badge: "Top answerer" },
    u6: { name: "Nadia Pervez", short: "Nadia", initials: "NP", photo: "photo-1516239482977-b550ba7253f2", since: "Aug 2026", lane: "Lane 3" },
    u7: { name: "Farah Siddiqui", short: "Farah", initials: "FS", photo: "photo-1552113125-81af17f36b57", since: "Apr 2026", lane: "Lane 6", badge: "Verified expert" },
    u8: { name: "Faisal Nawaz", short: "Faisal", initials: "FN", since: "Oct 2026", lane: "Lane 8" },
    u9: { name: "Zain Mirza", short: "Zain", initials: "ZM", since: "Sep 2026", lane: "Lane 2" },
    u10: { name: "Mariam Shah", short: "Mariam", initials: "MS", since: "Jul 2026", lane: "Lane 4" },
    mod: { name: "Imran Qureshi", short: "Imran", initials: "IQ", photo: "photo-1617817638453-4480d05e0b83", role: "Moderator" },
    mod2: { name: "Rabia Saeed", short: "Rabia", initials: "RS", role: "Moderator" },
    admin: { name: "Saad Ahmed", short: "Saad", initials: "SA", role: "Admin" }
  },

  /* CategoryOut (+ icon: UI). Restricted categories need COMMUNITY_VERIFIED (FR-B-02). */
  categories: [
    { id: "all", label: "All", icon: "layout-grid" },
    { id: 1, label: "Tools & DIY", icon: "hammer", is_restricted: false, min_verification: "UNVERIFIED" },
    { id: 2, label: "Party & events", icon: "party-popper", is_restricted: false, min_verification: "UNVERIFIED" },
    { id: 3, label: "Kitchen", icon: "cooking-pot", is_restricted: false, min_verification: "UNVERIFIED" },
    { id: 4, label: "Baby & kids", icon: "baby", is_restricted: false, min_verification: "UNVERIFIED" },
    { id: 5, label: "Outdoor & sports", icon: "tent", is_restricted: false, min_verification: "UNVERIFIED" },
    { id: 6, label: "Electronics", icon: "projector", is_restricted: true, min_verification: "COMMUNITY_VERIFIED" },
    { id: 7, label: "Books", icon: "book-open", is_restricted: false, min_verification: "UNVERIFIED" },
    { id: 8, label: "Medical", icon: "accessibility", is_restricted: true, min_verification: "COMMUNITY_VERIFIED" }
  ],

  /* ListingOut / ItemOut. condition NEW|GOOD|FAIR|WORN; value_band LOW|MEDIUM|HIGH;
     status DRAFT|PENDING_REVIEW|PUBLISHED|PAUSED|EXPIRED|REMOVED; booked = days of booked_periods.
     reason = SearchResultOut.reason. photo, lane, noun, trend: UI. */
  items: [
    { id: "makita", title: "Cordless drill, 2 batteries", noun: "drill", category_id: 1, photo: "photo-1572981779307-38b8cabb2407", lender: "u5", deposit: 3000, condition: "GOOD", value_band: "MEDIUM", lane: "Lane 5", booked: [], status: "PUBLISHED", required_verification: "UNVERIFIED",
      desc: "18V cordless drill-driver with two batteries, a charger and a case of wood and metal bits.", usage_terms: "Charge the batteries before returning. Wood and metal bits only.", handover_method: "Pick up from the lender's gate", search_terms: "drill, drill machine, screwdriver, barma",
      reason: "Matches “drill” · items as described in 10 of 11 loans · free on your dates" },
    { id: "deg", title: "Large deg for 40 guests", noun: "deg", category_id: 3, photo: "photo-1790008882050-76a602990485", lender: "u2", deposit: 1500, condition: "GOOD", value_band: "MEDIUM", lane: "Lane 2", booked: [18, 19], status: "PUBLISHED", required_verification: "UNVERIFIED", trend: "Booked 9× this season",
      desc: "Aluminium deg with lid and a long kafgeer. Enough biryani or haleem for about 40 people.", usage_terms: "Return scrubbed, with no burnt base.", handover_method: "Masjid parking", search_terms: "deg, degchi, biryani pot, cooking pot",
      reason: "Matches “cooking pot” · Bilal has lent it 9 times" },
    { id: "chairs", title: "Plastic chairs, set of 20", noun: "chairs", category_id: 2, photo: "photo-1778230501599-90003014460d", lender: "u4", deposit: 3000, condition: "FAIR", value_band: "MEDIUM", lane: "Lane 1", booked: [18, 19], status: "PUBLISHED", required_verification: "UNVERIFIED", trend: "Wedding season favourite",
      desc: "Stackable plastic chairs in two bundles of ten; 2 have scratches. You'll need a car or a rickshaw.", usage_terms: "Count all 20 at handover and at return.", handover_method: "Park gate", search_terms: "chairs, kursiyan, shaadi chairs",
      reason: "Some dates already booked" },
    { id: "ladder", title: "Aluminium ladder, 8 ft", noun: "ladder", category_id: 1, photo: "photo-1617515457325-728e2a50cd87", lender: "u5", deposit: 0, condition: "GOOD", value_band: "LOW", lane: "Lane 5", booked: [], status: "PUBLISHED", required_verification: "UNVERIFIED",
      desc: "Folding A-frame ladder that holds up to 120 kg. New rubber feet this year.", usage_terms: "Not for use on wet floors.", handover_method: "Pick up from the lender's gate", search_terms: "seedhi, ladder, step ladder",
      reason: "In your community and free on your dates" },
    { id: "tent", title: "4-person camping tent", noun: "tent", category_id: 5, photo: "photo-1504280390367-361c6d9f38f4", lender: "u2", deposit: 2500, condition: "GOOD", value_band: "MEDIUM", lane: "Lane 2", booked: [24, 25, 26, 27], status: "PUBLISHED", required_verification: "UNVERIFIED", trend: "Northern trips",
      desc: "Dome tent with rain fly, pegs and carry bag. Used twice in Naran.", usage_terms: "Dry it before returning.", handover_method: "Pick up from the lender's gate", search_terms: "tent, camping, khaima",
      reason: "Bilal has 14 completed loans as a lender" },
    { id: "projector", title: "Projector + 100-inch screen", noun: "projector", category_id: 6, photo: "photo-1535016120720-40c646be5580", lender: "u3", deposit: 8000, condition: "GOOD", value_band: "HIGH", lane: "Lane 7", booked: [], status: "PUBLISHED", required_verification: "COMMUNITY_VERIFIED", trend: "Match nights",
      desc: "1080p projector, pull-up screen and HDMI cable. Match nights and mehndi slideshows.", usage_terms: "Keep it indoors. Pack the screen in its tube.", handover_method: "Park gate", search_terms: "projector, screen, movie night",
      reason: "High-value item · verified members only" },
    { id: "wheelchair", title: "Folding wheelchair", noun: "wheelchair", category_id: 8, photo: "photo-1619618691037-751d1e6c9ad1", lender: "u6", deposit: 5000, condition: "GOOD", value_band: "MEDIUM", lane: "Lane 3", booked: [], status: "PUBLISHED", required_verification: "COMMUNITY_VERIFIED",
      desc: "Lightweight folding wheelchair with footrests. For neighbours after surgery or elderly visitors.", usage_terms: "Up to two weeks. Wipe the seat before returning.", handover_method: "Pick up from the lender's gate", search_terms: "wheelchair, wheel chair",
      reason: "Medical items need a verified member" },
    { id: "stroller", title: "Reclining baby stroller", noun: "stroller", category_id: 4, photo: "photo-1559135141-2bea6465fccf", lender: "u1", deposit: 1000, condition: "GOOD", value_band: "LOW", lane: "Lane 4", booked: [], status: "PUBLISHED", required_verification: "UNVERIFIED",
      desc: "Reclining stroller with rain cover; folds one-handed.", usage_terms: "Fold it gently; the hinge is stiff.", handover_method: "Pick up from the lender's gate", search_terms: "stroller, pram, baby gaari",
      reason: "New lender: shown at the community baseline" },
    { id: "books", title: "O-level Physics books", noun: "books", category_id: 7, photo: "photo-1497633762265-9d179a990aa6", lender: "u5", deposit: 0, condition: "WORN", value_band: "LOW", lane: "Lane 5", booked: [], status: "PUBLISHED", required_verification: "UNVERIFIED",
      desc: "Textbook plus two years of solved past papers. Some highlighting.", usage_terms: "Up to one term.", handover_method: "Pick up from the lender's gate", search_terms: "physics, o level, past papers, kitaab",
      reason: "Matches “books”" },
    { id: "drill", title: "Bosch impact drill + bits", noun: "drill", category_id: 1, photo: "photo-1622044939413-0b829c342434", lender: "u0", deposit: 2000, condition: "GOOD", value_band: "MEDIUM", lane: "Lane 3", booked: [14, 15, 16], status: "PUBLISHED", required_verification: "UNVERIFIED",
      desc: "650W impact drill with a 13-piece bit set and a spare chuck key.", usage_terms: "Masonry bits only for brick and concrete. Return wiped clean of dust.", handover_method: "From my gate", search_terms: "drill, barma, impact drill", reason: "" }
  ],

  /* LenderEvidenceOut per lender (GET /items/{id}, search). FactorOut: never a score;
     estimate and interval only when `enough`. Lender metrics: CONDITION_AGREED, DISPUTE_FREE. */
  lenderEv: {
    u1: { has_history: false, summary: "No verified loans as a lender yet. That is not a negative finding.", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 0, enough: false, confidence: "", note: "Not enough verified history yet. That is not a negative finding." },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 0, enough: false, confidence: "", note: "Not enough verified history yet. That is not a negative finding." }] },
    u2: { has_history: true, summary: "14 verified loans as a lender.", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 14, enough: true, estimate: 0.93, interval_low: 0.81, interval_high: 0.98, confidence: "high confidence", note: "" },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 14, enough: true, estimate: 0.95, interval_low: 0.84, interval_high: 0.99, confidence: "high confidence", note: "" }] },
    u3: { has_history: true, summary: "5 verified loans as a lender.", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 5, enough: true, estimate: 0.78, interval_low: 0.5, interval_high: 0.94, confidence: "moderate confidence", note: "" },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 5, enough: true, estimate: 0.74, interval_low: 0.45, interval_high: 0.92, confidence: "moderate confidence", note: "" }] },
    u4: { has_history: true, summary: "9 verified loans as a lender. One open dispute is not counted until it's resolved.", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 9, enough: true, estimate: 0.88, interval_low: 0.7, interval_high: 0.97, confidence: "moderate confidence", note: "" },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 9, enough: true, estimate: 0.9, interval_low: 0.72, interval_high: 0.98, confidence: "moderate confidence", note: "" }] },
    u5: { has_history: true, summary: "11 verified loans as a lender.", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 11, enough: true, estimate: 0.91, interval_low: 0.77, interval_high: 0.98, confidence: "high confidence", note: "" },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 11, enough: true, estimate: 0.93, interval_low: 0.79, interval_high: 0.99, confidence: "high confidence", note: "" }] },
    u6: { has_history: true, summary: "2 verified loans as a lender.", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 2, enough: false, confidence: "", note: "Too few loans to show detail." },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 2, enough: false, confidence: "", note: "Too few loans to show detail." }] }
  },

  /* MyEvidenceOut (GET /me/evidence): per role, factor by factor */
  myEvidence: { note: "Each factor is shown on its own, never combined into one number. Recent, similar loans count most, and a disputed loan counts only after a moderator resolves it.", roles: [
    { role: "BORROWER", factors: [
      { metric: "ON_TIME_RETURN", label: "Returns on time", verified_loans: 7, enough: true, estimate: 0.9, interval_low: 0.72, interval_high: 0.98, confidence: "high confidence", note: "" },
      { metric: "CONDITION_AGREED", label: "Item as described and returned in agreed condition", verified_loans: 7, enough: true, estimate: 0.92, interval_low: 0.75, interval_high: 0.98, confidence: "high confidence", note: "" },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 6, enough: true, estimate: 0.86, interval_low: 0.64, interval_high: 0.96, confidence: "moderate confidence", note: "One open dispute is not counted until a moderator resolves it." }] },
    { role: "LENDER", factors: [
      { metric: "CONDITION_AGREED", label: "Items are as described", verified_loans: 2, enough: false, confidence: "", note: "Too few loans to show detail." },
      { metric: "DISPUTE_FREE", label: "Loans without a dispute", verified_loans: 2, enough: false, confidence: "", note: "Too few loans to show detail." }] }] },

  /* RequestOut for the lender (GET /requests/{id}); assessment = AssessmentOut.
     dates = [start, end) with an exclusive end; expires = minutes left of the 72 h window (UI);
     lede = the plain-language line the app writes (UI). */
  requests: {
    r1: { id: "r1", item: "drill", borrower: "u1", state: "ASSESSED", hold_reason: null, your_role: "LENDER", dates: [14, 17], message: "Need it to put up shelves in my daughter's room. I'll pick it up after Asr.", deposit_required: true, expires: 40,
      overlap: { who: "Hamza A.", dates: "15–17 Oct" }, available_actions: ["accept", "decline"], moderator_safeguards: [],
      lede: "Ayesha joined Block C in October and hasn't completed a loan yet, as a borrower or a lender.",
      assessment: { assurance_state: "INSUFFICIENT_EVIDENCE", policy_decision: "REQUEST_VERIFICATION", rule_fired: "R3", config_version: "1.3.7-iteration2-draft",
        posterior_mean: 0.5, ci90_low: 0.05, ci90_high: 0.95, effective_evidence: 0, verified_loans: 0, community: { reliability: 0, paths: [] }, manipulation_risk: 8, manipulation_level: 1,
        safeguards: sg("DEPOSIT_RECORD", "HANDOVER_PHOTOS", "FIXED_RETURN_DATE"),
        explanation: "Insufficient verified history; lender review required. This is not a negative finding about the borrower. Direct evidence: no verified loans yet. Community paths from the lender: none found. Manipulation checks: no notable signals (level 1 of 4). Decision support, not a guarantee." } },
    r2: { id: "r2", item: "deg", borrower: "u6", state: "ASSESSED", hold_reason: null, your_role: "LENDER", dates: [20, 22], message: "Mehndi at our house on Saturday, cooking for 35.", deposit_required: true, expires: 300,
      available_actions: ["accept", "decline"], moderator_safeguards: [],
      lede: "Nadia has 2 verified loans in Block C, not enough on their own. Two neighbours in your circle have lent to her without problems.",
      assessment: { assurance_state: "REVIEW_RECOMMENDED", policy_decision: "PROCEED_WITH_SAFEGUARDS", rule_fired: "R9", config_version: "1.3.7-iteration2-draft",
        posterior_mean: 0.71, ci90_low: 0.31, ci90_high: 0.96, effective_evidence: 1.6, verified_loans: 2, manipulation_risk: 4, manipulation_level: 1,
        community: { reliability: 0.41, paths: [{ via: ["Bilal R."], strength: 0.62 }, { via: ["Kamran J.", "Hira A."], strength: 0.35 }] },
        safeguards: sg("MEDIUM_VALUE_DEPOSIT_RECORD", "HANDOVER_PHOTOS"),
        explanation: "Review recommended before lending. Direct evidence: 2 verified loan(s), weighted for recency and similarity to 1.6 effective outcomes; estimated on-time return 0.71 with a 90% interval of 0.31 to 0.96. Community paths from the lender: via Bilal R. (path strength 0.62); via Kamran J. then Hira A. (path strength 0.35); indirect reliability 0.41 (at most 0.60). Without these paths the request would be INSUFFICIENT_EVIDENCE. Manipulation checks: no notable signals (level 1 of 4). Decision support, not a guarantee." } },
    r3: { id: "r3", item: "tent", borrower: "u5", state: "ASSESSED", hold_reason: null, your_role: "LENDER", dates: [24, 28], message: "Family trip to Murree. We'll dry it properly before returning.", deposit_required: true, expires: 900,
      available_actions: ["accept", "decline"], moderator_safeguards: [],
      lede: "Kamran has 10 verified loans in Block C, returned on time and in the agreed condition. Most were outdoor and tool items like this one.",
      assessment: { assurance_state: "SUFFICIENT_EVIDENCE", policy_decision: "PROCEED_WITH_SAFEGUARDS", rule_fired: "R8", config_version: "1.3.7-iteration2-draft",
        posterior_mean: 0.91, ci90_low: 0.752, ci90_high: 0.995, effective_evidence: 9.5, verified_loans: 10, community: { reliability: 0, paths: [] }, manipulation_risk: 3, manipulation_level: 1,
        safeguards: sg("MEDIUM_VALUE_DEPOSIT_RECORD", "HANDOVER_PHOTOS"),
        explanation: "Sufficient verified evidence for this request. Direct evidence: 10 verified loan(s), weighted for recency and similarity to 9.5 effective outcomes; estimated on-time return 0.91 with a 90% interval of 0.75 to 0.99. Community paths from the lender: none found. Manipulation checks: no notable signals (level 1 of 4). Decision support, not a guarantee." } }
  },

  /* Sana's loans (GET /requests -> MyRequestOut, plus the request's available_actions).
     col = activity board column (UI); href = the screen for the next action (UI). */
  loans: [
    { id: "b6", item: "drill", your_role: "LENDER", other: "u1", state: "ASSESSED", actions: ["accept", "decline"], col: "action", label: "Decide on the request", tone: "saffron", next: "Accept, decline or suggest dates", mins: 40, href: "#/requests/r1", step: 0, dates: "14–16 Oct" },
    { id: "b1", item: "deg", your_role: "BORROWER", other: "u2", state: "ACCEPTED", actions: ["handover_confirm", "raise_dispute"], col: "action", label: "Confirm the handover", tone: "saffron", next: "Bilal recorded the condition at 5:04 pm", mins: 135, href: "#/handover/b1/borrower", step: 2, dates: "18–19 Oct", due: "Mon 20 Oct" },
    { id: "b5", item: "chairs", your_role: "BORROWER", other: "u4", state: "DISPUTED", actions: [], col: "action", label: "Moderator asked you", tone: "coral", next: "Reply before the deadline", mins: 290, href: "#/case/b5", step: 4, dates: "1–3 Oct" },
    { id: "b3", item: "drill", your_role: "LENDER", other: "u3", state: "RETURN_INITIATED", actions: ["return_checklist", "raise_dispute"], col: "action", label: "Inspect the return", tone: "sky", next: "Record the return checklist", href: "#/inspect/b3", step: 4, dates: "9–11 Oct" },
    { id: "b13", item: "ladder", your_role: "BORROWER", other: "u5", state: "RETURN_INITIATED", actions: ["return_confirm", "raise_dispute"], col: "action", label: "Confirm the return report", tone: "sky", next: "Kamran recorded the item's condition", mins: 1380, href: "#/return-confirm/b13", step: 4, dates: "6–8 Oct" },
    { id: "b10", item: "tent", your_role: "LENDER", other: "u5", state: "ACTIVE", actions: ["raise_dispute"], col: "action", label: "Extension requested", tone: "sky", next: "Approve or keep the due date", href: "#/extend-respond/b10", step: 3, dates: "24–27 Oct", extension: { new_due: "Thu 30 Oct", reason: "Rain in Murree, we're back two days later." } },
    { id: "b9", item: "projector", your_role: "BORROWER", other: "u3", state: "ASSESSED", actions: ["cancel"], col: "waiting", label: "New dates suggested", tone: "sky", next: "Usman offers 21–22 Oct", mins: 600, href: "#/counter/b9", step: 0, dates: "20–21 Oct", counter: { start: 21, end: 23, message: "The 20th we're out of town. Can you take it on the 21st?" } },
    { id: "b14", item: "wheelchair", your_role: "BORROWER", other: "u6", state: "HELD_FOR_REVIEW", hold_reason: "high_value_low_confidence", actions: ["cancel"], col: "waiting", label: "With a moderator", tone: "violet", next: "Checked before Nadia sees it", href: "#/loan/b14", step: 0, dates: "25 Oct–1 Nov" },
    { id: "b2", item: "ladder", your_role: "BORROWER", other: "u5", state: "ACTIVE", actions: ["initiate_return", "raise_dispute"], col: "active", label: "Due tomorrow", tone: "green", next: "Return by Wed 15 Oct", mins: 1560, href: "#/loan/b2", step: 3, dates: "13–14 Oct", due: "Wed 15 Oct" },
    { id: "b7", item: "books", your_role: "BORROWER", other: "u5", state: "ACTIVE", actions: ["initiate_return", "raise_dispute"], col: "active", label: "Overdue 1 day", tone: "coral", next: "2 reminders sent", mins: 1320, href: "#/loan/b7", step: 3, dates: "1–11 Oct", due: "Sun 12 Oct", overdue: true },
    { id: "b4", item: "tent", your_role: "BORROWER", other: "u2", state: "COMPLETED", actions: ["review"], col: "done", label: "Leave a review", tone: "green", next: "Reviews close 14 days after completion", href: "#/review/b4", step: 5, dates: "28 Sep–1 Oct" },
    { id: "b11", item: "chairs", your_role: "BORROWER", other: "u4", state: "COMPLETED", actions: [], col: "done", label: "Decision made", tone: "violet", next: "You can appeal within 7 days", href: "#/decision/b11", step: 5, dates: "5–6 Sep" },
    { id: "b8", item: "stroller", your_role: "BORROWER", other: "u1", state: "EXPIRED", actions: [], col: "done", label: "Expired", tone: "neutral", next: "No reply within 72 hours", href: "#/item/stroller", step: -1, dates: "7–9 Oct" },
    { id: "b15", item: "deg", your_role: "BORROWER", other: "u2", state: "DECLINED", actions: [], col: "done", label: "Declined: dates taken", tone: "neutral", next: "Another request for these dates was accepted first", href: "#/item/deg", step: -1, dates: "11–12 Oct" },
    { id: "b12", item: "makita", your_role: "BORROWER", other: "u5", state: "NO_SHOW", actions: [], col: "done", label: "No-show", tone: "neutral", next: "Handover missed · dates released", href: "#/loan/b12", step: -1, dates: "2–3 Oct" }
  ],

  /* NotificationOut (GET /notifications). The app writes the sentence from type + payload.
     Types are the ones the backend sends (lifecycle, jobs, cases, appeals, membership, reviews). */
  notifications: [
    { id: "n1", type: "request_received", payload: { transaction_id: "r1", item_title: "Bosch impact drill + bits" }, when: "10m", g: "Today", read: false, href: "#/requests/r1" },
    { id: "n2", type: "handover_reminder", payload: { transaction_id: "b1", item_title: "Large deg for 40 guests" }, when: "1h", g: "Today", read: false, href: "#/handover/b1/borrower" },
    { id: "n3", type: "counter_offered", payload: { transaction_id: "b9", item_title: "Projector + 100-inch screen", proposed_period: "21–22 Oct" }, when: "2h", g: "Today", read: false, href: "#/counter/b9" },
    { id: "n4", type: "information_requested", payload: { case_id: "D-014", deadline: "Thu 16 Oct, 6:00 pm" }, when: "3h", g: "Today", read: false, href: "#/case/b5", mins: 290 },
    { id: "n5", type: "extension_requested", payload: { transaction_id: "b10", item_title: "4-person camping tent", new_due: "Thu 30 Oct" }, when: "4h", g: "Today", read: false, href: "#/extend-respond/b10" },
    { id: "n6", type: "return_reminder", payload: { transaction_id: "b2", item_title: "Aluminium ladder, 8 ft" }, when: "8am", g: "Today", read: true, href: "#/loan/b2" },
    { id: "n7", type: "review_received", payload: { transaction_id: "b4" }, when: "1d", g: "Earlier", read: true, href: "#/evidence" },
    { id: "n8", type: "request_declined", payload: { transaction_id: "b15", item_title: "Large deg for 40 guests", reason: "dates taken" }, when: "2d", g: "Earlier", read: true, href: "#/item/deg" },
    { id: "n9", type: "request_expired", payload: { transaction_id: "b8", item_title: "Reclining baby stroller" }, when: "5d", g: "Earlier", read: true, href: "#/item/stroller" },
    { id: "n10", type: "listing_expired", payload: { item_id: "tins", item_title: "Cake tins, set of 3" }, when: "6d", g: "Earlier", read: true, href: "#/listings" },
    { id: "n11", type: "membership_decided", payload: { status: "APPROVED", community: "Block C, Gulberg III" }, when: "Mar", g: "Earlier", read: true, href: "#/home" }
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
  /* CaseQueueOut + ModeratorCaseOut. trigger_type: DISPUTE | MANIPULATION_FLAG |
     HIGH_VALUE_LOW_CONFIDENCE | LOCALITY_HOLD | ENGINE_FAILURE. status: OPEN | AWAITING_INFORMATION |
     DECIDED | APPEALED | REVERSED | WITHDRAWN. priority: 1 most urgent. The queue row carries no
     names; the case screen shows borrower and lender names (ModeratorCaseOut). */
  cases: [
    { id: "D-014", trigger_type: "DISPUTE", dispute_reason: "DAMAGE", hold_reason: null, raised_by_role: "LENDER", status: "AWAITING_INFORMATION", priority: 1, opened: "2h", item: "chairs", state: "DISPUTED",
      reason: "Return inspection reported 2 cracked chair legs", borrower: "u0", lender: "u4", period: "1–3 Oct", dispute_stage: "RETURN_INITIATED",
      information_request: { to: "BORROWER", question: "Do you have photos from when you collected the chairs? Please also say where they were stored.", deadline: "Thu 16 Oct, 6:00 pm", mins: 290 },
      statements: [{ author_role: "LENDER", author_name: "Hira Aslam", statement: "Two chairs came back with cracked legs. They were fine at handover; the checklist says so.", at: "15 Oct, 6:30 pm" }] },
    { id: "H-221", trigger_type: "HIGH_VALUE_LOW_CONFIDENCE", hold_reason: "high_value_low_confidence", status: "OPEN", priority: 1, opened: "35m", item: "projector", state: "HELD_FOR_REVIEW",
      reason: "High-value request on weak or dissimilar evidence (rule R4)", borrower: "u8", lender: "u3", period: "20–21 Oct" },
    { id: "L-230", trigger_type: "LOCALITY_HOLD", hold_reason: "locality_conflict", status: "OPEN", priority: 2, opened: "3h", item: "deg", state: "HELD_FOR_REVIEW",
      reason: "The borrower's stored locality result conflicts with the community", borrower: "u10", lender: "u2", period: "25–26 Oct" },
    { id: "A-003", trigger_type: "DISPUTE", dispute_reason: "DAMAGE", raised_by_role: "LENDER", status: "APPEALED", priority: 2, opened: "1h", item: "chairs", state: "COMPLETED",
      reason: "Appeal of the decision on this dispute", borrower: "u0", lender: "u4", period: "5–6 Sep",
      appeal: { reason: "The leg was already split at pickup. It's in my pickup photo, which wasn't attached to the case.", filed: "1h ago", by_role: "BORROWER" },
      decisions: [{ decider: "Rabia S.", decider_role: "MODERATOR", kind: "DISPUTE_RESOLVED", at_fault: "borrower", possession: "RETURNED", reason: "The return photo shows a split leg that isn't in the handover photo. Deposit deduction of Rs 600 agreed in person.", decided: "12 Oct, 4:10 pm" }] },
    { id: "H-219", trigger_type: "MANIPULATION_FLAG", hold_reason: "manipulation_risk", status: "OPEN", priority: 2, opened: "4h", item: "tent", state: "HELD_FOR_REVIEW",
      reason: "Corroborated manipulation risk: 2 signals at 0.5 or above (level 4)", borrower: "u9", lender: "u2", period: "2–5 Nov",
      risk: { level: 4, score: 72, signals: [["Partners reviewing one another (S1)", 0.72], ["Similar review texts (S4)", 0.64]] } },
    { id: "D-016", trigger_type: "DISPUTE", dispute_reason: "NON_RETURN", raised_by_role: null, status: "OPEN", priority: 2, opened: "5h", item: "books", state: "DISPUTED",
      reason: "Not returned 72 hours after the due date, after 2 reminders (scheduler)", borrower: "u10", lender: "u5", period: "1–9 Oct", dispute_stage: "ACTIVE",
      statements: [{ author_role: "BORROWER", author_name: "Mariam Shah", statement: "My son took them to his hostel by mistake. They'll be back on Friday.", at: "1h ago" }] },
    { id: "H-217", trigger_type: "ENGINE_FAILURE", hold_reason: "engine_failure", status: "OPEN", priority: 3, opened: "6h", item: "ladder", state: "HELD_FOR_REVIEW",
      reason: "The assessment timed out (2,000 ms) and no state was assigned", borrower: "u1", lender: "u5", period: "18–19 Oct" }
  ],

  /* MembershipQueueOut (GET /moderation/memberships). Only coarse results are stored:
     locality_outcome VERIFIED | INCONCLUSIVE | CONFLICTING; boundary_signal INSIDE | NEAR_BOUNDARY |
     OUTSIDE | UNAVAILABLE. Never a position, distance or address. */
  joinRequests: [
    { id: "M-88", applicant_name: "Omar Farooq", initials: "OF", status: "PENDING", requested: "1h", locality_outcome: "INCONCLUSIVE", boundary_signal: "UNAVAILABLE", invitation_used: true, permission_refused: true, mock_provider_detected: false, duplicate_suspected: false },
    { id: "M-87", applicant_name: "Zara Ali", initials: "ZA", status: "PENDING", requested: "5h", locality_outcome: "CONFLICTING", boundary_signal: "OUTSIDE", invitation_used: true, permission_refused: false, mock_provider_detected: false, duplicate_suspected: true },
    { id: "M-89", applicant_name: "Faraz Butt", initials: "FB", status: "PENDING", requested: "6h", locality_outcome: "CONFLICTING", boundary_signal: "INSIDE", invitation_used: false, permission_refused: false, mock_provider_detected: true, duplicate_suspected: false },
    { id: "M-90", applicant_name: "Hamza Ali", initials: "HA", status: "AWAITING_INFORMATION", requested: "1d", locality_outcome: "INCONCLUSIVE", boundary_signal: "NEAR_BOUNDARY", invitation_used: false, permission_refused: false, mock_provider_detected: false, duplicate_suspected: false },
    { id: "M-86", applicant_name: "Tariq Mehmood", initials: "TM", status: "APPROVED", requested: "1d", locality_outcome: "VERIFIED", boundary_signal: "INSIDE", invitation_used: true, permission_refused: false, mock_provider_detected: false, duplicate_suspected: false, decided_by: "Rabia" }
  ],

  /* AuditEntryOut (GET /admin/audit). category DISPUTE | MEMBERSHIP | ASSURANCE | OTHER;
     outcome SUCCESS | REJECTED; masked members are shown as initials until unmasked with a purpose. */
  audit: [
    { id: 1284, source: "audit_log", at: "16 Oct 10:42:18", action: "info_requested", category: "DISPUTE", actor: "Imran Q.", authorisation: "role:moderator@c1", target: "case D-014", outcome: "SUCCESS", summary: "Asked the borrower a question, 72 h deadline", prev: "OPEN", next: "AWAITING_INFORMATION", reason: null, hash_valid: true, masked: false },
    { id: 1283, source: "event", at: "16 Oct 09:15:02", action: "held_for_review", category: "ASSURANCE", actor: "system", authorisation: "svc:assurance", target: "transaction T-5531", outcome: "SUCCESS", summary: "Held: high_value_low_confidence (R4)", prev: "LOCALITY_CHECKED", next: "HELD_FOR_REVIEW", reason: null, hash_valid: true, masked: false },
    { id: 1282, source: "event", at: "16 Oct 08:00:04", action: "dispute_opened", category: "DISPUTE", actor: "system", authorisation: "svc:scheduler", target: "transaction T-5470", outcome: "SUCCESS", summary: "Overdue escalation after 2 reminders (job overdue_escalation)", prev: "ACTIVE", next: "DISPUTED", reason: null, hash_valid: true, masked: false },
    { id: 1281, source: "audit_log", at: "15 Oct 21:03:44", action: "membership_decided", category: "MEMBERSHIP", actor: "Rabia S.", authorisation: "role:moderator@c1", target: "membership T•••q M.", outcome: "SUCCESS", summary: "Approved", prev: "PENDING", next: "APPROVED", reason: "Inside the boundary and the invitation is valid", hash_valid: true, masked: true },
    { id: 1280, source: "event", at: "15 Oct 18:27:10", action: "dispute_opened", category: "DISPUTE", actor: "H•••a A.", authorisation: "party:lender", target: "transaction T-5490", outcome: "SUCCESS", summary: "Dispute: DAMAGE", prev: "RETURN_INITIATED", next: "DISPUTED", reason: null, hash_valid: true, masked: true },
    { id: 1279, source: "audit_log", at: "15 Oct 14:02:51", action: "reject_decide_case", category: "DISPUTE", actor: "U•••n T.", authorisation: "member", target: "case D-012", outcome: "REJECTED", summary: "Refused: a party cannot decide its own case", prev: null, next: null, reason: null, hash_valid: true, masked: true },
    { id: 1278, source: "event", at: "15 Oct 12:55:31", action: "request_declined", category: "OTHER", actor: "system", authorisation: "svc:lifecycle", target: "transaction T-5513", outcome: "SUCCESS", summary: "Declined: dates taken (overlap constraint)", prev: "ASSESSED", next: "DECLINED", reason: null, hash_valid: true, masked: false },
    { id: 1277, source: "event", at: "14 Oct 20:00:00", action: "no_show", category: "OTHER", actor: "system", authorisation: "svc:scheduler", target: "transaction T-5466", outcome: "SUCCESS", summary: "No handover within the 24 h grace period", prev: "ACCEPTED", next: "NO_SHOW", reason: null, hash_valid: true, masked: false },
    { id: 1276, source: "audit_log", at: "13 Oct 16:20:09", action: "audit_viewed", category: "OTHER", actor: "Saad A.", authorisation: "role:admin", target: "audit log", outcome: "SUCCESS", summary: "Viewed with filter: category DISPUTE", prev: null, next: null, reason: null, hash_valid: true, masked: false }
  ],
  /* AuditConcentrationOut: at least 3 decisions and 60% of a moderator's decisions in 90 days */
  concentration: [{ moderator: "Imran Q.", member: "H•••a A.", decisions: 3, share: 0.75 }],

  /* POST /internal/jobs/run -> JobReportOut (scheduler_b13; idempotent, locked, retried) */
  jobs: [
    ["no_show", "No-show", "Accepted, no handover within 24 h of the start", 1, 14, 0],
    ["request_expiry", "Request expiry", "No reply within 72 h, or 72 h after a counter-offer", 2, 9, 0],
    ["handover_reminder", "Handover reminder", "Before an accepted handover", 3, 6, 0],
    ["return_reminder", "Return reminder", "24 h before the due date, and on the day to the lender", 4, 11, 0],
    ["overdue_escalation", "Overdue escalation", "Opens a dispute 72 h after the due date, after 2 reminders", 1, 5, 0],
    ["confirmation_reminder", "Confirmation reminder", "The other party hasn't confirmed within 24 h", 2, 7, 0],
    ["information_deadline", "Information deadline", "A party didn't reply to a moderator in 72 h", 0, 3, 0],
    ["listing_expiry", "Listing expiry", "Listings expire after 60 days", 1, 41, 0],
    ["embedding_backfill", "Search index backfill", "Meaning-based search for new or edited listings", 3, 0, 1]
  ],
  reports: [
    { id: "R-41", what: "Forum post", t: "“Selling cheap gold, DM me”", why: "Spam · suspicious link", by: "Automatic flag + 3 members", prio: "high" },
    { id: "R-40", what: "Comment", t: "Mixed Urdu/English reply in DIY thread", why: "Uncertain language, sent to a person", by: "Automatic flag", prio: "low" },
    { id: "R-39", what: "User", t: "Repeated no-shows by one account", why: "Reported by 2 lenders", by: "Members", prio: "med" }
  ],
};
