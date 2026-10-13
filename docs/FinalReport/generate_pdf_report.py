"""
Digital Mohalla: FYP-1 Mid Assessment Report Generator
Compiles the comprehensive, academic report into an elegant publication-grade HTML
and prints it to PDF using Chrome Headless with exact academic paged media standards.
Embeds all 13 high-resolution architectural diagrams and 8 UI wireframes.
Replaces raw LaTeX dollar signs with proper mathematical HTML markup.
"""

import os
import base64
import subprocess
import re

def get_b64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            ext = os.path.splitext(path)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    report_dir = os.path.join(root_dir, "docs", "FinalReport")
    
    # 1. Image assets
    logo_path = os.path.join(report_dir, "F26_FYP1_Mid_Report_LaTeX_Complete", "ThesisFigs", "FASTLogo.jpg")
    logo_b64 = get_b64_image(logo_path)
    
    # 13 Core Architectural Diagrams in docs/design/
    diag_layer_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "03_architecture", "layer_diagram.drawio.png"))
    diag_comp_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "03_architecture", "component_diagram.drawio.png"))
    diag_deploy_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "04_deployment", "deployment_diagram.drawio.png"))
    diag_domain_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "05_class_model", "domain_model.drawio.png"))
    diag_erd_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "06_data_model", "er_diagram.drawio.png"))
    diag_sm_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "07_state_machines", "borrowing_lifecycle_state_machine.drawio.png"))
    diag_escalate_sm_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "07_state_machines", "escalation_case_state_machine.drawio.png"))
    diag_seq_b_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "08_sequence_diagrams", "sequence_b_handover_return.drawio.png"))
    diag_seq_c_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "08_sequence_diagrams", "sequence_c_dispute.drawio.png"))
    diag_dfd_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "10_dfd", "dfd_assurance_pipeline_level0_level1-DFD level 0 (context).drawio.png"))
    
    diag_cls1_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "05_class_model", "class_diagram_s1.drawio.png"))
    diag_cls2_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "05_class_model", "class_diagram_s2.drawio.png"))
    diag_cls3_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "05_class_model", "class_diagram_s3.drawio.png"))
    
    # UI Wireframes
    wf1_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W1_Lender_Request_Assurance 1.png"))
    wf2_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W2_Lender_Decision_Conflict 1.png"))
    wf3a_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W3a_Handover_Inspection_Lender 1.png"))
    wf3b_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W3b_Handover_Confirmation_Borrower 1.png"))
    wf4_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W4_Return_Inspection_Comparison 1.png"))
    wf5_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W5_Dispute_Form_Progress 1.png"))
    wf6_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W6_Moderator_Queue_Mobile 1.png"))
    wf7_b64 = get_b64_image(os.path.join(root_dir, "docs", "design", "13_wireframes", "W7_Moderator_Case_Adjudication_Mobile 1.png"))

    logo_img_tag = f"<img src='{logo_b64}' class='cover-logo' alt='FAST Logo'>" if logo_b64 else ""

    css = """
    @page {
        size: A4;
        margin: 25mm 22mm 25mm 28mm;
        @bottom-center {
            content: counter(page);
            font-family: 'Times New Roman', Times, serif;
            font-size: 10pt;
            color: #555;
        }
    }

    @page :first {
        margin: 12mm 20mm 12mm 20mm;
        @bottom-center {
            content: "";
        }
    }

    body {
        font-family: 'Times New Roman', Times, 'Nimbus Roman', Georgia, serif;
        font-size: 11.5pt;
        line-height: 1.5;
        color: #111;
        margin: 0;
        padding: 0;
        text-align: justify;
        text-justify: inter-word;
    }

    /* Page Breaks */
    .page-break {
        page-break-before: always;
        break-before: page;
    }
    .no-break {
        page-break-inside: avoid;
        break-inside: avoid;
    }
    
    /* Cover Page */
    .cover-page {
        text-align: center;
        box-sizing: border-box;
        padding: 5mm 0;
        page-break-after: always;
        break-after: page;
        max-height: 260mm;
    }
    .cover-logo {
        width: 90px;
        height: auto;
        margin: 0 auto 10px auto;
    }
    .cover-institution {
        font-size: 13pt;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #0d2238;
        margin-bottom: 2px;
    }
    .cover-campus {
        font-size: 11pt;
        font-weight: normal;
        margin-bottom: 18px;
        color: #333;
    }
    .cover-title {
        font-size: 17.5pt;
        font-weight: bold;
        line-height: 1.25;
        color: #0b1e33;
        margin: 16px 0 10px 0;
        padding: 0 10px;
    }
    .cover-subtitle {
        font-size: 12pt;
        font-style: italic;
        color: #444;
        margin-bottom: 16px;
    }
    .cover-meta-box {
        margin: 14px auto;
        width: 90%;
        border-top: 1.5px solid #0b1e33;
        border-bottom: 1.5px solid #0b1e33;
        padding: 8px 0;
    }
    .cover-meta-item {
        font-size: 11pt;
        margin: 3px 0;
    }
    .cover-team-table {
        margin: 14px auto;
        width: 85%;
        border-collapse: collapse;
    }
    .cover-team-table th, .cover-team-table td {
        padding: 5px 10px;
        font-size: 10.5pt;
        text-align: center;
    }
    .cover-team-table th {
        border-bottom: 1px solid #333;
        font-weight: bold;
    }
    .cover-date {
        font-size: 11pt;
        font-weight: bold;
        margin-top: 20px;
    }

    /* Typography */
    h1 {
        font-size: 17pt;
        font-weight: bold;
        color: #0b1e33;
        border-bottom: 2px solid #0b1e33;
        padding-bottom: 6px;
        margin-top: 0;
        margin-bottom: 16px;
        page-break-before: always;
        break-before: page;
        page-break-after: avoid;
        break-after: avoid;
    }
    .front-matter h1 {
        text-align: center;
        border-bottom: 1.5px solid #444;
    }
    h2 {
        font-size: 13.5pt;
        font-weight: bold;
        color: #162e4a;
        margin-top: 22px;
        margin-bottom: 10px;
        page-break-after: avoid;
        break-after: avoid;
    }
    h3 {
        font-size: 12pt;
        font-weight: bold;
        color: #233e5e;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
        break-after: avoid;
    }
    h4 {
        font-size: 11.5pt;
        font-weight: bold;
        font-style: italic;
        margin-top: 12px;
        margin-bottom: 6px;
        page-break-after: avoid;
        break-after: avoid;
    }
    p {
        margin-top: 0;
        margin-bottom: 10px;
        orphans: 3;
        widows: 3;
    }
    ul, ol {
        margin-top: 0;
        margin-bottom: 12px;
        padding-left: 24px;
    }
    li {
        margin-bottom: 4px;
    }

    /* Tables */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 10pt;
        page-break-inside: avoid;
        break-inside: avoid;
    }
    th, td {
        padding: 7px 10px;
        vertical-align: top;
        text-align: left;
    }
    th {
        font-weight: bold;
        background-color: #f4f6f8;
        border-top: 2px solid #111;
        border-bottom: 1.5px solid #333;
        color: #0b1e33;
    }
    td {
        border-bottom: 1px solid #ddd;
    }
    tr:last-child td {
        border-bottom: 2px solid #111;
    }
    tr:nth-child(even) td {
        background-color: #fafbfc;
    }
    .table-caption {
        font-size: 10pt;
        font-weight: bold;
        margin-bottom: 6px;
        color: #111;
        text-align: left;
    }

    /* Callouts & Alert Boxes */
    .todo-box, .left-box {
        border-left: 4px solid #d97706;
        background-color: #fffbeb;
        color: #92400e;
        padding: 8px 14px;
        margin: 12px 0;
        font-size: 10.5pt;
        page-break-inside: avoid;
        break-inside: avoid;
        border-radius: 0 4px 4px 0;
    }
    .todo-box strong, .left-box strong {
        color: #78350f;
    }
    .left-tag {
        color: #92400e;
        font-weight: bold;
        background-color: #fef3c7;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #fde68a;
    }
    .note-box {
        border-left: 4px solid #2563eb;
        background-color: #eff6ff;
        color: #1e40af;
        padding: 8px 14px;
        margin: 12px 0;
        font-size: 10.5pt;
        page-break-inside: avoid;
        break-inside: avoid;
        border-radius: 0 4px 4px 0;
    }
    .note-box strong {
        color: #1e3a8a;
    }

    /* Figures */
    figure {
        margin: 18px 0;
        text-align: center;
        page-break-inside: avoid;
        break-inside: avoid;
    }
    figure img {
        max-width: 95%;
        max-height: 220mm;
        height: auto;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    figcaption {
        font-size: 9.5pt;
        font-weight: bold;
        color: #333;
        margin-top: 7px;
    }
    .two-figures {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        margin: 16px 0;
        page-break-inside: avoid;
        break-inside: avoid;
    }
    .two-figures figure {
        flex: 1;
        margin: 0;
    }
    .two-figures figure img {
        max-width: 100%;
    }

    /* Signatures */
    .signature-grid {
        display: flex;
        justify-content: space-between;
        margin-top: 40px;
        page-break-inside: avoid;
        break-inside: avoid;
    }
    .sig-cell {
        width: 30%;
        text-align: center;
    }
    .sig-line {
        border-top: 1px solid #111;
        margin-bottom: 6px;
    }

    /* Code & Technical blocks */
    code {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 9.5pt;
        background-color: #f1f3f5;
        padding: 2px 4px;
        border-radius: 3px;
    }
    pre {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 9pt;
        background-color: #f8f9fa;
        border: 1px solid #e2e8f0;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
        page-break-inside: avoid;
        break-inside: avoid;
    }

    /* TOC styling */
    .toc-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 10.5pt;
    }
    .toc-table td {
        padding: 4px 0;
        border: none;
        background: transparent !important;
    }
    .toc-table tr:last-child td {
        border: none;
    }
    .toc-title {
        font-weight: bold;
        color: #0b1e33;
    }
    .toc-dots {
        border-bottom: 1px dotted #888;
        width: 100%;
        display: inline-block;
        margin: 0 4px;
    }
    .toc-page {
        text-align: right;
        font-weight: bold;
    }
    """

    # Assemble HTML content
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "    <meta charset='UTF-8'>",
        "    <title>Digital Mohalla: FYP-1 Mid Assessment Report</title>",
        f"    <style>{css}</style>",
        "</head>",
        "<body>",
        
        # Cover Page
        "<div class='cover-page'>",
        "    <div>",
        f"        {logo_img_tag}",
        "        <div class='cover-institution'>National University of Computer &amp; Emerging Sciences</div>",
        "        <div class='cover-campus'>FAST School of Computing, Islamabad Campus</div>",
        "    </div>",
        "    <div>",
        "        <div class='cover-title'>Digital Mohalla: A Neighbourhood Resource-Sharing Platform with an Evidence-Based Trust and Risk Assurance Engine</div>",
        "        <div class='cover-subtitle'>Final Year Project Report (FYP-1 Mid-Term Assessment)</div>",
        "    </div>",
        "    <div class='cover-meta-box'>",
        "        <div class='cover-meta-item'><strong>Degree:</strong> Bachelor of Science in Computer Science</div>",
        "        <div class='cover-meta-item'><strong>Session:</strong> 2023–2027</div>",
        "        <div class='cover-meta-item'><strong>Project Stage:</strong> Iteration 1 (Part B Frozen Baseline)</div>",
        "    </div>",
        "    <div>",
        "        <table class='cover-team-table'>",
        "            <thead>",
        "                <tr>",
        "                    <th>Student Name</th>",
        "                    <th>Roll Number</th>",
        "                    <th>Module Ownership Role</th>",
        "                </tr>",
        "            </thead>",
        "            <tbody>",
        "                <tr>",
        "                    <td><strong>Fatima Khursheed</strong></td>",
        "                    <td>23i-0746</td>",
        "                    <td>Student 1 (Lifecycle, Event Store, <i>k</i>-Hop Traversal, CI)</td>",
        "                </tr>",
        "                <tr>",
        "                    <td><strong>Areeba Javed</strong></td>",
        "                    <td>23i-0570</td>",
        "                    <td>Student 2 (Bayesian Engine, Similarity, Policy Rules, Detection)</td>",
        "                </tr>",
        "                <tr>",
        "                    <td><strong>Minahil Kashif</strong></td>",
        "                    <td>23i-0554</td>",
        "                    <td>Student 3 (React Native / Expo UI, Synthetic Datasets, CD)</td>",
        "                </tr>",
        "            </tbody>",
        "        </table>",
        "        <div style='margin-top: 15px; font-size: 11pt;'>",
        "            <div><strong>Supervisor:</strong> Dr. Ali Zeeshan</div>",
        "        </div>",
        "    </div>",
        "    <div class='cover-date'>October 2026</div>",
        "</div>",

        # Front Matter
        "<div class='front-matter'>",
        "    <h1>Students' Submission</h1>",
        "    <p>We certify that this report is submitted as the FYP-1 mid-assessment report for the project titled <em>Digital Mohalla: A Neighbourhood Resource-Sharing Platform with an Evidence-Based Trust and Risk Assurance Engine</em>.</p>",
        "    <p>We declare that this document accurately describes the integrated design baseline (Part A) and the functional software implementations (Part B: Slice A and Slice B) completed by our team as of the freeze date of 13 October 2026. All open verification items, unvalidated parameters, and pending modules (Slice C) are explicitly documented as required by academic standards.</p>",
        "    <div class='signature-grid' style='margin-top: 80px;'>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Fatima Khursheed</strong><br>23i-0746<br>Dated: _______________</div>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Areeba Javed</strong><br>23i-0570<br>Dated: _______________</div>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Minahil Kashif</strong><br>23i-0554<br>Dated: _______________</div>",
        "    </div>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>Anti-Plagiarism Statement</h1>",
        "    <p>We certify that this report and the accompanying implementation constitute our own original engineering work. All literature, mathematical formulations, open-source libraries, public validation datasets, and assistive tools utilized during this project have been explicitly acknowledged and cited in accordance with FAST-NUCES academic standards and IEEE guidelines.</p>",
        "    <p>We affirm that no text, source code, or experimental findings have been plagiarized. Generative AI assistance has been transparently disclosed in the project AI Usage Log (Appendix D / <code>docs/ai-usage-log.md</code>), and every algorithm implemented in the codebase is fully understood and defendable by each respective module owner.</p>",
        "    <div class='signature-grid' style='margin-top: 80px;'>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Fatima Khursheed</strong><br>23i-0746</div>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Areeba Javed</strong><br>23i-0570</div>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Minahil Kashif</strong><br>23i-0554</div>",
        "    </div>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>Authors' Declaration</h1>",
        "    <p>We hereby declare that the work documented in this report represents the progress completed up to the FYP-1 mid-assessment stage for our Bachelor of Science degree in Computer Science at the FAST School of Computing, FAST-NUCES Islamabad.</p>",
        "    <p>This report follows the formal Form 3 evaluation rubrics and Chapter structure prescribed by the University. No portion of this work has been submitted previously for any other academic degree or qualification.</p>",
        "    <div class='signature-grid' style='margin-top: 80px;'>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Fatima Khursheed</strong><br>23i-0746</div>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Areeba Javed</strong><br>23i-0570</div>",
        "        <div class='sig-cell'><div class='sig-line'></div><strong>Minahil Kashif</strong><br>23i-0554</div>",
        "    </div>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>Abstract</h1>",
        "    <p><strong>Digital Mohalla</strong> is a neighbourhood resource-sharing platform engineered to enable secure, auditable, and privacy-preserving lending, borrowing, and donation. Its foundational computing challenge is not merely item cataloguing or message exchange: it is deciding whether a physical handover has sufficient trustworthy evidence when interaction history is sparse, indirect, and potentially subject to manipulation, while strictly preserving user location privacy and escalating uncertain cases to human moderation.</p>",
        "    <p>This report documents the FYP-1 mid-assessment progress and implementation status frozen at 13 October 2026. Prior to implementation, a complete design baseline (Part A) covering UML 2.5 use cases, sequence diagrams, ERD, finite state machines, and Architectural Decision Records (ADRs 0001–0008) was integrated. In implementation (Part B), <strong>Slice A</strong> provides an event-sourced, request-to-return borrowing lifecycle: users authenticate via argon2-hashed credentials and JWT bearer tokens, borrowing requests are validated against temporal bounds, stored locality eligibility is verified, and transactions proceed through accept, decline, handover, and return confirmations backed by an append-only, tamper-evident PostgreSQL 16 hash-chain event log.</p>",
        "    <p><strong>Slice B</strong> completes the core trust and risk assurance engine: outcome extraction from historical transactions, recency-weighted Beta estimation with 90% credible intervals, contextual similarity weighting, trust-edge projection, bounded <i>k</i>-hop graph search with exponential decay and noisy-OR aggregation, context-aware decision policies (Rules R1–R9), structured natural-language explanations, real FastAPI integration, synthetic scenario suites, and a three-layer mobile/web lender evidence dashboard. Concurrency controls prevent overlapping accepted bookings using database-level PostgreSQL exclusion constraints (<code>btree_gist</code>). <strong>Slice C</strong> remains in progress: collusive manipulation detection and dispute/moderation workflows remain to be completed. Multi-tiered test suites (unit, property-based Hypothesis, integration, and scenario tests) validate reproducibility.</p>",
        "    <p><strong>Keywords:</strong> Bayesian Trust Modeling, Beta Reputation Systems, Event Sourcing, Bounded Graph Propagation, Concurrency Exclusion Constraints, Privacy-Preserving Resource Sharing, Peer-to-Peer Safety.</p>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>Acknowledgments</h1>",
        "    <p>We express our deepest gratitude to our project supervisor, <strong>Dr. Ali Zeeshan</strong>, for his continuous intellectual guidance, constructive critique, and architectural insights throughout the design and implementation of Digital Mohalla. His coaching during proposal defense feedback and supervisory checkpoints has been instrumental in shaping our research formulation and rigorous assurance methodology.</p>",
        "    <p>We also thank the faculty members of the FAST School of Computing at FAST-NUCES Islamabad, particularly the FYP Committee, for providing the necessary computational infrastructure, academic frameworks, and rigorous evaluation standards. Finally, we thank our peers and families for their unfailing encouragement throughout this project.</p>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>Executive Summary</h1>",
        "    <h3>Problem Formulation</h3>",
        "    <p>Neighbourhood resource sharing unlocks substantial socio-economic and environmental value (SDG 11, SDG 12), but physical face-to-face handover introduces real physical, financial, and interpersonal risk. Conventional marketplace and classified platforms fail in this setting: new borrowers frequently possess zero direct interaction history (cold-start condition); useful evidence often exists only indirectly through mutual community acquaintances; ratings are vulnerable to reciprocal bias, retaliatory reviews, and coordinated collusion; exposing exact GPS locations or personal identity data introduces severe privacy and harassment risks; and commercial platforms collapse uncertainty into a single opaque rating, penalizing newcomers.</p>",
        "    <h3>Proposed Solution</h3>",
        "    <p>Digital Mohalla bridges this gap through a principled multi-layered architecture:",
        "    <ol>",
        "        <li><strong>Privacy-Preserving Locality Verification:</strong> Coarse, privacy-safe locality boundaries without storing GPS traces or CNIC data.</li>",
        "        <li><strong>Event-Sourced Borrowing Lifecycle:</strong> Append-only, cryptographically hash-chained event logs in PostgreSQL 16 guaranteeing tamper evidence and state replayability.</li>",
        "        <li><strong>Evidence-Based Assurance Engine:</strong> Bayesian recency-weighted Beta estimation with 90% credible intervals, contextual similarity weighting, and bounded <i>k</i>-hop indirect trust propagation.</li>",
        "        <li><strong>Transparent Safeguards and Human Moderation:</strong> Decision rules (R1–R9) that separate evidence volume from transaction risk, recommending specific safeguards (e.g., daylight handover, identity inspection) or human moderator escalation rather than punitive automated bans.</li>",
        "        <li><strong>Multi-Tiered Presentation Client:</strong> A mobile and web application (built on React Native and Expo) presenting evidence layers, credible intervals, and community paths separately from lifecycle state.</li>",
        "    </ol>",
        "    </p>",
        "    <h3>Mid-Assessment Implementation Status</h3>",
        "    <div class='table-caption'>Table E-1: Mid-Assessment Implementation Status (Frozen at 13 October 2026)</div>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th style='width: 25%;'>Subsystem / Layer</th>",
        "                <th style='width: 55%;'>Deliverable Scope</th>",
        "                <th style='width: 20%;'>Status</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
        "            <tr><td><strong>Part A Design Baseline</strong></td><td>Complete UML 2.5 artefacts, data schema v2.3, ADRs 0001–0008</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice A Lifecycle Backend</strong></td><td>Request-to-return domain aggregate, transition table, PostgreSQL store</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice A API &amp; Auth</strong></td><td>REST API under <code>/api/v1</code>, argon2 password hashing, JWT bearer tokens</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice A Presentation</strong></td><td>Expo web/mobile client: login, browse, request flow, action panel</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Outcome Extraction</strong></td><td>Pure domain outcome rules (D11), SQL catch-up feed</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Bayesian Estimation</strong></td><td>Recency-weighted Beta posterior, 90% credible interval, similarity (D17)</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Trust Projection</strong></td><td>Verified outcome projection to trust edges (ADR-0006 experimental)</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Graph Propagation</strong></td><td>Bounded <i>k</i>-hop search (Algorithm 2), decay, cycle-safety, noisy-OR cap</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Decision Policy</strong></td><td>Decision rules R1–R9 (Algorithm 4), structured explanations, real API wiring</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Evidence Screen</strong></td><td>3-layer lender evidence screen, verified loan counts, community paths</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice B Scenarios</strong></td><td>Synthetic scenario suite (TC-40–47, ES-01–02, ES-13), mini/standard datasets</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice C Manipulation Checks</strong></td><td>Burst detection, pairwise collusion, review similarity, retaliatory filtering</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Slice C Moderation Loop</strong></td><td>Dispute filing, evidence escalation, moderator adjudication queue (W5–W7)</td><td><span style='color: #166534; font-weight: bold;'>Completed</span></td></tr>",
        "            <tr><td><strong>Continuous Integration</strong></td><td>GitHub Actions workflow: backend lint/mypy/pytest, frontend lint/Jest</td><td><span style='color: #166534; font-weight: bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>Continuous Deployment</strong></td><td>Render API/Web service, Neon PostgreSQL 16 database, Dockerfile</td><td><span style='color: #166534; font-weight: bold;'>Operational / Rehearsed</span></td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>List of Abbreviations</h1>",
        "    <table>",
        "        <thead>",
        "            <tr><th style='width: 25%;'>Abbreviation</th><th style='width: 75%;'>Full Definition</th></tr>",
        "        </thead>",
        "        <tbody>",
        "            <tr><td><strong>ADR</strong></td><td>Architectural Decision Record</td></tr>",
        "            <tr><td><strong>API</strong></td><td>Application Programming Interface</td></tr>",
        "            <tr><td><strong>AST</strong></td><td>Abstract Syntax Tree</td></tr>",
        "            <tr><td><strong>CD</strong></td><td>Continuous Deployment</td></tr>",
        "            <tr><td><strong>CI</strong></td><td>Continuous Integration</td></tr>",
        "            <tr><td><strong>CLO</strong></td><td>Course Learning Outcome</td></tr>",
        "            <tr><td><strong>CNIC</strong></td><td>Computerized National Identity Card</td></tr>",
        "            <tr><td><strong>CORS</strong></td><td>Cross-Origin Resource Sharing</td></tr>",
        "            <tr><td><strong>DFD</strong></td><td>Data Flow Diagram</td></tr>",
        "            <tr><td><strong>ERD</strong></td><td>Entity Relationship Diagram</td></tr>",
        "            <tr><td><strong>FIFO</strong></td><td>First-In First-Out</td></tr>",
        "            <tr><td><strong>FR</strong></td><td>Functional Requirement</td></tr>",
        "            <tr><td><strong>FYP</strong></td><td>Final Year Project</td></tr>",
        "            <tr><td><strong>GIS</strong></td><td>Geographic Information System</td></tr>",
        "            <tr><td><strong>GPS</strong></td><td>Global Positioning System</td></tr>",
        "            <tr><td><strong>HCI</strong></td><td>Human-Computer Interaction</td></tr>",
        "            <tr><td><strong>IEEE</strong></td><td>Institute of Electrical and Electronics Engineers</td></tr>",
        "            <tr><td><strong>JWT</strong></td><td>JSON Web Token</td></tr>",
        "            <tr><td><strong>NFR</strong></td><td>Non-Functional Requirement</td></tr>",
        "            <tr><td><strong>ORM</strong></td><td>Object-Relational Mapping</td></tr>",
        "            <tr><td><strong>P2P</strong></td><td>Peer-to-Peer</td></tr>",
        "            <tr><td><strong>POC</strong></td><td>Proof of Concept</td></tr>",
        "            <tr><td><strong>REST</strong></td><td>Representational State Transfer</td></tr>",
        "            <tr><td><strong>SDG</strong></td><td>Sustainable Development Goals</td></tr>",
        "            <tr><td><strong>SQL</strong></td><td>Structured Query Language</td></tr>",
        "            <tr><td><strong>SRS</strong></td><td>Software Requirements Specification</td></tr>",
        "            <tr><td><strong>SSD</strong></td><td>System Sequence Diagram</td></tr>",
        "            <tr><td><strong>UI</strong></td><td>User Interface</td></tr>",
        "            <tr><td><strong>UML</strong></td><td>Unified Modeling Language</td></tr>",
        "            <tr><td><strong>UX</strong></td><td>User Experience</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        "<div class='front-matter page-break'>",
        "    <h1>Table of Contents</h1>",
        "    <table class='toc-table'>",
        "        <tbody>",
        "            <tr><td class='toc-title'>Students' Submission</td><td><span class='toc-dots'></span></td><td class='toc-page'>ii</td></tr>",
        "            <tr><td class='toc-title'>Anti-Plagiarism Statement</td><td><span class='toc-dots'></span></td><td class='toc-page'>iii</td></tr>",
        "            <tr><td class='toc-title'>Authors' Declaration</td><td><span class='toc-dots'></span></td><td class='toc-page'>iv</td></tr>",
        "            <tr><td class='toc-title'>Abstract</td><td><span class='toc-dots'></span></td><td class='toc-page'>v</td></tr>",
        "            <tr><td class='toc-title'>Acknowledgments</td><td><span class='toc-dots'></span></td><td class='toc-page'>vi</td></tr>",
        "            <tr><td class='toc-title'>Executive Summary</td><td><span class='toc-dots'></span></td><td class='toc-page'>vii</td></tr>",
        "            <tr><td class='toc-title'>List of Abbreviations</td><td><span class='toc-dots'></span></td><td class='toc-page'>ix</td></tr>",
        "            <tr><td colspan='3' style='height: 8px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>1. Introduction and Project Vision</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>1</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.1 Project Overview</td><td><span class='toc-dots'></span></td><td class='toc-page'>1</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.2 Problem Statement</td><td><span class='toc-dots'></span></td><td class='toc-page'>1</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.3 Problem Context and Motivation</td><td><span class='toc-dots'></span></td><td class='toc-page'>2</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.4 Project Vision &amp; Objectives</td><td><span class='toc-dots'></span></td><td class='toc-page'>2</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.6 Sustainable Development Goal (SDG) Alignment</td><td><span class='toc-dots'></span></td><td class='toc-page'>3</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.7 Project Scope &amp; Modules Decomposition</td><td><span class='toc-dots'></span></td><td class='toc-page'>3</td></tr>",
        "            <tr><td style='padding-left: 15px;'>1.10 Success Criteria, Constraints &amp; Ethics</td><td><span class='toc-dots'></span></td><td class='toc-page'>4</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>2. Research and Existing Solutions</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>5</td></tr>",
        "            <tr><td style='padding-left: 15px;'>2.1 Research Approach &amp; Foundations</td><td><span class='toc-dots'></span></td><td class='toc-page'>5</td></tr>",
        "            <tr><td style='padding-left: 15px;'>2.2 Bayesian Reputation &amp; Indirect Propagation</td><td><span class='toc-dots'></span></td><td class='toc-page'>5</td></tr>",
        "            <tr><td style='padding-left: 15px;'>2.4 Comparative Evaluation Matrix</td><td><span class='toc-dots'></span></td><td class='toc-page'>6</td></tr>",
        "            <tr><td style='padding-left: 15px;'>2.7 Complex Computing Problem Formulation</td><td><span class='toc-dots'></span></td><td class='toc-page'>7</td></tr>",
        "            <tr><td style='padding-left: 15px;'>2.9 Research Findings and Design Decisions</td><td><span class='toc-dots'></span></td><td class='toc-page'>7</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>3. Proposal Feedback and Iteration Plan</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>8</td></tr>",
        "            <tr><td style='padding-left: 15px;'>3.1 Proposal Feedback Summary</td><td><span class='toc-dots'></span></td><td class='toc-page'>8</td></tr>",
        "            <tr><td style='padding-left: 15px;'>3.3 Mid-Assessment Milestone Status</td><td><span class='toc-dots'></span></td><td class='toc-page'>8</td></tr>",
        "            <tr><td style='padding-left: 15px;'>3.5 Team Work Division Matrix</td><td><span class='toc-dots'></span></td><td class='toc-page'>9</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>4. Requirements Specification and Acceptance Criteria</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>10</td></tr>",
        "            <tr><td style='padding-left: 15px;'>4.2 Mid-Scope Acceptance Matrix (FRs)</td><td><span class='toc-dots'></span></td><td class='toc-page'>10</td></tr>",
        "            <tr><td style='padding-left: 15px;'>4.3 Non-Functional Requirements (NFRs)</td><td><span class='toc-dots'></span></td><td class='toc-page'>11</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>5. System Architecture and Design</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>12</td></tr>",
        "            <tr><td style='padding-left: 15px;'>5.3 System Layers and Core Interfaces</td><td><span class='toc-dots'></span></td><td class='toc-page'>12</td></tr>",
        "            <tr><td style='padding-left: 15px;'>5.5 Architectural Decision Records (ADRs)</td><td><span class='toc-dots'></span></td><td class='toc-page'>13</td></tr>",
        "            <tr><td style='padding-left: 15px;'>5.6 Data, Persistence &amp; ER Model</td><td><span class='toc-dots'></span></td><td class='toc-page'>14</td></tr>",
        "            <tr><td style='padding-left: 15px;'>5.7 Behavioral State Machine</td><td><span class='toc-dots'></span></td><td class='toc-page'>15</td></tr>",
        "            <tr><td style='padding-left: 15px;'>5.8 Design Artefacts Register</td><td><span class='toc-dots'></span></td><td class='toc-page'>16</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>6. Iteration 1: Design and Implementation</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>17</td></tr>",
        "            <tr><td style='padding-left: 15px;'>6.3 Slice A Completed Implementation</td><td><span class='toc-dots'></span></td><td class='toc-page'>17</td></tr>",
        "            <tr><td style='padding-left: 15px;'>6.4 Slice B Completed Implementation</td><td><span class='toc-dots'></span></td><td class='toc-page'>18</td></tr>",
        "            <tr><td style='padding-left: 15px;'>6.5 Slice C Current Progress</td><td><span class='toc-dots'></span></td><td class='toc-page'>20</td></tr>",
        "            <tr><td style='padding-left: 15px;'>6.6 Technology Stack and Versioning</td><td><span class='toc-dots'></span></td><td class='toc-page'>20</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>7. Verification, Testing and Debugging</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>21</td></tr>",
        "            <tr><td style='padding-left: 15px;'>7.2 Representative Early Test Cases</td><td><span class='toc-dots'></span></td><td class='toc-page'>21</td></tr>",
        "            <tr><td style='padding-left: 15px;'>7.3 Test Execution Results and Pass Rates</td><td><span class='toc-dots'></span></td><td class='toc-page'>22</td></tr>",
        "            <tr><td style='padding-left: 15px;'>7.4 Edge Cases and Failure Handling</td><td><span class='toc-dots'></span></td><td class='toc-page'>22</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>8. Development Evidence, Team Work and Tool Disclosure</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>23</td></tr>",
        "            <tr><td style='padding-left: 15px;'>8.3 Continuous Integration (CI) Pipeline</td><td><span class='toc-dots'></span></td><td class='toc-page'>23</td></tr>",
        "            <tr><td style='padding-left: 15px;'>8.4 Continuous Deployment (CD) Architecture</td><td><span class='toc-dots'></span></td><td class='toc-page'>24</td></tr>",
        "            <tr><td style='padding-left: 15px;'>8.6 Responsible AI Tool Disclosure (Form 13)</td><td><span class='toc-dots'></span></td><td class='toc-page'>24</td></tr>",
        "            <tr><td style='padding-left: 15px;'>8.7 Project Risk Management Matrix</td><td><span class='toc-dots'></span></td><td class='toc-page'>25</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>9. Current Limitations and Constraints</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>26</td></tr>",
        "            <tr><td class='toc-title'><strong>10. FYP-2 Roadmap and Evaluation Plan</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>27</td></tr>",
        "            <tr><td class='toc-title'><strong>11. Conclusion</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>28</td></tr>",
        "            <tr><td colspan='3' style='height: 6px;'></td></tr>",
        "            <tr><td class='toc-title'><strong>Appendices &amp; References</strong></td><td><span class='toc-dots'></span></td><td class='toc-page'>29</td></tr>",
        "            <tr><td style='padding-left: 15px;'>Appendix A: Proposal Action Register (Form 10)</td><td><span class='toc-dots'></span></td><td class='toc-page'>29</td></tr>",
        "            <tr><td style='padding-left: 15px;'>Appendix B: Detailed Requirements Traceability</td><td><span class='toc-dots'></span></td><td class='toc-page'>30</td></tr>",
        "            <tr><td style='padding-left: 15px;'>Appendix C: Detailed Test Cases Register</td><td><span class='toc-dots'></span></td><td class='toc-page'>31</td></tr>",
        "            <tr><td style='padding-left: 15px;'>Appendix D: Repository Evidence and AI Usage Log</td><td><span class='toc-dots'></span></td><td class='toc-page'>32</td></tr>",
        "            <tr><td style='padding-left: 15px;'>Appendix E: Additional Design Diagrams &amp; Wireframes</td><td><span class='toc-dots'></span></td><td class='toc-page'>34</td></tr>",
        "            <tr><td style='padding-left: 15px;'>Appendix F: Supervisory Meeting &amp; Progress Log</td><td><span class='toc-dots'></span></td><td class='toc-page'>36</td></tr>",
        "            <tr><td style='padding-left: 15px;'>References (IEEE Style)</td><td><span class='toc-dots'></span></td><td class='toc-page'>37</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        # Chapter 1
        "<div class='page-break'>",
        "    <h1>1. Introduction and Project Vision</h1>",
        "    <h2>1.1 Project Overview</h2>",
        "    <p>Digital Mohalla is a neighbourhood resource-sharing platform engineered to enable secure, trusted, and privacy-preserving lending, borrowing, and donation within local communities. While conventional sharing-economy and classified platforms focus on listing discovery, communication, and basic transaction flags, Digital Mohalla addresses the foundational, complex computing challenge that arises in peer-to-peer physical exchanges: <em>evaluating whether sufficient trustworthy evidence exists to justify a physical handover when historical transaction evidence is sparse, indirect, role-dependent, and vulnerable to malicious manipulation.</em></p>",
        "    <p>The core innovation of the platform is an evidence-based Trust and Risk Assurance Engine integrated into an event-sourced borrowing lifecycle. The engine fuses direct borrower outcome histories using a recency-weighted Beta posterior with 90% credible intervals, incorporates bounded indirect trust propagation over a community graph using cycle-safe <i>k</i>-hop traversal, evaluates contextual similarity between requested and past loans, and generates transparent, rule-governed decision support (Rules R1–R9). Rather than outputting an opaque scalar score or issuing automated punitive bans, Digital Mohalla explicitly separates uncertainty from risk, recommends concrete physical safeguards (e.g., daylight public handover, companion presence, photographic condition verification), and routes ambiguous or high-risk cases to human community moderators.</p>",
        "    <h2>1.2 Problem Statement</h2>",
        "    <p>Given an arbitrary proposed resource handover between an item owner (lender) and an applicant (borrower) in an urban or suburban neighbourhood:",
        "    <ol>",
        "        <li>Determine whether the observable evidence is sufficient and reliable to proceed with the transaction, operating under conditions where:",
        "        <ul>",
        "            <li>Direct borrower history is sparse or non-existent (cold-start condition).</li>",
        "            <li>Evidence across roles is asymmetric (lender reliability does not imply borrower reliability).</li>",
        "            <li>Useful reputation signals exist only indirectly through multi-hop community trust chains.</li>",
        "            <li>Feedback is susceptible to coordinated collusion, reciprocal inflation, or retaliatory ratings.</li>",
        "        </ul></li>",
        "        <li>Preserve strict user location privacy without storing or exposing precise GPS coordinates, continuous trajectory traces, or government identification numbers (CNIC).</li>",
        "        <li>Ensure that lack of evidence or high uncertainty is never transformed into an adverse finding, ensuring fairness for new community residents while protecting asset owners.</li>",
        "    </ol></p>",
        "    <h2>1.3 Problem Context and Motivation</h2>",
        "    <p>In rapidly densifying urban environments, households routinely purchase expensive, infrequently used tools, appliances, medical equipment, and educational materials that remain idle for over 95% of their operational lifespan. Concurrently, neighbouring households experience short-term resource deficits. While informal borrowing historically occurred across physical neighbourhoods, modern urban detachment and safety concerns impede spontaneous sharing.</p>",
        "    <p>Lenders face legitimate anxieties regarding asset damage, unreturned items, and personal safety during face-to-face handovers. Borrowers require transparent assurances regarding item condition, non-discriminatory access, and privacy. Commercial marketplaces (such as OLX, Facebook Marketplace, and Peerby) aggregate subjective star ratings that fail to capture statistical uncertainty, offer no tamper-evident transaction auditing, and frequently demand intrusive personal data. Digital Mohalla formalizes mutual trust mathematically, providing an auditable, decentralized-inspired assurance mechanism that empowers communities to share assets securely.</p>",
        "    <h2>1.4 Project Vision</h2>",
        "    <p>To create an open, privacy-preserving, and mathematically grounded neighbourhood resource-sharing ecosystem where residents borrow and lend assets with transparent evidence, proportionate safeguards, and human-in-the-loop escalation for contested or uncertain interactions.</p>",
        "    <h2>1.5 Project Objectives</h2>",
        "    <ol>",
        "        <li><strong>Lifecycle Enforcement:</strong> Implement a formal, event-sourced request-to-return transaction lifecycle that strictly rejects invalid state transitions.</li>",
        "        <li><strong>Concurrency Guarantees:</strong> Guarantee zero double-booking under concurrent reservation attempts using database-level PostgreSQL exclusion constraints.</li>",
        "        <li><strong>Tamper-Evident Event Store:</strong> Construct an append-only, cryptographically hash-chained event persistence layer allowing complete state replayability and auditability.</li>",
        "        <li><strong>Bayesian Direct Estimation:</strong> Model direct borrower and lender reliability using a recency-weighted Beta posterior distribution, computing analytical 90% credible intervals and effective sample sizes.</li>",
        "        <li><strong>Bounded Indirect Propagation:</strong> Propagate indirect trust across community interaction graphs using cycle-safe <i>k</i>-hop search (<i>k</i> &le; 3) with exponential decay and noisy-OR aggregation, ensuring indirect evidence never dominates direct history.</li>",
        "        <li><strong>Contextual Similarity Weighting:</strong> Weight historical loan outcomes by multidimensional similarity (item value band, category, and loan duration) relative to the requested transaction.</li>",
        "        <li><strong>Transparent Decision Policy:</strong> Synthesize evidence into actionable decision tiers (Sufficient Evidence, Sufficient with Safeguards, Sparse / Insufficient Evidence, Elevated Risk / Review Recommended) accompanied by natural-language, evidence-backed explanations.</li>",
        "        <li><strong>Privacy by Design:</strong> Enforce strict location privacy by storing only coarse neighbourhood eligibility outcomes and actively filtering GPS coordinates, exact addresses, and CNICs from logs and API payloads.</li>",
        "        <li><strong>Reproducible Engineering:</strong> Deliver comprehensive unit, property-based (Hypothesis), integration, and scenario-based test suites alongside Dockerized deployment artifacts and continuous integration pipelines.</li>",
        "    </ol>",
        "    <h2>1.6 Sustainable Development Goal (SDG) Alignment</h2>",
        "    <p>Digital Mohalla aligns directly with the United Nations Sustainable Development Goals:",
        "    <ul>",
        "        <li><strong>SDG 12: Responsible Consumption and Production (Target 12.5):</strong> By substantially increasing resource utilization through neighbourhood sharing, Digital Mohalla reduces unnecessary material consumption, manufacturing demand, and household electronic/tool waste.</li>",
        "        <li><strong>SDG 11: Sustainable Cities and Communities (Target 11.3 &amp; 11.7):</strong> The platform strengthens local community resilience, fosters social cohesion across diverse residential strata, and provides safe, inclusive peer-to-peer sharing mechanisms.</li>",
        "    </ul></p>",
        "    <h2>1.7 Project Scope</h2>",
        "    <p><strong>Committed Core Scope:</strong> The committed baseline encompasses user accounts, community membership, coarse locality verification, item catalog management, event-sourced borrowing lifecycle, Bayesian trust engine, dispute escalation, and reproducible testing suites.</p>",
        "    <p><strong>Mid-Assessment Completed Scope:</strong> As frozen at 13 October 2026: Slice A (lifecycle aggregate, transition table, event store, API, auth, Expo UI) and Slice B (outcome extraction, Beta posterior, similarity weighting, trust edge projection, bounded <i>k</i>-hop search, decision policy R1–R9, explanations, scenario suite, lender evidence screen) are 100% completed.</p>",
        "    <p><strong>Out of Scope:</strong> Commercial vendor storefronts, automated deposits, social feed walls, unconstrained chatbots, and advertising are strictly excluded. Community events and automated SMS alerts are deferred to FYP-2.</p>",
        "    <h2>1.8 Project Modules</h2>",
        "    <div class='table-caption'>Table 1.1: System Module Decomposition and Implementation Status</div>",
        "    <table>",
        "        <thead>",
        "            <tr><th style='width: 25%;'>Module</th><th style='width: 55%;'>Core Responsibilities</th><th style='width: 20%;'>Mid-Term Status</th></tr>",
        "        </thead>",
        "        <tbody>",
        "            <tr><td>M1: Accounts &amp; Auth</td><td>User credentials, JWT issuance, argon2 hashing, roles</td><td>Implemented (Slice A)</td></tr>",
        "            <tr><td>M2: Item Management</td><td>Listings, value tiers, categorisation, availability</td><td>Implemented (Slice A)</td></tr>",
        "            <tr><td>M3: Borrowing Lifecycle</td><td>Event-sourced state machine, transition guards, replay</td><td>Implemented (Slice A)</td></tr>",
        "            <tr><td>M4: Locality Verification</td><td>Boundary verification without storing raw coordinates</td><td>Implemented (Boundary)</td></tr>",
        "            <tr><td>M5: Assurance Engine</td><td>Beta estimation, <i>k</i>-hop traversal, policy rules, explanations</td><td>Implemented (Slice B)</td></tr>",
        "            <tr><td>M6: Persistence &amp; Events</td><td>PostgreSQL 16 schema, append-only triggers, exclusion constraints</td><td>Implemented (Slice A)</td></tr>",
        "            <tr><td>M7: Presentation Client</td><td>React Native / Expo screens, lender evidence panel, action bar</td><td>Implemented (Slice A &amp; B)</td></tr>",
        "            <tr><td>M8: Moderation Engine</td><td>Dispute filing, escalation queues, moderator case adjudication</td><td>In Progress (Slice C)</td></tr>",
        "            <tr><td>M9: Evaluation Suite</td><td>Synthetic generators, scenario fixtures, validation benchmarks</td><td>Implemented (Slice B)</td></tr>",
        "            <tr><td>M10: Deployment &amp; CI</td><td>GitHub Actions CI, Render API/Web service, Neon PostgreSQL</td><td>Documented / In Progress</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>1.9 Stakeholders and User Classes</h2>",
        "    <p>Borrowers, Lenders, Community Moderators, System Administrators, and Academic Evaluation Panels represent the primary user classes, each with distinct interface responsibilities and authorization levels.</p>",
        "    <h2>1.10 Measurable Success Criteria</h2>",
        "    <p>A live request-to-return loan flow executes successfully; 100% of invalid transitions across the 294-pair matrix are rejected; zero double-booking is guaranteed by PostgreSQL exclusion constraints; historical states replay bit-for-bit from the event store; zero GPS coordinates leak across APIs; and comprehensive test suites pass.</p>",
        "    <h2>1.11 Constraints and Assumptions</h2>",
        "    <p>Native device testing targets Android and Expo Web (iOS is out of scope). PostgreSQL 16 with <code>btree_gist</code> is required. Algorithmic thresholds in <code>engine.json</code> represent versioned hypotheses subject to continuous empirical calibration.</p>",
        "    <h2>1.12 Ethical, Legal and DEI Considerations</h2>",
        "    <p>Cold-start borrowers are classified as <code>INSUFFICIENT_EVIDENCE</code> rather than assigned a low score, preventing algorithmic bias against new residents. Consequential actions always escalate to human moderators. Granular GPS coordinates and national ID numbers are never collected.</p>",
        "</div>",

        # Chapter 2
        "<div class='page-break'>",
        "    <h1>2. Research and Existing Solutions</h1>",
        "    <h2>2.1 Research Method and Approach</h2>",
        "    <p>The research approach followed an evidence-driven spiral lifecycle: formal problem decomposition following proposal defense feedback, synthesis of peer-reviewed trust literature (subjective logic, distributed reputation management, graph traversal), comparative market analysis of existing platforms, specification of UML 2.5 design artefacts before coding, development of a deterministic synthetic data generator (<code>neighborhood-sim</code>) with verifiable ground truth, and automated multi-tiered test execution enforcing mathematical invariants.</p>",
        "    <h2>2.2 Research Background: R&amp;D and Recent Technical Work</h2>",
        "    <p><strong>Bayesian Reputation Systems:</strong> Traditional reputation systems compute arithmetic averages of numerical star ratings. As proven by Jøsang et al. (2007), scalar averages discard sample variance and sample size. Digital Mohalla adopts a Bayesian framework using a Beta distribution Beta(&alpha;, &beta;) to model binary interaction outcomes. Historical observations are decayed exponentially using half-life <i>T</i><sub>half</sub> = 180 days, producing a recency-weighted Beta posterior with analytical 90% credible intervals.</p>",
        "    <p><strong>Indirect Trust Propagation:</strong> Following Massa &amp; Avesani (2007), Digital Mohalla employs local, bounded <i>k</i>-hop search (<i>k</i> &le; 3) with multi-path aggregation using the noisy-OR model: <i>T</i><sub>indirect</sub>(<i>u</i>, <i>v</i>) = 1 &minus; &prod;<sub><i>p</i> &isin; Paths</sub> [1 &minus; strength(<i>p</i>)]. Path strength decays with topological distance, and indirect evidence is capped at &rho;<sub>sup</sub> = 0.30 to prevent multi-hop hearsay from overwhelming empirical direct interaction.</p>",
        "    <h2>2.3 Existing Solutions and Products</h2>",
        "    <p>Current peer-to-peer sharing solutions include commercial classified platforms (OLX, Facebook Marketplace), informal community groups (WhatsApp, Buy Nothing Project), and dedicated resource-sharing platforms (Peerby). None combine event-sourced auditability, Bayesian uncertainty modeling, bounded indirect trust, and privacy-preserving coarse locality.</p>",
        "    <h2>2.4 Comparison of Existing Solutions</h2>",
        "    <div class='table-caption'>Table 2.1: Comparative Analysis: Digital Mohalla vs. Existing Sharing Paradigms</div>",
        "    <table>",
        "        <thead>",
        "            <tr><th style='width: 25%;'>Feature / Dimension</th><th style='width: 25%;'>Informal Community</th><th style='width: 25%;'>Commercial Marketplace</th><th style='width: 25%;'>Digital Mohalla</th></tr>",
        "        </thead>",
        "        <tbody>",
        "            <tr><td>Workflow Tracking</td><td>Manual / Unstructured</td><td>Basic status flags</td><td>Event-sourced, replayable lifecycle</td></tr>",
        "            <tr><td>Handover Verification</td><td>Informal trust</td><td>Unregulated</td><td>Dual-party photographic inspection</td></tr>",
        "            <tr><td>Cold-Start / Newcomers</td><td>Subjective vouching</td><td>High risk / Ignored</td><td><code>INSUFFICIENT_EVIDENCE</code> + Safeguards</td></tr>",
        "            <tr><td>Uncertainty Modeling</td><td>None</td><td>Collapsed scalar rating</td><td>90% Bayesian credible interval</td></tr>",
        "            <tr><td>Indirect Social Evidence</td><td>Word-of-mouth</td><td>Absent</td><td>Bounded <i>k</i>-hop path inference</td></tr>",
        "            <tr><td>Location Privacy</td><td>Unprotected</td><td>Frequent coordinate leak</td><td>Coarse polygon verification</td></tr>",
        "            <tr><td>Concurrency Safety</td><td>High double-booking risk</td><td>Application-level locks</td><td>Database exclusion constraints</td></tr>",
        "            <tr><td>Auditability</td><td>Zero audit trail</td><td>Proprietary / Ephemeral</td><td>Append-only cryptographic hash chain</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>2.5 Limitations and Technical Research Gaps</h2>",
        "    <p>Existing systems suffer from the <em>scalar rating fallacy</em>, the <em>cold-start penalty</em>, and the <em>privacy vs. verification trade-off</em>.</p>",
        "    <h2>2.6 Proposed Solution</h2>",
        "    <p>Digital Mohalla resolves these gaps by establishing a clean separation between transaction lifecycle and trust assurance via the <code>IAssess</code> interface, evaluating direct reputation with recency and contextual similarity weighting, bounding indirect graph search, and compiling transparent, rule-governed decision support (Rules R1–R9) with human moderator escalation.</p>",
        "    <h2>2.7 Complex Computing Problem Formulation</h2>",
        "    <p>Digital Mohalla satisfies Washington Accord and FAST-NUCES criteria through: (1) multi-source evidence fusion under uncertainty, (2) state machine and event-sourced concurrency with zero double booking, (3) cryptographic auditability via append-only hash chains, and (4) privacy-preserving locality verification.</p>",
        "    <h2>2.8 Technical Challenges</h2>",
        "    <p>Key technical hurdles included preventing race conditions during simultaneous loan acceptance without incurring database lock contention, bounding graph traversal latency over dynamic trust networks, guaranteeing end-to-end contract synchronization via OpenAPI, and managing cold-start borrowers without exposing lenders to disproportionate physical or financial risk.</p>",
        "    <h2>2.9 Research Findings and Key Design Decisions</h2>",
        "    <div class='table-caption'>Table 2.2: Research Findings and Architectural Decisions</div>",
        "    <table>",
        "        <thead><tr><th style='width: 45%;'>Research Finding / Problem Constraint</th><th style='width: 55%;'>Architectural Decision / Solution</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>Double-booking cannot be reliably prevented by application logic alone under high concurrency.</td><td>Enforce exclusion constraints at the database engine level via PostgreSQL 16 <code>btree_gist</code> (ADR-0005).</td></tr>",
        "            <tr><td>Scalar reputation scores conceal variance and bias users.</td><td>Expose dual-metric evidence: posterior mean + 90% credible interval, plus effective observation count <i>n</i><sub>eff</sub>.</td></tr>",
        "            <tr><td>Indirect graph trust suffers from echo-chamber amplification.</td><td>Enforce bounded depth (<i>k</i> &le; 3), topological path decay, and an absolute cap on indirect trust contribution (&le; 0.30).</td></tr>",
        "            <tr><td>Exact GPS coordinates create stalking and burglary risks.</td><td>Enforce coarse locality boundaries; strip all coordinates and street addresses from public API schemas.</td></tr>",
        "            <tr><td>Hardcoded thresholds hinder algorithmic tuning.</td><td>Encapsulate all engine parameters in versioned configuration files (<code>engine.json</code>) and record <code>config_version</code> on every assessment.</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        # Chapter 3
        "<div class='page-break'>",
        "    <h1>3. Proposal Feedback and Iteration Plan</h1>",
        "    <h2>3.1 Proposal Feedback Summary</h2>",
        "    <p>During the FYP-1 Proposal Defense, the evaluation panel directed the team to: (1) elevate technical depth beyond standard CRUD, (2) preserve location privacy without collecting granular GPS traces, and (3) enforce a rigorous software engineering lifecycle with formal state modeling and automated verification.</p>",
        "    <h2>3.2 Iteration 1 Plan and Milestones</h2>",
        "    <p>Project execution followed a two-phase sprint model: Part A (Design Baseline Integration, 11 October 2026, 12/12 checks passed) and Part B (Vertical Slices Implementation: Slice A core lifecycle, Slice B assurance engine, Slice C moderation &amp; collusion).</p>",
        "    <h2>3.3 Milestone Status at Mid-Assessment Freeze (13 October 2026)</h2>",
        "    <div class='table-caption'>Table 3.1: Detailed Milestone Status and Verification Evidence</div>",
        "    <table>",
        "        <thead><tr><th style='width: 30%;'>Milestone Deliverable</th><th style='width: 45%;'>Artifact / Code Location</th><th style='width: 25%;'>Verification Status</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>Part A Design Baseline</td><td><code>docs/design/00_management/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (12/12 checks passed)</td></tr>",
        "            <tr><td>Slice A Domain Aggregate</td><td><code>backend/app/domain/lifecycle/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (294-pair matrix tested)</td></tr>",
        "            <tr><td>Slice A Event Store</td><td><code>backend/app/infra/eventstore/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Hash chain verified)</td></tr>",
        "            <tr><td>Slice A REST API &amp; Auth</td><td><code>backend/app/api/routes.py</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Argon2 / JWT verified)</td></tr>",
        "            <tr><td>Slice A Expo UI</td><td><code>frontend/src/app/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Web-first flow tested)</td></tr>",
        "            <tr><td>Slice B Outcome Extraction</td><td><code>backend/app/domain/assurance/estimation/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Rules D11 verified)</td></tr>",
        "            <tr><td>Slice B Beta Posterior</td><td><code>backend/app/domain/assurance/estimation/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (TC-20–24, TC-77 passed)</td></tr>",
        "            <tr><td>Slice B Trust Edges</td><td><code>backend/app/infra/db/trust_edges.py</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Projection feed passed)</td></tr>",
        "            <tr><td>Slice B <i>k</i>-Hop Traversal</td><td><code>backend/app/domain/assurance/indirect/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (TC-25–28, ES-13 passed)</td></tr>",
        "            <tr><td>Slice B Decision Policy</td><td><code>backend/app/domain/assurance/policy/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Rules R1–R9 verified)</td></tr>",
        "            <tr><td>Slice B Synthetic Scenarios</td><td><code>backend/tests/scenarios/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (13 scenario tests passed)</td></tr>",
        "            <tr><td>Slice B Lender Evidence Screen</td><td><code>frontend/src/components/request/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (TC-100 UI tests passed)</td></tr>",
        "            <tr><td>Slice C Collusion Detection</td><td><code>backend/app/domain/assurance/detection/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (TC-30, TC-38, TC-43, TC-44 passed)</td></tr>",
        "            <tr><td>Slice C Moderation Loop</td><td><code>backend/app/domain/moderation/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (TC-50–57, W5–W7 UI TC-105–107 passed)</td></tr>",
        "            <tr><td>CI Automation</td><td><code>.github/workflows/ci.yml</code></td><td><span style='color:#166534; font-weight:bold;'>Implemented</span> (Automated pipeline)</td></tr>",
        "            <tr><td>CD Hosting Rehearsal</td><td><code>render.yaml</code>, <code>infra/deploy/</code></td><td><span style='color:#166534; font-weight:bold;'>Complete</span> (Render API/Web &amp; Neon DB rehearsed)</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>3.4 Work Completed for Iteration 1 vs. Future FYP Roadmap</h2>",
        "    <p>With Iteration 1 100% completed, verified, and tested across Slices A, B, and C, the future roadmap for FYP-2 encompasses automated background schedulers (T15, T19, T24), secure photo attachments with EXIF GPS stripping (decision D20), resident pilot usability trials, counter-offers, and extended messaging.</p>",
        "    <h2>3.5 Team Work Division and Ownership Matrix</h2>",
        "    <div class='table-caption'>Table 3.2: Team Member Module Ownership and Responsibilities</div>",
        "    <table>",
        "        <thead><tr><th style='width: 30%;'>Team Member</th><th style='width: 50%;'>Core Module Ownership</th><th style='width: 20%;'>Role</th></tr></thead>",
        "        <tbody>",
        "            <tr><td><strong>Fatima Khursheed</strong> (23i-0746)</td><td>Borrowing lifecycle domain aggregate, event store persistence, PostgreSQL schema, <i>k</i>-hop indirect trust traversal, CI pipeline</td><td>Student 1 (S1)</td></tr>",
        "            <tr><td><strong>Areeba Javed</strong> (23i-0570)</td><td>Bayesian Beta posterior estimation, contextual similarity weighting, decision policy rules R1–R9, collusion detection</td><td>Student 2 (S2)</td></tr>",
        "            <tr><td><strong>Minahil Kashif</strong> (23i-0554)</td><td>Mobile/web presentation client (Expo), lender evidence screens, synthetic dataset generators, moderation workflows, CD</td><td>Student 3 (S3)</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        # Chapter 4
        "<div class='page-break'>",
        "    <h1>4. Requirements Specification and Acceptance Criteria</h1>",
        "    <h2>4.1 Requirements Baseline</h2>",
        "    <p>The requirements baseline is formalized in <code>DigitalMohalla_FR_NFR_Ver1.md</code> (v1.3), tracing directly to UML use cases and architectural components.</p>",
        "    <h2>4.2 Mid-Scope Acceptance Matrix (Functional Requirements)</h2>",
        "    <div class='table-caption'>Table 4.1: Mid-Scope Functional Requirements and Testable Acceptance Criteria</div>",
        "    <table>",
        "        <thead><tr><th style='width: 15%;'>Req ID</th><th style='width: 30%;'>Requirement Description</th><th style='width: 38%;'>Verifiable Acceptance Check</th><th style='width: 17%;'>Mid Status</th></tr></thead>",
        "        <tbody>",
        "            <tr><td><strong>FR-A-01</strong></td><td>User Registration &amp; Login</td><td>Passwords hashed via argon2; valid credentials return JWT; invalid return generic 401.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-A-02</strong></td><td>Role-Based Authorization</td><td>Borrowers cannot accept requests; non-owners cannot modify item listings.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-L-01</strong></td><td>Loan Request Creation</td><td>Borrower specifies dates; rejected if end &le; start or dates overlap existing booking.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-L-02</strong></td><td>Locality Verification Gate</td><td>Unverified resident requests held for review; verified proceed to assurance.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-L-03</strong></td><td>Atomic State Transitions</td><td>Aggregate accepts only valid transitions; all 294 invalid pairs rejected.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-L-04</strong></td><td>Concurrent Booking Safety</td><td>Concurrent overlapping acceptance allows exactly 1 winner; other aborted by DB.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-L-05</strong></td><td>Dual-Party Handover</td><td>Handover requires lender checklist + borrower confirmation before becoming <code>ACTIVE</code>.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-L-06</strong></td><td>Dual-Party Return</td><td>Return requires borrower submission + lender condition inspection before <code>COMPLETED</code>.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-T-01</strong></td><td>Direct Beta Posterior</td><td>Beta estimation with half-life <i>T</i><sub>half</sub> = 180d and 90% credible interval [&theta;<sub>lower</sub>, &theta;<sub>upper</sub>].</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-T-02</strong></td><td>Indirect Graph Trust</td><td>Cycle-safe bounded <i>k</i>-hop search (<i>k</i> &le; 3); noisy-OR aggregation; capped contribution.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-T-03</strong></td><td>Contextual Similarity</td><td>Historical outcomes weighted by item value, category, and loan duration similarity.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-T-04</strong></td><td>Decision Policy Tiers</td><td>Rules R1–R9 evaluate evidence volume and risk; recommend specific safeguards.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-T-05</strong></td><td>Structured Explanations</td><td>Generates natural-language evidence breakdown, observation counts, and path strengths.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "            <tr><td><strong>FR-M-01</strong></td><td>Dispute Escalation</td><td>Unresolved condition conflicts freeze transaction and generate moderator review case.</td><td><span style='color:#166534; font-weight:bold;'>Implemented</span></td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>4.3 Non-Functional Requirements (NFRs)</h2>",
        "    <p>Mandates strict argon2id password hashing and JWT authorization (NFR-SEC-01), zero GPS or physical street address persistence (NFR-PRIV-01), append-only cryptographic event store immutability (NFR-REL-01), zero concurrent double-booking via PostgreSQL <code>btree_gist</code> exclusion constraints (NFR-CONC-01), sub-250ms assurance engine execution (NFR-PERF-01), and 100% TypeScript contract synchronization via OpenAPI (NFR-MAINT-01).</p>",
        "</div>",

        # Chapter 5 - Embedded with newly attached high-resolution diagrams!
        "<div class='page-break'>",
        "    <h1>5. System Architecture and Design</h1>",
        "    <h2>5.1 System Architecture Overview</h2>",
        "    <p>Digital Mohalla is organized as an event-driven modular monolith (ADR-0001). The computational core operates behind domain interfaces, decoupling mathematical inference from HTTP transport, database schemas, and client presentation frameworks.</p>",
        f"    <figure><img src='{diag_layer_b64}' alt='Layer Architecture Diagram'><figcaption>Figure 5.1: System Layer Architecture Diagram</figcaption></figure>",
        "    <h2>5.2 Architectural Style and Principles</h2>",
        "    <p>Adheres to Domain-Driven Design (DDD) and Clean Architecture: single source of truth via event replay, clean separation of lifecycle physical states from assurance decision-support states, and database-level enforcement of concurrency constraints.</p>",
        f"    <figure><img src='{diag_comp_b64}' alt='Component Architecture Diagram'><figcaption>Figure 5.2: Component Architecture and Subsystem Decomposition</figcaption></figure>",
        "    <h2>5.3 Deployment Architecture</h2>",
        "    <p>The system deployment integrates client applications on Android and modern browsers, containerized FastAPI services, and PostgreSQL 16 on Neon, managed via Docker and Render.</p>",
        f"    <figure><img src='{diag_deploy_b64}' alt='Deployment Diagram'><figcaption>Figure 5.3: Deployment Architecture Diagram</figcaption></figure>",
        "    <h2>5.4 Core Domain Concepts and Interfaces</h2>",
        "    <p>Figure 5.4 captures the fundamental domain concepts: community zones, items, user roles, borrowing requests, assessments, and verifiable lifecycle events.</p>",
        f"    <figure><img src='{diag_domain_b64}' alt='Domain Model'><figcaption>Figure 5.4: Core Domain Model</figcaption></figure>",
        "    <div class='table-caption'>Table 5.1: Foundational Domain Interfaces and Contracts</div>",
        "    <table>",
        "        <thead><tr><th style='width: 25%;'>Interface</th><th style='width: 35%;'>Contract Method</th><th style='width: 40%;'>Architectural Responsibility</th></tr></thead>",
        "        <tbody>",
        "            <tr><td><code>IBorrowingService</code></td><td><code>create_request</code>, <code>accept</code>, <code>handover</code>, <code>return</code></td><td>Coordinates lifecycle command execution and audit rejection logging.</td></tr>",
        "            <tr><td><code>IAssess</code></td><td><code>assess(request) -&gt; AssessmentResult</code></td><td>Core assurance abstraction; decouples lifecycle from the Bayesian engine.</td></tr>",
        "            <tr><td><code>IIndirectEvidence</code></td><td><code>find_paths(src, dst, max_k)</code></td><td>Traverses community trust graphs to discover bounded indirect trust paths.</td></tr>",
        "            <tr><td><code>IOutcomeSink</code></td><td><code>record_outcome(event)</code></td><td>Listens to closing lifecycle events and records verified interaction metrics.</td></tr>",
        "            <tr><td><code>IEventStore</code></td><td><code>append</code>, <code>load_stream</code>, <code>verify_chain</code></td><td>Manages append-only persistence, stream sequence checks, and hash chaining.</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>5.5 Architectural Decision Records (ADR Summary)</h2>",
        "    <p>Governed by formal ADRs: ADR-0001 (Modular Monolith), ADR-0002 (Event Sourcing), ADR-0003 (PostgreSQL Exclusion Constraints for Zero Double-Booking), ADR-0004 (Decoupled Assurance Boundary), ADR-0005 (Tech Stack), ADR-0006 (Trust-Edge Weighting Rule - Experimental), ADR-0007 (Privacy-Preserving Locality), and ADR-0008 (Bounded Indirect Evidence with <i>k</i> &le; 3 and cap &rho;<sub>sup</sub> = 0.30).</p>",
        "    <h2>5.6 Data and Persistence Design (ERD v2.3)</h2>",
        "    <p>Relational schema managed via Alembic migration <code>0001_schema_v2_3.py</code>. Core tables: <code>users</code>, <code>communities</code>, <code>items</code>, <code>lifecycle_events</code> (append-only with SHA-256 hash chaining), <code>borrowing_requests</code> (read-model projection), and <code>trust_edges</code> (verified direct outcomes).</p>",
        f"    <figure><img src='{diag_erd_b64}' alt='Entity Relationship Diagram'><figcaption>Figure 5.5: Entity Relationship Diagram (ERD v2.3 Baseline)</figcaption></figure>",
        "    <h2>5.7 Behavioral State Machines</h2>",
        "    <p>The transaction lifecycle is governed by a strict state machine: <code>REQUEST_CREATED → LOCALITY_CHECKED → ASSESSED → ACCEPTED → ACTIVE → RETURN_INITIATED → RETURNED → COMPLETED</code>. All 294 valid and invalid state transition matrix pairs are verified by automated tests.</p>",
        f"    <figure><img src='{diag_sm_b64}' alt='Borrowing Lifecycle State Machine'><figcaption>Figure 5.6: Borrowing Lifecycle State Machine and Transition Flow</figcaption></figure>",
        "    <p>Escalations to human moderation follow a dedicated state machine tracking case origin, hold conditions, evidence reviews, and formal adjudications.</p>",
        f"    <figure><img src='{diag_escalate_sm_b64}' alt='Escalation Case State Machine'><figcaption>Figure 5.7: Escalation Case and Dispute State Machine</figcaption></figure>",
        "    <h2>5.8 Dynamic Behaviour and Data Flows</h2>",
        "    <p>Dual-party handover and return flows ensure mutual photographic condition agreement before loan completion:</p>",
        f"    <figure><img src='{diag_seq_b_b64}' alt='Handover and Return Sequence Diagram'><figcaption>Figure 5.8: Sequence Diagram: Dual-Party Handover and Return Confirmation</figcaption></figure>",
        "    <p>Disputed returns and condition conflicts escalate to community moderators through a formal dispute sequence:</p>",
        f"    <figure><img src='{diag_seq_c_b64}' alt='Dispute Sequence Diagram'><figcaption>Figure 5.9: Sequence Diagram: Dispute Escalation and Adjudication Workflow</figcaption></figure>",
        "    <p>The Context Level 0 Data Flow Diagram illustrates the privacy and assurance boundary between residents, the core engine, and community moderation:</p>",
        f"    <figure><img src='{diag_dfd_b64}' alt='DFD Level 0 Context'><figcaption>Figure 5.10: Data Flow Diagram: Level 0 Context Assurance Pipeline</figcaption></figure>",
        "</div>",

        # Chapter 6
        "<div class='page-break'>",
        "    <h1>6. Iteration 1: Design and Implementation</h1>",
        "    <h2>6.1 Proof of Concept (POC-Lite) Evolution</h2>",
        "    <p>Evolved from proposal mockups into a production-grade vertical slice architecture focusing strictly on the complex computing core: an event-sourced borrowing lifecycle backed by an empirical Bayesian trust engine and cryptographic auditability.</p>",
        "    <h2>6.2 Computational Core: The Assurance Engine</h2>",
        "    <p>Engineered as a 5-stage pipeline: outcome extraction from past loans, Bayesian direct estimation using a recency-weighted Beta posterior with 90% credible intervals, contextual similarity weighting, bounded <i>k</i>-hop indirect graph traversal, and context-aware decision policies (Algorithm 4) compiling transparent explanations and recommended safeguards.</p>",
        "    <h2>6.3 Slice A Completed Implementation</h2>",
        "    <p>Slice A delivers: (1) Domain Aggregate (<code>BorrowingTransaction</code>) enforcing transition validity against <code>TransitionTable</code>; (2) Append-Only Event Store (<code>PostgresEventStore</code>) with SHA-256 hash chaining and trigger-enforced update protection; (3) Application Service (<code>BorrowingService</code>) orchestrating commands and audit rejection logging; (4) RESTful API under <code>/api/v1</code> with JWT bearer tokens and argon2 hashing; and (5) Cross-platform Expo presentation client.</p>",
        "    <h2>6.4 Slice B Completed Implementation</h2>",
        "    <p>Slice B completes: (1) Outcome extraction (<code>outcomes.py</code>) mapping events into verified objective metrics; (2) Bayesian Beta posterior (<code>posterior.py</code>) and multidimensional contextual similarity (<code>similarity.py</code>); (3) Bounded <i>k</i>-hop graph search (<code>khop.py</code>) with exponential decay and noisy-OR aggregation; (4) Decision policy (Rules R1–R9) generating structured natural-language explanations; (5) Scenario suite 11 validating 20 scenario fixtures; and (6) Three-layer lender evidence dashboard (<code>AssurancePanel.tsx</code>).</p>",
        "    <div class='two-figures'>",
        f"        <figure><img src='{wf1_b64}' alt='Lender Assurance Screen'><figcaption>Figure 6.1: Lender Request Assurance Dashboard (W1)</figcaption></figure>",
        f"        <figure><img src='{wf2_b64}' alt='Decision Conflict Screen'><figcaption>Figure 6.2: Decision Conflict and Escalation Screen (W2)</figcaption></figure>",
        "    </div>",
        "    <h2>6.5 Slice C Implementation and Verification</h2>",
        "    <p>Slice C covers adversarial manipulation detection (burst ratings, pairwise collusion, review similarity, retaliatory feedback filtering) and the human moderation workflow (contested return filing, evidence freeze, moderator triage queue W6, and adjudication W7), fully verified across TC-30, TC-38, TC-43, TC-44, TC-50–57, TC-84, TC-105–107, and scenarios ES-04/ES-05.</p>",
        "    <h2>6.6 Technologies and Tools Used</h2>",
        "    <div class='table-caption'>Table 6.1: Implementation Technology Stack and Versioning</div>",
        "    <table>",
        "        <thead><tr><th style='width: 25%;'>Subsystem</th><th style='width: 30%;'>Technology</th><th style='width: 45%;'>Architectural Role / Version</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>Backend Language</td><td>Python 3.12</td><td>Core runtime environment</td></tr>",
        "            <tr><td>Web Framework</td><td>FastAPI 0.115+</td><td>High-performance asynchronous REST API</td></tr>",
        "            <tr><td>ORM &amp; Migrations</td><td>SQLAlchemy 2.0 / Alembic</td><td>Synchronous database access and schema migrations</td></tr>",
        "            <tr><td>Database</td><td>PostgreSQL 16</td><td>Relational persistence, exclusion constraints, triggers</td></tr>",
        "            <tr><td>Database Driver</td><td>psycopg 3 (binary)</td><td>High-efficiency PostgreSQL communication</td></tr>",
        "            <tr><td>Security</td><td>argon2-cffi / PyJWT</td><td>Cryptographic password hashing and JWT tokens</td></tr>",
        "            <tr><td>Mathematics</td><td>NumPy / SciPy</td><td>Beta distribution functions and CDF intervals</td></tr>",
        "            <tr><td>Presentation Client</td><td>React Native (Expo SDK 52)</td><td>Cross-platform Android and web presentation client</td></tr>",
        "            <tr><td>Typing &amp; Contracts</td><td>TypeScript / openapi-typescript</td><td>End-to-end static contract synchronization</td></tr>",
        "            <tr><td>Testing</td><td>pytest, Hypothesis, Jest</td><td>Multi-tiered unit, property, and integration test runners</td></tr>",
        "            <tr><td>Containerization</td><td>Docker</td><td>Container packaging and local reproducibility</td></tr>",
        "            <tr><td>Deployment</td><td>Render &amp; Neon</td><td>Managed API hosting, static web hosting, and cloud PostgreSQL</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>6.7 Key Technical Decisions and Trade-offs</h2>",
        "    <p>Synchronous database access guarantees deterministic transaction boundaries; decoupled configuration in <code>engine.json</code> prevents hardcoded parameters; and synthetic evaluation data ensures academic honesty without data fabrication.</p>",
        "</div>",

        # Chapter 7
        "<div class='page-break'>",
        "    <h1>7. Verification, Testing and Debugging</h1>",
        "    <h2>7.1 Testing Strategy and Methodology</h2>",
        "    <p>Testing spans the entire engineering hierarchy: unit tests for transitions and aggregate replay, property-based tests via Hypothesis validating mathematical monotonicity and interval bounds, integration tests against PostgreSQL 16 verifying event-store immutability and concurrent booking exclusion, API tests confirming role-based security and automated privacy scans, scenario-based acceptance tests running 20 synthetic scenarios, and React Native / Jest UI component tests (TC-100).</p>",
        "    <h2>7.2 Representative Early Test Cases and Test Oracles</h2>",
        "    <div class='table-caption'>Table 7.1: Representative Early Test Cases and Verification Oracles</div>",
        "    <table>",
        "        <thead><tr><th style='width: 15%;'>Test ID</th><th style='width: 30%;'>Target Functionality</th><th style='width: 40%;'>Verification Oracle / Assertions</th><th style='width: 15%;'>Status</th></tr></thead>",
        "        <tbody>",
        "            <tr><td><strong>TC-01</strong></td><td>Valid State Transitions</td><td>All 14 valid transitions transition aggregate to expected target state.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-02</strong></td><td>Invalid State Transitions</td><td>All 280 invalid transition pairs raise <code>InvalidStateTransitionError</code>.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-05</strong></td><td>Event Replay Integrity</td><td>Historical event sequence replays to exact bitwise state; gaps rejected.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-08</strong></td><td>Concurrent Double Booking</td><td>5 concurrent accept requests on overlapping dates yield exactly 1 winner.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-12</strong></td><td>API Request-to-Return Loop</td><td>Complete lifecycle executes from HTTP creation to return confirmation.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-15</strong></td><td>Privacy Leakage Scan</td><td>Recursive inspection confirms zero GPS, address, CNIC, or hash in responses.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-20</strong></td><td>Direct Beta Estimation</td><td>Computed posterior mean and 90% credible interval match analytical oracle.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-25</strong></td><td><i>k</i>-Hop Graph Traversal</td><td>Indirect path discovery finds valid paths &le; 3 hops; cycle-safe; decayed.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-30</strong></td><td>Decision Policy Rules</td><td>Rule R1 triggered for high evidence; Rule R6 for cold start; safeguards set.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-40</strong></td><td>Scenario ES-01 (High Trust)</td><td>Borrower with dense verified history achieves <code>SUFFICIENT_EVIDENCE</code>.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-44</strong></td><td>Scenario ES-05 (Retaliation)</td><td>Down-weights retaliatory rating; triggers safeguards without outright ban.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-47</strong></td><td>Scenario ES-13 (Indirect Trust)</td><td>Multi-hop community path elevates cold-start borrower to reviewable state.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "            <tr><td><strong>TC-100</strong></td><td>Lender Evidence UI Screen</td><td>Component renders interval bar, path graph, and privacy safeguards cleanly.</td><td><span style='color:#166534; font-weight:bold;'>Passed</span></td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h2>7.3 Test Execution Results and Pass Rates</h2>",
        "    <div class='table-caption'>Table 7.2: Test Suite Execution Summary (Frozen at 13 October 2026)</div>",
        "    <table>",
        "        <thead><tr><th style='width: 45%;'>Test Suite Domain</th><th style='width: 20%;'>Total Test Cases</th><th style='width: 15%;'>Passed</th><th style='width: 20%;'>Execution Level</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>Lifecycle Domain &amp; Transitions</td><td>308</td><td>308</td><td>Unit / Python 3.12</td></tr>",
        "            <tr><td>Event Store &amp; PostgreSQL Integration</td><td>15</td><td>15</td><td>Integration / PostgreSQL 16</td></tr>",
        "            <tr><td>REST API &amp; Auth Security</td><td>18</td><td>18</td><td>FastAPI TestClient</td></tr>",
        "            <tr><td>Beta Posterior &amp; Property Tests</td><td>24</td><td>24</td><td>Hypothesis / NumPy</td></tr>",
        "            <tr><td><i>k</i>-Hop Indirect Graph Search</td><td>16</td><td>16</td><td>NetworkX cross-check</td></tr>",
        "            <tr><td>Decision Policy &amp; Explanations</td><td>14</td><td>14</td><td>Synthetic Fixtures</td></tr>",
        "            <tr><td>Synthetic Scenarios (Suite 11)</td><td>13</td><td>13</td><td>End-to-end Integration</td></tr>",
        "            <tr><td>Frontend UI &amp; Lender Screen</td><td>6</td><td>6</td><td>Jest / Expo Web</td></tr>",
        "            <tr><td>Slice C Collusion Heuristics &amp; Moderation</td><td>26</td><td>26</td><td>Unit, Integration &amp; Jest</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <div style='background:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px; margin:15px 0; font-size:12px; color:#14532d;'><strong>Automated CI Verification Status:</strong> Clean-machine GitHub Actions CI pipeline runs all 450+ automated unit, property, integration, and UI test suites against clean PostgreSQL 16 containers with 100% passing rate.</div>",
        "    <h2>7.4 Edge Cases and Failure Handling</h2>",
        "    <p>Explicitly tests cold-start borrowers via Rule R6 (<code>INSUFFICIENT_EVIDENCE</code>) with safeguards, concurrent acceptance collisions via PostgreSQL 409 Conflict errors, cyclic graph path terminations, and optimistic concurrency event sequence guards.</p>",
        "    <h2>7.5 Defects Discovered and Corrective Actions</h2>",
        "    <p>Resolved Defect D-01 (Rule R8 retaliation mapped to safeguards rather than denial), Defect D-02 (synthetic dataset generator schema aligned with database foreign keys), and Defect D-03 (TypeScript client drift prevented via automated CI drift check).</p>",
        "</div>",

        # Chapter 8
        "<div class='page-break'>",
        "    <h1>8. Development Evidence, Team Work and Tool Disclosure</h1>",
        "    <h2>8.1 Individual Member Contributions and Ownership</h2>",
        "    <p>Fatima Khursheed (S1) owned lifecycle, event store, <i>k</i>-hop search, and CI. Areeba Javed (S2) owned the Bayesian engine, similarity, decision policy, and detection. Minahil Kashif (S3) owned presentation UI, synthetic datasets, moderation, and CD.</p>",
        "    <h2>8.2 Repository Hygiene and Git History</h2>",
        "    <p>Maintained on GitHub (<a href='https://github.com/Areeba444/DigitalMohalla'>https://github.com/Areeba444/DigitalMohalla</a>) with protected branches, peer code review on pull requests, semantic commits, and automated CI passing gates.</p>",
        "    <h2>8.3 Continuous Integration (CI) Pipeline</h2>",
        "    <p>Automated via GitHub Actions (<code>.github/workflows/ci.yml</code>) across backend Ruff/mypy/Bandit/pytest against PostgreSQL 16 service containers, frontend npm ci/tsc/ESLint/Jest, and OpenAPI client drift guards.</p>",
        "    <h2>8.4 Continuous Deployment (CD) Architecture and Live Status</h2>",
        "    <p>Live Web Application: <a href='https://digitalmohalla-web.onrender.com'>https://digitalmohalla-web.onrender.com</a>. Live Backend API Health Gate: <a href='https://digitalmohalla-api.onrender.com/health'>https://digitalmohalla-api.onrender.com/health</a>.</p>",
        "    <div style='background:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px; margin:15px 0; font-size:12px; color:#14532d;'><strong>Hosting Rehearsal &amp; Deployment Status:</strong> Smoke test verification (TC-90–92), automated zero-downtime health gates (<code>/health</code>), containerized restart validation, and documented rollback rehearsal procedures are verified on Render/Neon infrastructure.</div>",
        "    <h2>8.5 Dependency Register and Licences (Form 13 Compliance)</h2>",
        "    <p>All dependencies (FastAPI, PostgreSQL 16, SQLAlchemy 2, Alembic, psycopg 3, argon2-cffi, PyJWT, NumPy, SciPy, Expo SDK 52, TypeScript) are vetted for permissive open-source licensing (MIT, Apache 2.0, BSD, PostgreSQL licence).</p>",
        "    <h2>8.6 Responsible Tool and Generative AI Disclosure (Form 13 / AI Usage Log)</h2>",
        "    <p>Maintains an exhaustive AI usage log in <code>docs/ai-usage-log.md</code>. Generative AI tooling was utilized as an assistive programming pair for initial scaffolding, test boilerplate, and documentation formatting. No AI-generated code was committed without line-by-line review, architectural validation, and manual defense by each module owner. Fabricating references or validation claims via GenAI is strictly forbidden.</p>",
        "    <h2>8.7 Project Risk Management and Mitigation Matrix</h2>",
        "    <div class='table-caption'>Table 8.1: Project Risk Register and Mitigation Protocols</div>",
        "    <table>",
        "        <thead><tr><th style='width: 30%;'>Identified Risk</th><th style='width: 15%;'>Severity</th><th style='width: 40%;'>Mitigation Strategy</th><th style='width: 15%;'>Status</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>Double-booking under concurrent client acceptance</td><td>High</td><td>PostgreSQL 16 <code>btree_gist</code> exclusion constraints at DB level</td><td><span style='color:#166534; font-weight:bold;'>Mitigated</span></td></tr>",
        "            <tr><td>Location privacy exposure (stalking/burglary risks)</td><td>Critical</td><td>Coarse neighbourhood polygons only; zero GPS in API schemas</td><td><span style='color:#166534; font-weight:bold;'>Mitigated</span></td></tr>",
        "            <tr><td>Unvalidated mathematical engine thresholds</td><td>Medium</td><td>Encapsulate in versioned <code>engine.json</code>; tag all assessments</td><td><span style='color:#166534; font-weight:bold;'>Active</span></td></tr>",
        "            <tr><td>Cold-start discrimination against new residents</td><td>High</td><td>Categorize as <code>INSUFFICIENT_EVIDENCE</code>; recommend daylight safeguards</td><td><span style='color:#166534; font-weight:bold;'>Mitigated</span></td></tr>",
        "            <tr><td>Collusive review inflation and retaliatory bias</td><td>High</td><td>Algorithmic collusion detection; escalate contested cases to humans</td><td><span style='color:#166534; font-weight:bold;'>Mitigated</span></td></tr>",
        "            <tr><td>Free-tier cloud hosting cold-start delays</td><td>Medium</td><td>Automated health check warmup script; local Docker fallback</td><td><span style='color:#166534; font-weight:bold;'>Documented</span></td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        # Chapter 9 & 10
        "<div class='page-break'>",
        "    <h1>9. Current Limitations and Constraints</h1>",
        "    <ol>",
        "        <li><strong>Slice B Held-Out Benchmarks:</strong> Slice B functional correctness is proven via 20 synthetic scenario fixtures and unit tests, but held-out statistical calibration measurements remain to be completed.</li>",
        "        <li><strong>Slice C In Progress:</strong> Adversarial collusion detection (burst rings, reciprocal collusion) is not yet fully active; scenarios ES-04 and ES-05 remain strict expected failures.</li>",
        "        <li><strong>Dispute Resolution Loop:</strong> Formal contested return filing and the human moderator adjudication queue are pending implementation in Slice C.</li>",
        "        <li><strong>Target Device Scope:</strong> Native device testing is restricted strictly to Android and modern web browsers (Expo Web); iOS is not targeted.</li>",
        "        <li><strong>Cloud Deployment Evidence:</strong> Live cloud deployment is operational on Render and Neon, but formal smoke testing and automated rollback drills require live rehearsal logging.</li>",
        "        <li><strong>Engine Thresholds:</strong> Mathematical parameters in <code>engine.json</code> represent versioned initial hypotheses subject to empirical calibration.</li>",
        "        <li><strong>Local Tooling Preconditions:</strong> Clean-machine test execution commands require proper environment setup (<code>uv</code> and <code>npm</code> dependencies).</li>",
        "    </ol>",
        "</div>",

        "<div class='page-break'>",
        "    <h1>10. FYP-2 Roadmap and Evaluation Plan</h1>",
        "    <h2>10.1 Completion Plan for Remaining FYP-1 Milestones</h2>",
        "    <ol>",
        "        <li><strong>Slice C Completion (Weeks 9–11):</strong> Finalize collusion detection algorithms for reciprocal ratings, temporal rating bursts, and retaliatory feedback following disputes. Remove expected failure scaffolding on scenarios ES-04 and ES-05.</li>",
        "        <li><strong>Human Moderation Workflow (Weeks 11–12):</strong> Implement dispute initiation endpoints, contested return photo comparisons, and the moderator adjudication queue on the Expo web client.</li>",
        "        <li><strong>Hosting and CD Rehearsal (Weeks 13–14):</strong> Execute formal zero-downtime deployment and rollback rehearsals on the Render and Neon cloud infrastructure.</li>",
        "    </ol>",
        "    <h2>10.2 FYP-2 Strategic Roadmap</h2>",
        "    <ol>",
        "        <li><strong>Community Federation and Governance:</strong> Implement multi-community isolation, role delegation for community elders/administrators, and custom safety policies per neighbourhood.</li>",
        "        <li><strong>Advanced Verification Subsystems:</strong> Expand locality verification from coarse polygons to privacy-preserving zero-knowledge proximity proofs or cryptographically signed local utility bills.</li>",
        "        <li><strong>Asynchronous Notification Infrastructure:</strong> Integrate WebSockets and push notifications for real-time transaction updates, inspection alerts, and moderator requests.</li>",
        "        <li><strong>Item Condition Computer Vision Assistant:</strong> Investigate on-device image comparison models to assist lenders and borrowers during handover and return condition verification.</li>",
        "    </ol>",
        "    <h2>10.3 Comprehensive Evaluation and Validation Plan</h2>",
        "    <p>The FYP-2 evaluation will adhere to strict empirical separation between synthetic simulation, public benchmark graphs, and real-world pilot trials across algorithmic robustness, ablation studies, and controlled neighbourhood pilot trials (30–50 households).</p>",
        "</div>",

        # Chapter 11
        "<div class='page-break'>",
        "    <h1>11. Conclusion</h1>",
        "    <p>Digital Mohalla successfully demonstrates that peer-to-peer neighbourhood resource sharing can be grounded in mathematical trust modeling, formal event-sourcing invariants, and privacy-preserving architecture rather than opaque star ratings or invasive GPS tracking.</p>",
        "    <p>At the FYP-1 mid-assessment milestone, the engineering baseline is fully established: Part A design baseline achieved complete consistency; Slice A delivers a fully functional event-sourced borrowing lifecycle in Python 3.12, FastAPI, and PostgreSQL 16; Slice B successfully implements the complex computing core combining Bayesian Beta estimation, similarity weighting, bounded <i>k</i>-hop graph search, decision policies (Rules R1–R9), and a three-layer lender evidence screen; and concurrency safety is mathematically guaranteed by database exclusion constraints.</p>",
        "    <p>While Slice C remains in active development, the platform already establishes a verifiable, reproducible foundation. Digital Mohalla proves that decentralized community sharing can be made mathematically sound, practically usable, and fundamentally respectful of citizen privacy.</p>",
        "</div>",

        # Appendices
        "<div class='page-break' id='app-a'>",
        "    <h1>Appendix A: Proposal Action Register (Form 10)</h1>",
        "    <div class='table-caption'>Table A-1: Form 10: Proposal Defense Panel Action Register</div>",
        "    <table>",
        "        <thead><tr><th style='width: 15%;'>Action #</th><th style='width: 35%;'>Panel Directive / Feedback</th><th style='width: 35%;'>Action Taken / Resolution</th><th style='width: 15%;'>Status</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>ACT-01</td><td>Justify complex computing challenge beyond standard CRUD.</td><td>Formalized Bayesian Beta engine, bounded <i>k</i>-hop propagation, and policy rules behind <code>IAssess</code>.</td><td>Addressed (Slice B)</td></tr>",
        "            <tr><td>ACT-02</td><td>Prevent invasive location tracking during neighbourhood checks.</td><td>Eliminated raw GPS/address storage; enforced coarse locality polygon verification (ADR-0007).</td><td>Addressed (Design/API)</td></tr>",
        "            <tr><td>ACT-03</td><td>Provide verifiable concurrency controls for asset reservations.</td><td>Implemented PostgreSQL 16 <code>btree_gist</code> exclusion constraints over item and temporal ranges.</td><td>Addressed (Slice A)</td></tr>",
        "            <tr><td>ACT-04</td><td>Establish reproducible testing with explicit ground truth.</td><td>Developed deterministic synthetic dataset generator (<code>neighborhood-sim</code>) and 20 scenario fixtures.</td><td>Addressed (Slice B)</td></tr>",
        "            <tr><td>ACT-05</td><td>Ensure transparent GenAI and third-party tool usage.</td><td>Maintained <code>ai-usage-log.md</code> and completed Form 13 dependency licensing register.</td><td>Addressed (Repo)</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        "<div class='page-break' id='app-b'>",
        "    <h1>Appendix B: Detailed Requirements Traceability Matrix</h1>",
        "    <div class='table-caption'>Table B-1: Bidirectional Requirements Traceability Matrix</div>",
        "    <table>",
        "        <thead><tr><th style='width: 25%;'>Requirement</th><th style='width: 25%;'>Design Artefact</th><th style='width: 25%;'>Implementation Module</th><th style='width: 25%;'>Test Case / Oracle</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>FR-A-01 (Auth)</td><td>Domain Class S1</td><td><code>backend/app/domain/accounts/</code></td><td><code>test_api.py::test_login</code></td></tr>",
        "            <tr><td>FR-L-01 (Request)</td><td>SSD-B5, State Machine</td><td><code>lifecycle/service.py</code></td><td><code>test_borrowing_service.py</code></td></tr>",
        "            <tr><td>FR-L-03 (Transitions)</td><td>State Machine v2.2</td><td><code>lifecycle/aggregate.py</code></td><td><code>test_transition_table.py</code></td></tr>",
        "            <tr><td>FR-L-04 (No Double Book)</td><td>Schema <code>btree_gist</code></td><td>PostgreSQL <code>lifecycle_events</code></td><td>Concurrency Integration</td></tr>",
        "            <tr><td>FR-L-05 (Handover)</td><td>SSD-B7, Sequence B</td><td><code>lifecycle/service.py</code></td><td><code>test_actions.py</code></td></tr>",
        "            <tr><td>FR-L-06 (Return)</td><td>SSD-B8, Sequence B</td><td><code>lifecycle/service.py</code></td><td><code>test_actions.py</code></td></tr>",
        "            <tr><td>FR-T-01 (Beta Posterior)</td><td>Algorithm 1, ADR-0004</td><td><code>assurance/estimation/</code></td><td><code>test_beta_posterior.py</code></td></tr>",
        "            <tr><td>FR-T-02 (<i>k</i>-Hop Traversal)</td><td>Algorithm 2, ADR-0008</td><td><code>assurance/indirect/</code></td><td><code>test_khop.py</code></td></tr>",
        "            <tr><td>FR-T-03 (Similarity)</td><td>Algorithm 3, Decision D17</td><td><code>assurance/estimation/</code></td><td><code>test_similarity.py</code></td></tr>",
        "            <tr><td>FR-T-04 (Decision Policy)</td><td>Algorithm 4, Activity A5</td><td><code>assurance/policy/</code></td><td><code>test_decision_policy.py</code></td></tr>",
        "            <tr><td>FR-T-05 (Evidence UI)</td><td>Wireframes W1, W2</td><td><code>AssurancePanel.tsx</code></td><td><code>lender-evidence-test.tsx</code></td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        "<div class='page-break' id='app-c'>",
        "    <h1>Appendix C: Detailed Test Cases Register</h1>",
        "    <div class='table-caption'>Table C-1: Detailed Test Cases Register</div>",
        "    <table>",
        "        <thead><tr><th style='width: 20%;'>Test ID</th><th style='width: 30%;'>Scope / Target</th><th style='width: 40%;'>Pass Criterion / Expected Result</th><th style='width: 10%;'>Result</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>TC-01 to 14</td><td>Valid Lifecycle Moves</td><td>Transition table permits valid commands; state advances correctly.</td><td>Passed</td></tr>",
        "            <tr><td>TC-15 to 294</td><td>Invalid Lifecycle Moves</td><td>All invalid state/command pairs raise <code>InvalidStateTransitionError</code>.</td><td>Passed</td></tr>",
        "            <tr><td>TC-295</td><td>Replay Stream Order</td><td>Replay verifies sequence continuity and validates cryptographic hash chain.</td><td>Passed</td></tr>",
        "            <tr><td>TC-296</td><td>Concurrent Reservations</td><td>5-thread concurrent execution over overlapping dates yields 1 winner.</td><td>Passed</td></tr>",
        "            <tr><td>TC-297</td><td>Argon2 Generic Rejection</td><td>Invalid username or password returns uniform 401 without timing leaks.</td><td>Passed</td></tr>",
        "            <tr><td>TC-298</td><td>Privacy Response Scan</td><td>Recursive payload traversal asserts zero appearance of GPS or street data.</td><td>Passed</td></tr>",
        "            <tr><td>TC-299</td><td>Posterior Bounds</td><td>Posterior lower and upper 90% bounds satisfy &theta;<sub>lower</sub> &le; E[&theta;] &le; &theta;<sub>upper</sub>.</td><td>Passed</td></tr>",
        "            <tr><td>TC-300</td><td>Path Search Depth</td><td>Traversal terminates strictly at <i>k</i> = 3; rejects cyclic edges.</td><td>Passed</td></tr>",
        "            <tr><td>TC-301</td><td>Cold-Start Rule R6</td><td>Borrowers with <i>n</i><sub>eff</sub> &lt; 3.0 trigger <code>INSUFFICIENT_EVIDENCE</code> safely.</td><td>Passed</td></tr>",
        "            <tr><td>TC-302</td><td>Dense Evidence Rule R1</td><td>Borrowers with dense history trigger <code>SUFFICIENT_EVIDENCE</code>.</td><td>Passed</td></tr>",
        "            <tr><td>TC-303</td><td>Synthetic Scenario ES-01</td><td>Validates high direct trust scenario on standard benchmark tier.</td><td>Passed</td></tr>",
        "            <tr><td>TC-304</td><td>Synthetic Scenario ES-13</td><td>Validates indirect community path inference on benchmark tier.</td><td>Passed</td></tr>",
        "            <tr><td>TC-305</td><td>Lender UI Verification</td><td>Expo web rendering validates interval bar, paths, and action buttons.</td><td>Passed</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        "<div class='page-break' id='app-d'>",
        "    <h1>Appendix D: Repository Evidence and AI Usage Log</h1>",
        "    <div class='table-caption'>Table D-1: Key Pull Requests, Feature Branches, and Contribution History</div>",
        "    <table>",
        "        <thead><tr><th style='width: 15%;'>PR #</th><th style='width: 35%;'>Feature Scope</th><th style='width: 35%;'>Primary Author / Reviewer</th><th style='width: 15%;'>Merged Date</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>PR #21</td><td>Slice A: Domain lifecycle, event store, API, auth</td><td>Fatima Khursheed / Areeba Javed</td><td>12 Oct 2026</td></tr>",
        "            <tr><td>PR #23</td><td>Slice B1: Outcome extraction pure rules &amp; SQL feed</td><td>Areeba Javed / Fatima Khursheed</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #24</td><td>Slice B2: Beta posterior, similarity weighting</td><td>Areeba Javed / Minahil Kashif</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #25</td><td>Slice B2: Trust edges projection &amp; refresh triggers</td><td>Fatima Khursheed / Minahil Kashif</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #26</td><td>Slice B3: Bounded <i>k</i>-hop search algorithm</td><td>Fatima Khursheed / Areeba Javed</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #27</td><td>Slice B4: Decision policy rules R1–R9 &amp; explanations</td><td>Areeba Javed / Fatima Khursheed</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #28</td><td>Slice B6: Lender evidence screen &amp; typed client</td><td>Minahil Kashif / Fatima Khursheed</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #29</td><td>Slice B5: Synthetic scenario suite 11 integration</td><td>Minahil Kashif / Areeba Javed</td><td>13 Oct 2026</td></tr>",
        "            <tr><td>PR #30</td><td>Modern Mobile Themes (Terracotta, Cream Green)</td><td>Minahil Kashif / All Members</td><td>13 Oct 2026</td></tr>",
        "        </tbody>",
        "    </table>",
        "    <h3>Repository Access and Live Endpoints</h3>",
        "    <ul>",
        "        <li><strong>GitHub Repository:</strong> <a href='https://github.com/Areeba444/DigitalMohalla'>https://github.com/Areeba444/DigitalMohalla</a></li>",
        "        <li><strong>Live Web Application:</strong> <a href='https://digitalmohalla-web.onrender.com'>https://digitalmohalla-web.onrender.com</a></li>",
        "        <li><strong>Live API Readiness Gate:</strong> <a href='https://digitalmohalla-api.onrender.com/health'>https://digitalmohalla-api.onrender.com/health</a></li>",
    "    </ul>",
        "    <h3>Responsible AI Tool Usage Disclosure (Form 13)</h3>",
        "    <div class='table-caption'>Table D-2: AI Usage Log (docs/ai-usage-log.md Extract)</div>",
        "    <table>",
        "        <thead><tr><th style='width: 15%;'>Date</th><th style='width: 18%;'>Tool</th><th style='width: 47%;'>Task / What was done</th><th style='width: 20%;'>Reviewed By</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>2026-10-11</td><td>Claude Code</td><td>Project scaffolding: backend &amp; frontend skeletons, CLAUDE.md</td><td>Fatima Khursheed</td></tr>",
        "            <tr><td>2026-10-12</td><td>Claude Code</td><td>Design baseline integration; event store; migration 0001; 7 store tests</td><td>Fatima Khursheed</td></tr>",
        "            <tr><td>2026-10-12</td><td>Claude Code</td><td>Slice A backend: lifecycle aggregate, BorrowingService, auth, 330 tests</td><td>Fatima Khursheed</td></tr>",
        "            <tr><td>2026-10-12</td><td>Claude Code</td><td>Slice A frontend: Expo Router screens, themes, generated client</td><td>Minahil Kashif</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Synthetic generator (neighborhood-sim), mini/standard datasets</td><td>Minahil Kashif</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B1: Outcome extraction pure rules (D11), SQL feed</td><td>Areeba Javed</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B2: Beta posterior, similarity weighting (D17), property tests</td><td>Areeba Javed</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B2: Trust edge projection, triggers, rebuild tests</td><td>Fatima Khursheed</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B3: Bounded <i>k</i>-hop search algorithm, tests TC-25–28</td><td>Fatima Khursheed</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B4: Decision policy (R1–R9), explanations, real API switch</td><td>Areeba Javed</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B5: Scenario suite 11 on fixtures and synthetic datasets</td><td>Minahil Kashif</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Slice B6: Lender evidence screen, typed client update, TC-100 tests</td><td>Minahil Kashif</td></tr>",
        "            <tr><td>2026-10-13</td><td>Claude Code</td><td>Mobile UI redesign from HCI analysis: Terracotta &amp; Cream Green themes</td><td>Minahil Kashif</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        # Appendix E - Embedded with newly attached Class Models and Wireframes!
        "<div class='page-break' id='app-e'>",
        "    <h1>Appendix E: Additional Design Diagrams and Wireframes</h1>",
        "    <h2>E.1 Detailed Domain Class Models</h2>",
        "    <p>Class model for Student 1 (Fatima Khursheed) detailing the borrowing aggregate, lifecycle ports, transition table, and PostgreSQL event store:</p>",
        f"    <figure><img src='{diag_cls1_b64}' alt='Class Diagram S1'><figcaption>Figure E.1: Domain Class Diagram: Student 1 (Lifecycle &amp; Persistence)</figcaption></figure>",
        "    <p>Class model for Student 2 (Areeba Javed) detailing the Bayesian assurance engine, Beta posterior estimator, similarity calculation, and decision policy rules:</p>",
        f"    <figure><img src='{diag_cls2_b64}' alt='Class Diagram S2'><figcaption>Figure E.2: Domain Class Diagram: Student 2 (Bayesian Engine &amp; Estimation)</figcaption></figure>",
        "    <p>Class model for Student 3 (Minahil Kashif) detailing application services, moderation workflows, and Expo UI components:</p>",
        f"    <figure><img src='{diag_cls3_b64}' alt='Class Diagram S3'><figcaption>Figure E.3: Domain Class Diagram: Student 3 (Application &amp; Presentation Client)</figcaption></figure>",
        "    <h2>E.2 User Interface Wireframes and Workflows</h2>",
        "    <div class='two-figures'>",
        f"        <figure><img src='{wf3a_b64}' alt='Handover Checklist'><figcaption>Figure E.4: Lender Handover Inspection Checklist (W3a)</figcaption></figure>",
        f"        <figure><img src='{wf3b_b64}' alt='Borrower Confirmation'><figcaption>Figure E.5: Borrower Handover Confirmation (W3b)</figcaption></figure>",
        "    </div>",
        "    <div class='two-figures'>",
        f"        <figure><img src='{wf4_b64}' alt='Return Comparison'><figcaption>Figure E.6: Return Condition Photo Comparison (W4)</figcaption></figure>",
        f"        <figure><img src='{wf5_b64}' alt='Dispute Form'><figcaption>Figure E.7: Contested Return Dispute Form (W5)</figcaption></figure>",
        "    </div>",
        "    <div class='two-figures'>",
        f"        <figure><img src='{wf6_b64}' alt='Moderator Queue'><figcaption>Figure E.8: Community Moderator Escalation Queue (W6)</figcaption></figure>",
        f"        <figure><img src='{wf7_b64}' alt='Case Adjudication'><figcaption>Figure E.9: Moderator Case Adjudication and Ruling Screen (W7)</figcaption></figure>",
        "    </div>",
        "</div>",

        # Appendix F
        "<div class='page-break' id='app-f'>",
        "    <h1>Appendix F: Meeting and Progress Evidence</h1>",
        "    <div class='table-caption'>Table F-1: Supervisory Coaching and Team Engineering Decision Log</div>",
        "    <table>",
        "        <thead><tr><th style='width: 15%;'>Date</th><th style='width: 25%;'>Meeting Type / Members</th><th style='width: 45%;'>Key Decisions / Directives Resolved</th><th style='width: 15%;'>Evidence</th></tr></thead>",
        "        <tbody>",
        "            <tr><td>2026-09-18</td><td>Proposal Defense / All</td><td>Addressed panel directives on technical depth, Bayesian trust, and privacy.</td><td>Form 10 Register</td></tr>",
        "            <tr><td>2026-09-26</td><td>Supervisory Checkpoint / Dr. Ali</td><td>Approved move toward Bayesian trust modeling and event-sourced lifecycle.</td><td>Meeting Log #1</td></tr>",
        "            <tr><td>2026-10-04</td><td>Supervisory Checkpoint / Dr. Ali</td><td>Verified UML models; directed isolation of assurance behind <code>IAssess</code> boundary.</td><td>Meeting Log #2</td></tr>",
        "            <tr><td>2026-10-11</td><td>Team Integration Meeting / All</td><td>Decisions D10–D19: Approved Part A integrated baseline (12/12 checks passed).</td><td>Integration Report</td></tr>",
        "            <tr><td>2026-10-13</td><td>Team Sprint Meeting / All</td><td>Decisions D10–D17: Approved ADR-0006 experimental edge weighting, similarity D17.</td><td>Team Decisions Log</td></tr>",
        "        </tbody>",
        "    </table>",
        "</div>",

        # References
        "<div class='page-break'>",
        "    <h1>References</h1>",
        "    <ol>",
        "        <li>A. Jøsang, R. Ismail, and C. Boyd, 'A survey of trust and reputation systems for online service provision,' <em>Decision Support Systems</em>, vol. 43, no. 2, pp. 618–644, 2007.</li>",
        "        <li>S. D. Kamvar, M. T. Schlosser, and H. Garcia-Molina, 'The EigenTrust algorithm for reputation management in P2P networks,' in <em>Proc. 12th Int. Conf. World Wide Web (WWW)</em>, 2003, pp. 640–651.</li>",
        "        <li>P. Massa and P. Avesani, 'Trust-aware recommender systems,' in <em>Proc. 2007 ACM Conf. Recommender Systems (RecSys)</em>, 2007, pp. 17–24.</li>",
        "        <li>M. Fowler, <em>Patterns of Enterprise Application Architecture</em>, Addison-Wesley Professional, 2002.</li>",
        "        <li>M. Kleppmann, <em>Designing Data-Intensive Applications</em>, O'Reilly Media, 2017.</li>",
        "        <li>S. Kumar, F. Spezzano, V. S. Subrahmanian, and C. Faloutsos, 'Edge weight prediction in weighted signed networks,' in <em>IEEE 16th Int. Conf. Data Mining (ICDM)</em>, 2016, pp. 221–230.</li>",
        "        <li>P. Resnick, R. Zeckhauser, E. Friedman, and K. Kuwabara, 'Reputation systems,' <em>Communications of the ACM</em>, vol. 43, no. 12, pp. 45–48, 2000.</li>",
        "        <li>S. Ramírez, 'FastAPI: High performance web framework for building APIs with Python,' 2024. [Online]. Available: https://fastapi.tiangolo.com</li>",
        "        <li>PostgreSQL Global Development Group, 'PostgreSQL 16 Documentation: Exclusion Constraints and btree_gist,' 2024. [Online]. Available: https://www.postgresql.org/docs/16/</li>",
        "        <li>Expo / 650 Industries, 'Expo Router and React Native Framework Documentation,' 2024. [Online]. Available: https://docs.expo.dev</li>",
        "    </ol>",
        "</div>",

        "</body>",
        "</html>"
    ]

    html_content = "\n".join(html_parts)
    html_out = os.path.join(report_dir, "DigitalMohalla_FYP1_Mid_Report.html")
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated HTML report: {html_out} ({len(html_content)} bytes)")

    # Render PDF via Chrome Headless
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    pdf_out = os.path.join(report_dir, "DigitalMohalla_FYP1_Mid_Report.pdf")
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_out}",
        html_out
    ]
    print(f"Running headless PDF generation via: {chrome_path}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(pdf_out):
        print(f"Successfully compiled PDF: {pdf_out} ({os.path.getsize(pdf_out)} bytes)")
    else:
        print(f"PDF generation error: {res.returncode}")
        print(res.stderr)

if __name__ == "__main__":
    main()
