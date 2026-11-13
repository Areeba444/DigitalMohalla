"""Generates the iteration 2 system sequence diagrams SSD-A3, SSD-A4 and SSD-D1 (DA-12, Student 3).

    python generate_ssd_iteration2.py   ->  ssd_diagrams.drawio  (all seven SSDs: four of iteration 1, these three)

Same convention as ssd_diagrams.drawio (UML 2.5.1 sequence notation, SSD after Larman): the system is one black
box, ":Digital Mohalla"; system events are solid arrows with numbered operations, results are dashed; alt / opt
fragments carry the use-case extensions. Each page states the FRs it realises and a short rationale.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import EDGE_BASE, Diagram, save_pages  # noqa: E402

ACT_X, SYS_X, TOP, HEAD = 120, 560, 150, 56
SYNC = EDGE_BASE + "endArrow=block;endFill=1;strokeColor=#1D1D1D;fontSize=10.5;"
RET = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;fontColor=#33404D;fontSize=10.5;"
FAIL = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#B00020;fontColor=#B00020;fontSize=10.5;"
INFO = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;"
        "fillColor=#F7F9FC;strokeColor=#9AA5B1;fontSize=10.5;fontColor=#1D1D1D;")
FRAME = ("shape=umlFrame;whiteSpace=wrap;html=1;width=46;height=22;boundedLbl=1;verticalAlign=middle;align=left;"
         "spacingLeft=4;fontStyle=1;fontSize=11;fillColor=none;strokeColor=#5F6B76;")


class SSD:
    def __init__(self, name, title, frs, rationale, actor, height):
        self.d = Diagram(name, 1100, height)
        self.bottom = height - 40
        d = self.d
        d.node(f"<b>{title}</b><br><b>Document:</b> behaviour design, iteration 2, DA-12 (Student 3), v1.0 draft<br>"
               f"<b>FRs realised:</b> {frs}<br><b>Rationale:</b> {rationale}", 30, 12, 1040, 92, INFO,
               check=False)
        self.lifelines = [d.node(actor, ACT_X - 40, TOP, 80, self.bottom - TOP, "shape=umlLifeline;participant=umlActor;"
               "perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;verticalAlign=top;spacingTop=36;"
               f"size={HEAD - 14};fontSize=11;fontStyle=1;", check=False),
                          d.node(":Digital Mohalla", SYS_X - 90, TOP, 180, self.bottom - TOP, "shape=umlLifeline;"
               "perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;collapsible=0;"
               f"size={HEAD};fontSize=12;fontStyle=1;fillColor=#F2F2F2;strokeColor=#46535F;", check=False)]
        self.y, self.n = TOP + HEAD + 36, 0

    def call(self, text, ref):
        self.n += 1
        self.d.edge(None, None, f"{self.n}: {text}", style=SYNC, src_pt=(ACT_X + 5, self.y),
                    tgt_pt=(SYS_X - 5, self.y), label_dy=-9)
        self._ref(ref)
        self.y += 30

    def reply(self, text, ref, fail=False):
        self.d.edge(None, None, text, style=FAIL if fail else RET, src_pt=(SYS_X - 5, self.y),
                    tgt_pt=(ACT_X + 5, self.y), label_dy=-9)
        self._ref(ref)
        self.y += 30

    def _ref(self, ref):
        self.d.text(ref, SYS_X + 110, self.y - 16, 330, 18, size=10, color="#5F6B76", check=False)

    def fragment(self, op, parts):
        """parts: list of (guard, [(kind, text, ref), ...]); kind is 'call', 'reply' or 'fail'."""
        y0 = self.y - 10
        self.y += 26
        guards = []
        for k, (guard, steps) in enumerate(parts):
            if k:
                self.y += 14
            guards.append((self.y, guard))
            self.y += 40
            for kind, text, ref in steps:
                if kind == "call":
                    self.call(text, ref)
                else:
                    self.reply(text, ref, fail=(kind == "fail"))
        y1 = self.y
        d = self.d
        d.node(op, 60, y0, 980, y1 - y0, FRAME, check=False)
        for k, (gy, text) in enumerate(guards):
            if k:
                d.edge(None, None, "", style="endArrow=none;dashed=1;html=1;strokeColor=#5F6B76;",
                       src_pt=(60, gy - 8), tgt_pt=(1040, gy - 8), check=False)
            d.text(f"[{text}]", 116 if k == 0 else 70, gy - 6 if k == 0 else gy - 4, 600, 18, size=10.5,
                   color="#33404D", check=False)
        self.y += 24

    def finish(self) -> Diagram:
        """Size the lifelines and the page to the content."""
        end = self.y + 20
        for lid in self.lifelines:
            self.d.by_id[lid]["h"] = end - TOP
        self.d.height = end + 30
        return self.d


def ssd_a3() -> Diagram:
    s = SSD("SSD-A3 Request community membership", "SSD-A3: Select neighbourhood and request community membership",
            "FR-A-06, FR-A-07, FR-A-08, FR-A-09, NFR-PR-01.",
            "The member sees only coarse outcomes. One GPS fix and the invitation code are checked inside the "
            "system and discarded, so no coordinate ever appears in a reply, a log or a stored row (A11, D13). "
            "Every uncertain outcome still creates a request for a moderator; nothing is rejected automatically.",
            "Member", 980)
    s.call("openJoinCommunity()", "UC-A3 step 1")
    s.reply("communities by name or code (nearby if coarse location is allowed)", "step 1")
    s.call("selectCommunity(communityId)", "step 2")
    s.reply("rules, verification methods", "step 2")
    s.call("checkLocality(oneCoarseFix?, invitationCode)", "step 3 (A11)")
    s.fragment("alt", [
        ("fix inside the community and a valid invitation", [("reply", "outcome VERIFIED", "step 3")]),
        ("permission refused, boundary home or weak fix (3a, 3b)",
         [("reply", "outcome INCONCLUSIVE: a moderator will decide", "ext 3a, 3b; ES-10")]),
        ("fix outside the community or a mock location (3c)",
         [("reply", "outcome CONFLICTING: a moderator will decide", "ext 3c; ES-09")]),
        ("invitation invalid, expired, used or for another community (3d)",
         [("fail", "error: check the code and try again", "ext 3d")]),
    ])
    s.call("submitJoinRequest(communityId)", "step 4")
    s.fragment("alt", [
        ("no live membership in this community", [("reply", "request PENDING; moderators notified (M01)", "step 4")]),
        ("a request or membership already exists (4b)",
         [("fail", "blocked: current status shown", "ext 4b")]),
    ])
    return s.finish()


def ssd_a4() -> Diagram:
    s = SSD("SSD-A4 Approve or reject membership", "SSD-A4: Approve or reject a membership request",
            "FR-A-08, FR-A-10, FR-A-11, NFR-S-03.",
            "The moderator decides with the coarse locality outcome and any flags as evidence, never raw location. "
            "A reason is required for every decision, and the system applies a decision only while the request is "
            "still undecided, so two moderators cannot both apply one (membership state machine M02 to M08).",
            "Moderator", 1000)
    s.call("openMembershipQueue()", "UC-A4 step 1")
    s.reply("pending requests for the moderator's own community", "step 1")
    s.call("openRequest(membershipId)", "step 2")
    s.reply("minimal profile, locality outcome, duplicate and mismatch flags", "step 2")
    s.fragment("opt", [
        ("evidence insufficient (2a)", [
            ("call", "requestInformation(membershipId, question)", "ext 2a"),
            ("reply", "AWAITING_INFORMATION; applicant notified (M02)", "ext 2a")]),
    ])
    s.call("decide(membershipId, APPROVE | REJECT, reason)", "steps 3, 4")
    s.fragment("alt", [
        ("authorised, reason given, request still undecided",
         [("reply", "APPROVED (M04) or REJECTED (M05); applicant notified; audit entry", "steps 3, 4")]),
        ("reason missing (3a)", [("fail", "decision blocked: a reason is required", "ext 3a")]),
        ("another moderator decided first, or the applicant withdrew (4a, 4c)",
         [("fail", "current status shown; nothing applied", "ext 4a, 4c")]),
        ("not a moderator of this community (4b)", [("fail", "denied and logged", "ext 4b; NFR-S-03")]),
    ])
    return s.finish()


def ssd_d1() -> Diagram:
    s = SSD("SSD-D1 Submit review", "SSD-D1: Submit a review after a completed loan",
            "FR-T-09, FR-B-15, NFR-U-01.",
            "Only the two parties to a COMPLETED loan may review, once each, inside a short edit window. "
            "Suspected retaliation and near-identical text are flagged inside the system and handled by the "
            "manipulation checks (D19); the reviewer is not told, so nobody is accused, and reviews never enter "
            "the trust estimate, which uses verified loan outcomes only.",
            "Member", 860)
    s.call("openReview(transactionId)", "UC-D1")
    s.fragment("alt", [
        ("party to this COMPLETED loan, not yet reviewed",
         [("reply", "review form: ratings per dimension, comment", "FR-T-09")]),
        ("not a party, loan not completed, or already reviewed",
         [("fail", "review not available", "FR-T-09")]),
    ])
    s.call("submitReview(transactionId, ratings, comment?)", "FR-T-09")
    s.reply("review recorded (flags, if any, are set internally)", "FR-T-09; D19")
    s.fragment("opt", [
        ("within the edit window", [
            ("call", "editReview(reviewId, ratings, comment?)", "FR-T-09"),
            ("reply", "review updated", "FR-T-09")]),
    ])
    return s.finish()


def save_all(path):
    """One SSD file for the system: the four iteration 1 pages (hand-drawn, kept as drawn in
    archive_v1/ssd_diagrams_iteration1.drawio) followed by the iteration 2 pages generated here."""
    import xml.etree.ElementTree as ET
    tmp = path + ".tmp"
    save_pages(tmp, [ssd_a3(), ssd_a4(), ssd_d1()])
    new = ET.parse(tmp)
    os.remove(tmp)
    root = new.getroot()
    old = ET.parse(os.path.join(HERE, "archive_v1", "ssd_diagrams_iteration1.drawio")).getroot().findall("diagram")
    for i, dg in enumerate(old):
        root.insert(i, dg)
    root.set("pages", str(len(root.findall("diagram"))))
    ET.indent(root, space="  ")
    new.write(path, encoding="utf-8")
    print(f"{path}: {len(root.findall('diagram'))} pages (4 from iteration 1, 3 from iteration 2)")


if __name__ == "__main__":
    save_all(os.path.join(HERE, "ssd_diagrams.drawio"))
