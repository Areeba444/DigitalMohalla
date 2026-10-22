"""Generates deployment_diagram.drawio (design step A13, provisional deployment diagram).

Sources: Iteration 1 plan (CI/CD section, B0, demo fallback), NFR-D-02 to D-05, NFR-S-01, NFR-PR-01,
Architecture_Design.md (modular monolith, REST /api/v1, /health), decision D17.
Run: python 04_deployment/generate_deployment.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

INK = "#1F2D3A"
NODE = ("shape=cube;whiteSpace=wrap;html=1;size=12;darkOpacity=0.04;darkOpacity2=0.08;align=left;verticalAlign=top;"
        "spacingLeft=10;spacingTop=14;fontSize=12;strokeColor=#46535F;fontColor=#1F2D3A;")
ENV = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fontSize=11.5;"
       "strokeColor=#5B6B7A;fontColor=#1F2D3A;")
ART = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;spacingRight=22;"
       "fontSize=10.5;fillColor=#FFFFFF;strokeColor=#6A7A8A;fontColor=#1F2D3A;")
DOC_ICON = "shape=note;size=5;html=1;fillColor=#FFFFFF;strokeColor=#6A7A8A;"
COMMENT = ("shape=note;size=12;whiteSpace=wrap;html=1;align=left;verticalAlign=top;fontSize=10.5;spacingLeft=6;"
           "spacingTop=2;")
# communication paths are associations (no arrowheads); internal-network paths dashed
LINK = EDGE_BASE + "endArrow=none;strokeColor=#2F4F6F;strokeWidth=1.4;"
INTERNAL = EDGE_BASE + "endArrow=none;strokeColor=#2E5E1E;strokeWidth=1.4;dashed=1;"


def artifact(d, label, x, y, w, h):
    """UML artifact: rectangle with the keyword and a document icon in the top-right corner."""
    a = d.node(label, x, y, w, h, ART)
    d.node("", x + w - 18, y + 6, 11, 14, DOC_ICON, check=False)
    return a


def st(fill):
    return f"fillColor={fill};"


def build():
    d = Diagram("Deployment diagram (A13)", 1840, 1160)
    d.text("<b>Digital Mohalla &#8212; deployment diagram, iteration 1 (provisional)</b> (design step A13; "
           "decision D17; target confirmed by Student 3 by D-14)", 30, 14, 1500, 24, size=16, check=False)
    d.text("UML 2.5 deployment notation: 3-D box = node (&#171;device&#187; or &#171;cloud service&#187;); "
           "plain box = &#171;executionEnvironment&#187; / &#171;container&#187;; box with document icon = "
           "&#171;artifact&#187;; folded note = comment; line = communication path (association) with protocol and "
           "port, dashed inside the Docker network. Items marked TBC are confirmed at the D-14 / D-15 gates.",
           30, 42, 1700, 20, size=11, color="#4A5560", check=False)

    # ---------------------------------------------------------------- clients
    phone = d.node("&#171;device&#187;<br><b>Mobile phone</b> (Android / iOS) [*]: residents, lenders, "
                   "moderators and admins", 30, 110, 350, 260, NODE + st("#EAF2FB"))
    d.mark_container(phone, pass_through=True)
    rn = d.node("&#171;executionEnvironment&#187;<br><b>React Native / Expo runtime</b> (NFR-D-05)",
                50, 180, 310, 170, ENV + st("#F7FAFE"))
    d.mark_container(rn, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>digital-mohalla-app</b> (one app, screens by role)<br>lender W1&#8211;W2, "
           "handover and return W3a&#8211;W4, dispute W5, moderator W6&#8211;W7 (13_wireframes); EAS build or Expo Go",
             66, 230, 278, 104)

    lap = d.node("&#171;device&#187;<br><b>Team laptop: demo fallback</b>", 30, 430, 350, 210, NODE + st("#F1F1F1"))
    d.mark_container(lap, pass_through=True)
    d.node("&#171;executionEnvironment&#187; <b>Docker Compose (local)</b><br>same <i>docker-compose.yml</i> and images as "
           "production, seed-reset script, synthetic users labelled synthetic. Used if the network fails during the "
           "demo; a local run is still live (plan, demo script).", 50, 488, 310, 132, ENV + st("#FAFAFA"))

    # ---------------------------------------------------------------- AWS
    aws = d.node("<b>AWS</b> &#8212; one region (nearest to the pilot, TBC)", 560, 70, 700, 1060,
                 "rounded=1;arcSize=2;dashed=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=10;"
                 "spacingTop=6;fontSize=12;fillColor=#FFF9F0;strokeColor=#C77700;fontColor=#8A4B12;")
    d.mark_container(aws, pass_through=True)
    ec2 = d.node("&#171;device&#187;<br><b>EC2 instance</b>, Ubuntu 24.04 LTS (size TBC, e.g. 2 vCPU / 2 GB)",
                 585, 110, 650, 830, NODE + st("#FFFFFF"))
    d.mark_container(ec2, pass_through=True)
    dock = d.node("&#171;executionEnvironment&#187;<br><b>Docker Engine + Docker Compose</b> "
                  "(<i>infra/docker-compose.yml</i>; one internal network)", 605, 170, 610, 620, ENV + st("#F4F8FB"))
    d.mark_container(dock, pass_through=True)
    proxy = d.node("&#171;container&#187; <b>proxy</b>: TLS reverse proxy (Caddy or Nginx)<br>"
                   "terminates HTTPS :443 (NFR-S-01); routes <i>/api/v1</i> to <i>api</i>; serves no other content; "
                   "adds no logging of request bodies", 625, 225, 570, 92, ENV + st("#FFFFFF"))
    api = d.node("&#171;container&#187; <b>api</b>: Python 3.12, FastAPI + Uvicorn (modular monolith, A8)<br>"
                 "&#171;artifact&#187; <i>ghcr.io/&lt;org&gt;/dm-api:&lt;commit-sha&gt;</i><br>"
                 "&#8226; Module 1 accounts and locality, Module 3 borrowing lifecycle, Module 5 assurance engine "
                 "(S2 estimation and policy, S1 indirect trust), Module 9 moderation and audit, Module 7 notify() stub<br>"
                 "&#8226; &#171;artifact&#187; <i>Assurance_Engine_Config_Draft.json</i> (config_version stored on every "
                 "assessment, NFR-D-01)<br>"
                 "&#8226; &#171;artifact&#187; migrations from <i>schema.sql</i> v2.3, run by CD before start-up<br>"
                 "&#8226; privacy filter on every response and log line (NFR-PR-01, NFR-S-07)<br>"
                 "&#8226; <i>GET /health</i> for the CD smoke test (NFR-D-04)", 625, 375, 570, 220, ENV + st("#FFFFFF"))
    db = d.node("&#171;container&#187; <b>db</b>: PostgreSQL 16 with <i>btree_gist</i> (ADR-0002)<br>"
                "&#171;artifact&#187; schema <i>dm</i>: event store, projections, bookings (EXCLUDE), assessments, cases, "
                "audit log<br>volume <i>pgdata</i>; port 5432 on the internal network only; nightly <i>pg_dump</i> "
                "(target TBC)", 625, 655, 570, 115, ENV + st("#FFFFFF"))
    d.node("&#171;volume&#187; <b>attachments</b>: photos and documents, EXIF location stripped before storage "
           "(NFR-PR-01); a host volume in iteration 1, an S3 bucket TBC", 605, 806, 610, 50, ENV + st("#FFFFFF"))
    d.node("<b>Security group</b>: inbound 443 from anywhere; 22 only from the GitHub Actions deploy key and the "
           "team; 5432 never public. Secrets come from GitHub Environments into an <i>.env</i> file, never the repo.",
           605, 868, 610, 56, COMMENT + "fillColor=#FFF3E0;strokeColor=#C77700;")
    d.text("No coordinates, addresses or CNIC fields exist in any container or volume (schema privacy scan, test "
           "suite 14). Notifications are an in-process stub in iteration 1 (no e-mail or push service).",
           585, 958, 660, 50, size=10.5, color="#8A4B12", check=False)

    # ---------------------------------------------------------------- GitHub
    gh = d.node("&#171;cloud service&#187;<br><b>GitHub</b>", 1420, 100, 380, 440, NODE + st("#F3EEF9"))
    d.mark_container(gh, pass_through=True)
    act = d.node("&#171;executionEnvironment&#187; <b>GitHub Actions runner</b><br>"
                 "&#171;artifact&#187; <i>ci.yml</i> (every PR and push): ruff, eslint, mypy, bandit, pip-audit, "
                 "pytest with coverage, integration tests on a Postgres service container, scenario suite, frontend "
                 "build, JUnit and coverage reports<br>"
                 "&#171;artifact&#187; <i>cd.yml</i> (push to main): build and push images, deploy over SSH, smoke "
                 "test, roll back to the previous tag on failure", 1440, 152, 340, 210, ENV + st("#FFFFFF"))
    d.mark_container(act, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>repository</b><br>backend/, frontend/, infra/, docs/ (this design folder)<br>"
           "protected main and develop; tags v0.1.0-mid1, design-v1.0, schema-v1", 1440, 384, 250, 140)
    ghcr = d.node("&#171;cloud service&#187;<br><b>GitHub Container Registry (GHCR)</b><br>"
                  "&#171;artifact&#187; dm-api:&lt;sha&gt;, dm-proxy:&lt;sha&gt;<br>previous tag kept for rollback",
                  1420, 620, 380, 160, NODE + st("#F3EEF9"))
    d.node("<b>GitHub Environments</b>: SSH deploy key, database password, any API keys. The handbook forbids "
           "committing keys; Dependabot and pre-commit hooks guard the repo.", 1420, 820, 380, 80,
           COMMENT + "fillColor=#F7F3FB;strokeColor=#7A5C99;")

    # ---------------------------------------------------------------- communication paths
    d.edge(phone, proxy, "HTTPS :443<br>REST /api/v1 (JSON)", style=LINK, exit=(1, 0.5), entry=(0, 0.25),
           points=[(470, 240), (470, 248)], label_x=-0.45)
    d.edge(proxy, api, "HTTP :8000 (internal network)", style=INTERNAL, exit=(0.5, 1), entry=(0.5, 0), label_dx=0)
    d.edge(api, db, "SQL / TCP :5432 (internal only)", style=INTERNAL, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(act, ec2, "SSH :22<br>pull, migrate, up -d", style=LINK, exit=(0, 0.05), entry=(1, 0.0633))
    d.edge(act, proxy, "HTTPS smoke test<br>/health + one request", style=LINK, exit=(0, 0.6), entry=(1, 0.5761),
           label_x=-0.55)
    d.edge(act, ghcr, "docker push", style=LINK, exit=(1, 0.8), entry=(0.9868, 0), points=[(1795, 320), (1795, 620)])
    d.edge(ec2, ghcr, "docker pull<br>(HTTPS)", style=LINK, exit=(1, 0.7), entry=(0, 0.4438))

    # ---------------------------------------------------------------- notes
    d.node("", 30, 940, 520, 200, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    d.text("<b>Why this deployment</b><br>&#8226; One environment and one host are enough to show real CD for Mid-1 "
           "(plan, CI/CD); a staging environment can be added later.<br>&#8226; The backend is one FastAPI process "
           "(modular monolith, A8), so one api container serves every module; module boundaries stay code "
           "interfaces.<br>&#8226; PostgreSQL is required, not optional: the overlap constraint needs "
           "<i>btree_gist</i> (ADR-0002).<br>&#8226; Rollback = redeploy the previous image tag after a failed smoke "
           "test (NFR-D-03).<br>&#8226; Traceability: NFR-D-02 (clean install from the compose file), NFR-D-03, "
           "NFR-D-04, NFR-D-05, NFR-S-01, NFR-PR-01, NFR-S-07.<br>Rationale and open items: "
           "<i>Deployment_Design.md</i>.", 40, 948, 500, 185, size=10.5, check=False)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "deployment_diagram.drawio"))
