"""Generates deployment_diagram.drawio: the deployment diagram as built in iteration 1 (v1.0).

The provisional Part A design (one AWS EC2 host with Docker Compose and GHCR, design step A13, v0.9/0.10)
is kept in archive_v1/ (deployment_diagram_v0.9_partA_provisional.drawio and its generator).

Sources (as built, 14 October 2026): render.yaml, backend/Dockerfile, .github/workflows/ci.yml,
infra/deploy/README.md, backend/app/infra/db/session.py, backend/app/main.py, backend/config/engine.json,
backend/alembic/versions/0001_schema_v2_3.py. Requirements: NFR-S-01, NFR-D-03, NFR-D-04, NFR-PR-01, NFR-S-07.
Run: python 04_deployment/generate_deployment.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

NODE = ("shape=cube;whiteSpace=wrap;html=1;size=14;darkOpacity=0.04;darkOpacity2=0.08;align=left;verticalAlign=top;"
        "spacingLeft=10;spacingTop=16;fontSize=15;strokeColor=#46535F;fontColor=#1F2D3A;")
ENV = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fontSize=14;"
       "strokeColor=#5B6B7A;fontColor=#1F2D3A;")
ART = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;spacingRight=24;"
       "fontSize=13;fillColor=#FFFFFF;strokeColor=#6A7A8A;fontColor=#1F2D3A;")
DOC_ICON = "shape=note;size=5;html=1;fillColor=#FFFFFF;strokeColor=#6A7A8A;"
COMMENT = ("shape=note;size=14;whiteSpace=wrap;html=1;align=left;verticalAlign=top;fontSize=13;spacingLeft=8;"
           "spacingTop=4;spacingRight=10;")
PLANNED = ("shape=note;size=14;whiteSpace=wrap;html=1;align=left;verticalAlign=top;fontSize=13;spacingLeft=8;"
           "spacingTop=4;spacingRight=10;dashed=1;fillColor=#F4F4F4;strokeColor=#7A7A7A;fontColor=#3A3A3A;")
# communication paths are associations (no arrowheads), labelled with protocol and port
LINK = EDGE_BASE + "endArrow=none;strokeColor=#2F4F6F;strokeWidth=1.6;fontSize=13;"
# deployment by Render from GitHub: a dependency (dashed, open arrow) labelled with the trigger
DEPLOY = EDGE_BASE + "endArrow=open;endSize=12;dashed=1;strokeColor=#5B3E86;strokeWidth=1.6;fontSize=13;"


def artifact(d, label, x, y, w, h):
    """UML artifact: rectangle with the keyword and a document icon in the top-right corner."""
    a = d.node(label, x, y, w, h, ART)
    d.node("", x + w - 19, y + 7, 12, 15, DOC_ICON, check=False)
    return a


def st(fill):
    return f"fillColor={fill};"


def build():
    d = Diagram("Deployment diagram (as built)", 1240, 1290)
    d.text("<b>Digital Mohalla &#8212; deployment diagram, iteration 1, as built</b> (v1.0, 14 October 2026; "
           "replaces the provisional Part A design A13)", 30, 12, 1180, 26, size=18, check=False)
    d.text("UML 2.5 deployment notation: 3-D box = node (&#171;device&#187; or &#171;cloud service&#187;); plain box = "
           "&#171;executionEnvironment&#187;; box with document icon = &#171;artifact&#187;; folded note = comment; "
           "solid line = communication path with protocol and port; dashed arrow = deployment trigger; "
           "grey dashed note = planned, not built.", 30, 44, 1180, 40, size=13, color="#4A5560", check=False)

    # ---------------------------------------------------------------- clients
    phone = d.node("&#171;device&#187;<br><b>Android phone</b> [*]: residents, lenders, moderators", 30, 100, 380, 250,
                   NODE + st("#EAF2FB"))
    d.mark_container(phone, pass_through=True)
    rn = d.node("&#171;executionEnvironment&#187;<br><b>Expo runtime</b> (Expo Go / development build)",
                50, 168, 340, 166, ENV + st("#F7FAFE"))
    d.mark_container(rn, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>digital-mohalla-app</b><br>one app, screens by role (W1&#8211;W7); "
                "API address set at build time", 66, 226, 308, 92)

    browser = d.node("&#171;device&#187;<br><b>Computer or phone with a web browser</b> [*]", 440, 100, 370, 250,
                     NODE + st("#EAF2FB"))
    d.mark_container(browser, pass_through=True)
    benv = d.node("&#171;executionEnvironment&#187;<br><b>Web browser</b>", 460, 168, 330, 166, ENV + st("#F7FAFE"))
    d.mark_container(benv, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>web app</b><br>the same Expo app, exported for the web and loaded from "
                "the static site", 476, 226, 298, 92)

    # ---------------------------------------------------------------- GitHub
    gh = d.node("&#171;cloud service&#187;<br><b>GitHub</b>", 850, 100, 360, 430, NODE + st("#F3EEF9"))
    d.mark_container(gh, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>repository</b> Areeba444/DigitalMohalla<br><i>main</i> = deployed, "
                "<i>develop</i> = integration; <i>render.yaml</i>", 870, 162, 320, 100)
    act = d.node("&#171;executionEnvironment&#187; <b>GitHub Actions runner</b><br>&#171;artifact&#187; <i>ci.yml</i> "
                 "on every push and pull request: Backend (ruff, mypy, bandit, pytest on a PostgreSQL 16 service "
                 "container), Frontend (tsc, ESLint, Jest), API client in sync", 870, 280, 320, 230, ENV + st("#FFFFFF"))
    d.mark_container(act, pass_through=True)

    # ---------------------------------------------------------------- Render
    render = d.node("&#171;cloud service&#187;<br><b>Render</b>", 30, 430, 780, 500, NODE + st("#FFF9F0"))
    d.mark_container(render, pass_through=True)
    d.text("free plan, region Singapore;<br>HTTPS :443 ends at Render's edge<br>(NFR-S-01)", 232, 438, 226, 58,
           size=13, color="#8A4B12", check=False)
    web = d.node("&#171;executionEnvironment&#187;<br><b>Web service</b> <i>digitalmohalla-api</i>: Docker "
                 "container (sleeps after about 15 min idle)", 50, 500, 360, 410, ENV + st("#FFFFFF"))
    d.mark_container(web, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>API image</b> (<i>backend/Dockerfile</i>)<br>Python 3.12, FastAPI + "
                "Uvicorn, modular monolith (Modules 1, 3, 5, 9)<br>start-up: <i>alembic upgrade head</i>, then "
                "Uvicorn<br>REST <i>/api/v1</i>; <i>GET /health</i>", 66, 578, 328, 162)
    artifact(d, "&#171;artifact&#187; <i>config/engine.json</i><br>config_version 1.3.0-iteration1-draft",
             66, 752, 328, 62)
    d.node("Secrets in Render settings: <i>DATABASE_URL</i>, <i>JWT_SECRET</i> (generated); "
           "<i>CORS_ORIGINS</i> = the web app only", 66, 826, 328, 72, COMMENT + "fillColor=#FFF3E0;strokeColor=#C77700;")

    static = d.node("&#171;executionEnvironment&#187;<br><b>Static site</b> <i>digitalmohalla-web</i> on "
                    "Render's CDN (does not sleep)", 480, 500, 310, 230, ENV + st("#FFFFFF"))
    d.mark_container(static, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>Expo web export</b> (<i>frontend/dist</i>)<br>every path rewritten to "
                "<i>index.html</i>; API address built in", 496, 578, 278, 136)
    d.node("Render builds <i>main</i> only after the CI checks pass, and only when <i>backend/</i> or "
           "<i>frontend/</i> changed. A new API version goes live only if <i>/health</i> answers; otherwise the "
           "previous one stays. Rollback: redeploy an earlier deploy (NFR-D-03, NFR-D-04).",
           480, 746, 310, 164, COMMENT + "fillColor=#FFF3E0;strokeColor=#C77700;")

    # ---------------------------------------------------------------- Neon
    neon = d.node("&#171;cloud service&#187;<br><b>Neon</b>", 30, 1010, 780, 250, NODE + st("#EEF7EE"))
    d.mark_container(neon, pass_through=True)
    d.text("free plan, AWS ap-southeast-1 (Singapore), the same region as the API", 250, 1030, 540, 24,
           size=13, color="#2E5E1E", check=False)
    pg = d.node("&#171;executionEnvironment&#187; <b>PostgreSQL 16</b> with <i>btree_gist</i>; direct endpoint "
                "(not the pooler); suspends when idle, wakes on connect", 50, 1074, 740, 170, ENV + st("#FFFFFF"))
    d.mark_container(pg, pass_through=True)
    artifact(d, "&#171;artifact&#187; <b>schema <i>dm</i></b> v2.3 (Alembic migration 0001): event store "
                "(append-only, hash-chained), projections, bookings (EXCLUDE), assessments, cases, moderator "
                "decisions, audit log. No coordinates, addresses or CNIC (suite 14).", 66, 1132, 708, 96)

    # ---------------------------------------------------------------- right column
    lap = d.node("&#171;device&#187;<br><b>Team laptop</b>: development and demo fallback", 850, 620, 360, 230,
                 NODE + st("#F1F1F1"))
    d.mark_container(lap, pass_through=True)
    d.node("&#171;executionEnvironment&#187; <b>local run</b><br>PostgreSQL 16, Uvicorn API, Expo dev server; "
           "synthetic seed data. Used if the hosted service is unavailable during the demo.",
           870, 688, 320, 144, ENV + st("#FAFAFA"))
    d.node("<b>Planned, not built yet</b> (Iteration 2): Android release build with the API address (EAS, "
           "TC-73); post-deploy smoke test (TC-91); rehearsed rollback; a paid tier or small host for the pilot "
           "if free-tier sleep affects users.", 850, 878, 360, 160, PLANNED)
    d.node("<b>Why</b>: managed services give HTTPS, TLS to the database, health-gated deploys and rollback "
           "without server administration. Serves NFR-S-01, NFR-D-03, NFR-D-04, NFR-PR-01, NFR-S-07. "
           "The Part A design (one AWS host) is kept for reference.", 850, 1062, 360, 198,
           COMMENT + "fillColor=#FFFFFF;strokeColor=#B0BAC4;")

    # ---------------------------------------------------------------- communication paths
    d.edge(phone, web, "HTTPS :443<br>REST /api/v1 (JSON)", style=LINK, exit=(0.5, 1), entry=(0.4722, 0),
           label_x=-0.55)
    d.edge(browser, static, "HTTPS :443<br>static files", style=LINK, exit=(0.6, 1), entry=(0.5871, 0),
           label_x=-0.55)
    d.edge(browser, web, "HTTPS :443<br>REST /api/v1<br>(CORS)", style=LINK, exit=(0.0784, 1), entry=(1, 0.1463),
           points=[(469, 560)], label_x=-0.62)
    d.edge(web, pg, "PostgreSQL protocol over TLS :5432<br>(sslmode=require)", style=LINK, exit=(0.5, 1),
           entry=(0.2432, 0), label_x=0.05)
    d.edge(gh, render, "push to main, CI passed:<br>build and deploy", style=DEPLOY, exit=(0.5, 1),
           entry=(1, 0.26), points=[(1030, 560)], label_x=0.35)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "deployment_diagram.drawio"))
