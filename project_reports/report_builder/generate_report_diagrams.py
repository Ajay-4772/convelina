"""
Generate 7 high-resolution UML and System Design Diagrams for Chapter 4 of the CONVELINA Project Report.
Matches IEEE and university engineering report design standards.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import os

os.makedirs("report_assets", exist_ok=True)

# Common styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

def draw_box(ax, x, y, w, h, title, subtitle="", color="#E2E8F0", border="#475569", radius=0.03):
    box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={radius}",
                         facecolor=color, edgecolor=border, linewidth=1.5, zorder=2)
    ax.add_patch(box)
    if title:
        if subtitle:
            ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F172A', zorder=3)
            ax.text(x + w/2, y + h*0.30, subtitle, ha='center', va='center', fontsize=7.5, color='#334155', zorder=3)
        else:
            ax.text(x + w/2, y + h*0.5, title, ha='center', va='center', fontsize=9, fontweight='bold', color='#0F172A', zorder=3)

def draw_arrow(ax, x1, y1, x2, y2, label="", color="#334155", lw=1.5, rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw,
                                connectionstyle=f"arc3,rad={rad}"), zorder=4)
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        ax.text(mx, my + 0.02, label, ha='center', va='bottom', fontsize=7.5, fontweight='semibold', color='#0F172A',
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#CBD5E1", lw=0.8, alpha=0.9), zorder=5)

# ==============================================================================
# 1. FIG 4.1: SYSTEM ARCHITECTURE DIAGRAM
# ==============================================================================
def make_fig_4_1():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Background container panels
    # Layer 1: Client
    p1 = FancyBboxPatch((0.4, 7.2), 9.2, 2.2, boxstyle="round,pad=0.02", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=1, ls="--")
    ax.add_patch(p1)
    ax.text(0.6, 9.1, "PRESENTATION LAYER (Next.js 14 App Router / TailwindCSS / Lucide)", fontsize=9, fontweight='bold', color='#1E293B')

    draw_box(ax, 0.8, 7.5, 2.6, 1.4, "Citizen Workspace UI", "Next.js App / Client Portal", "#EFF6FF", "#3B82F6")
    draw_box(ax, 3.7, 7.5, 2.6, 1.4, "Admin Verification UI", "Government Officer Dashboard", "#F5F3FF", "#8B5CF6")
    draw_box(ax, 6.6, 7.5, 2.6, 1.4, "Document Discrepancy UI", "Diff Inspection & Affidavit Preview", "#ECFDF5", "#10B981")

    # Layer 2: API Gateway & Services
    p2 = FancyBboxPatch((0.4, 3.7), 9.2, 3.0, boxstyle="round,pad=0.02", facecolor="#F1F5F9", edgecolor="#64748B", lw=1, ls="--")
    ax.add_patch(p2)
    ax.text(0.6, 6.4, "APPLICATION & BUSINESS LOGIC LAYER (FastAPI / Asynchronous Workers)", fontsize=9, fontweight='bold', color='#1E293B')

    draw_box(ax, 0.8, 4.0, 2.0, 2.1, "Auth & Role Scoping", "Firebase Auth / JWT\nForced Session Context", "#F8FAFC", "#64748B")
    draw_box(ax, 3.0, 4.0, 2.0, 2.1, "OCR Ingestion Pipeline", "Tesseract / PaddleOCR\nAadhaar/PAN Parsers", "#EFF6FF", "#2563EB")
    draw_box(ax, 5.2, 4.0, 2.0, 2.1, "Conflict Engine", "Multi-Algorithmic Fuzzy\nJaro-Winkler & Token Sort", "#FEF3C7", "#D97706")
    draw_box(ax, 7.4, 4.0, 2.0, 2.1, "RAG Knowledge Base", "LangChain / Gemini API\nIndian Govt Statutes", "#F0FDF4", "#059669")

    # Layer 3: Persistence & Security
    p3 = FancyBboxPatch((0.4, 0.4), 9.2, 2.8, boxstyle="round,pad=0.02", facecolor="#F8FAFC", edgecolor="#94A3B8", lw=1, ls="--")
    ax.add_patch(p3)
    ax.text(0.6, 2.9, "DATA PERSISTENCE & CRYPTOGRAPHIC SECURITY LAYER", fontsize=9, fontweight='bold', color='#1E293B')

    draw_box(ax, 0.8, 0.7, 2.6, 1.9, "PostgreSQL 16 + Forced RLS", "Strict Multi-Tenant Isolation\nNon-Superuser consolith_app", "#EFF6FF", "#1D4ED8")
    draw_box(ax, 3.7, 0.7, 2.6, 1.9, "Qdrant Vector DB", "Legal Statute Embeddings\nCosine Similarity Index", "#FEF2F2", "#DC2626")
    draw_box(ax, 6.6, 0.7, 2.6, 1.9, "Ed25519 PKI CA Engine", "Tamper-Evident SHA-256 Audit\nDigital Attestation Signatures", "#FAF5FF", "#7C3AED")

    # Connecting arrows
    draw_arrow(ax, 2.1, 7.5, 2.1, 6.1)
    draw_arrow(ax, 5.0, 7.5, 5.0, 6.1)
    draw_arrow(ax, 7.9, 7.5, 7.9, 6.1)

    draw_arrow(ax, 1.8, 4.0, 1.8, 2.6)
    draw_arrow(ax, 4.0, 4.0, 2.5, 2.6)
    draw_arrow(ax, 6.2, 4.0, 5.0, 2.6)
    draw_arrow(ax, 8.4, 4.0, 7.9, 2.6)

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_1_architecture.png", dpi=300, bbox_inches='tight')
    plt.close()

# ==============================================================================
# 2. FIG 4.2: DATA FLOW DIAGRAM (DFD Level 1)
# ==============================================================================
def make_fig_4_2():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # External Entities
    draw_box(ax, 0.5, 7.5, 1.8, 1.2, "Citizen / Resident", "Document Uploader", "#DBEAFE", "#2563EB")
    draw_box(ax, 7.7, 7.5, 1.8, 1.2, "Verification Officer", "Administrative Reviewer", "#E0E7FF", "#4F46E5")

    # Processes (Circles / rounded boxes)
    draw_box(ax, 3.8, 7.8, 2.4, 1.1, "1.0 Ingestion & OCR", "Extract & Mask Identity", "#FEF3C7", "#D97706", radius=0.05)
    draw_box(ax, 3.8, 5.5, 2.4, 1.1, "2.0 Conflict Detection", "Fuzzy Cross-Doc Match", "#FEF3C7", "#D97706", radius=0.05)
    draw_box(ax, 3.8, 3.2, 2.4, 1.1, "3.0 RAG Legal Guidance", "Statutory Retrieval", "#FEF3C7", "#D97706", radius=0.05)
    draw_box(ax, 3.8, 0.9, 2.4, 1.1, "4.0 Ed25519 Signing", "Affidavit Certification", "#FEF3C7", "#D97706", radius=0.05)

    # Data Stores (Open-ended rects / double lines)
    draw_box(ax, 0.5, 4.5, 2.0, 1.2, "D1: Documents Store", "Encrypted Metadata (RLS)", "#F1F5F9", "#475569")
    draw_box(ax, 7.5, 4.5, 2.0, 1.2, "D2: Inconsistencies Store", "Discrepancy Records", "#F1F5F9", "#475569")
    draw_box(ax, 0.5, 1.5, 2.0, 1.2, "D3: Legal Knowledge", "Qdrant Vector DB", "#F1F5F9", "#475569")
    draw_box(ax, 7.5, 1.5, 2.0, 1.2, "D4: Audit Log (Ledger)", "Hash-Chained Immutability", "#F1F5F9", "#475569")

    # Connectors
    draw_arrow(ax, 2.3, 8.1, 3.8, 8.35, "Upload IDs")
    draw_arrow(ax, 5.0, 7.8, 5.0, 6.6, "Cleaned Extracted JSON")
    draw_arrow(ax, 5.0, 5.5, 5.0, 4.3, "Flagged Inconsistencies")
    draw_arrow(ax, 5.0, 3.2, 5.0, 2.0, "Resolution Path")

    draw_arrow(ax, 3.8, 8.0, 2.5, 5.5, "Save Docs")
    draw_arrow(ax, 6.2, 5.8, 7.5, 5.3, "Store Conflicts")
    draw_arrow(ax, 2.5, 2.0, 3.8, 3.5, "Retrieve Rules")
    draw_arrow(ax, 6.2, 1.2, 7.5, 1.8, "Append Audit Hash")

    draw_arrow(ax, 7.7, 7.8, 6.2, 6.0, "Review / Resolve")
    draw_arrow(ax, 3.8, 1.3, 1.4, 7.5, "Download Signed Affidavit", rad=0.2)

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_2_dfd.png", dpi=300, bbox_inches='tight')
    plt.close()

# ==============================================================================
# 3. FIG 4.3: CLASS DIAGRAM
# ==============================================================================
def make_fig_4_3():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    def draw_uml_class(ax, x, y, w, h, name, attrs, methods, bg="#EFF6FF", border="#1E40AF"):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                             facecolor=bg, edgecolor=border, linewidth=1.5, zorder=2)
        ax.add_patch(box)
        # Title bar
        ax.plot([x, x+w], [y + h - 0.5, y + h - 0.5], color=border, lw=1, zorder=3)
        ax.text(x + w/2, y + h - 0.25, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1E3A8A', zorder=4)
        
        # Attributes
        ay = y + h - 0.7
        for attr in attrs:
            ax.text(x + 0.1, ay, attr, ha='left', va='center', fontsize=6.8, color='#0F172A', zorder=4)
            ay -= 0.28
        
        # Method separator
        ax.plot([x, x+w], [ay + 0.1, ay + 0.1], color=border, lw=0.8, ls=":", zorder=3)
        ay -= 0.15
        for m in methods:
            ax.text(x + 0.1, ay, m, ha='left', va='center', fontsize=6.8, color='#047857', zorder=4)
            ay -= 0.28

    # Classes
    draw_uml_class(ax, 0.4, 5.2, 2.8, 4.3, "DocumentIngestionManager",
                   ["+ id: UUID", "+ resident_id: UUID", "+ doc_type: Enum", "+ storage_hash: str", "+ encryption_key: Fernet"],
                   ["+ upload_file(stream): bool", "+ parse_ocr_text(): dict", "+ mask_aadhaar(): str", "+ persist_secure(): UUID"])

    draw_uml_class(ax, 3.6, 5.2, 2.8, 4.3, "ConflictDetectionEngine",
                   ["+ conflict_id: UUID", "+ doc_a: Document", "+ doc_b: Document", "+ field_name: str", "+ score: float"],
                   ["+ compare_tokens(val1, val2)", "+ jaro_winkler_match()", "+ classify_severity()", "+ flag_unresolvable()"])

    draw_uml_class(ax, 6.8, 5.2, 2.8, 4.3, "RAGStatutoryAssistant",
                   ["+ session_id: str", "+ qdrant_client: Client", "+ floor_threshold: 0.55", "+ llm_router: GeminiAPI"],
                   ["+ embed_query(query): Vector", "+ search_statutes(): Context", "+ generate_grounded_steps()", "+ cite_government_orders()"])

    draw_uml_class(ax, 0.4, 0.5, 2.8, 4.0, "SecurityPolicyEnforcer",
                   ["+ user_role: RoleEnum", "+ tenant_id: UUID", "+ rls_session: Session", "+ app_role: consolith_app"],
                   ["+ set_session_tenant(uuid)", "+ verify_rls_isolation()", "+ prevent_escalation()", "+ sanitize_credentials()"])

    draw_uml_class(ax, 3.6, 0.5, 2.8, 4.0, "AffidavitGenerator",
                   ["+ affidavit_id: UUID", "+ resident_name: str", "+ correction_clauses: list", "+ template_type: str"],
                   ["+ compile_pdf_document()", "+ inject_qr_verification()", "+ format_legal_clauses()", "+ render_downloadable()"])

    draw_uml_class(ax, 6.8, 0.5, 2.8, 4.0, "PKIAttestationEngine",
                   ["+ private_key: Ed25519Key", "+ public_key_pem: str", "+ cert_id: UUID", "+ prev_audit_hash: str"],
                   ["+ sign_document_hash(): bytes", "+ append_tamper_log(): str", "+ verify_digital_seal(): bool", "+ block_mutations()"])

    # Relationships
    draw_arrow(ax, 3.2, 7.3, 3.6, 7.3, "invokes", lw=1.2)
    draw_arrow(ax, 6.4, 7.3, 6.8, 7.3, "routes to", lw=1.2)
    draw_arrow(ax, 5.0, 5.2, 5.0, 4.5, "triggers", lw=1.2)
    draw_arrow(ax, 6.4, 2.5, 6.8, 2.5, "signs with", lw=1.2)
    draw_arrow(ax, 1.8, 4.5, 1.8, 5.2, "enforces RLS", lw=1.2)

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_3_class.png", dpi=300, bbox_inches='tight')
    plt.close()

# ==============================================================================
# 4. FIG 4.4: USE CASE DIAGRAM
# ==============================================================================
def make_fig_4_4():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Actors
    def draw_actor(ax, x, y, name):
        circle = plt.Circle((x, y + 0.45), 0.22, color='#1E293B', fill=False, lw=1.8, zorder=4)
        ax.add_patch(circle)
        ax.plot([x, x], [y + 0.23, y - 0.25], color='#1E293B', lw=1.8, zorder=4)
        ax.plot([x - 0.3, x + 0.3], [y + 0.05, y + 0.05], color='#1E293B', lw=1.8, zorder=4)
        ax.plot([x, x - 0.25], [y - 0.25, y - 0.65], color='#1E293B', lw=1.8, zorder=4)
        ax.plot([x, x + 0.25], [y - 0.25, y - 0.65], color='#1E293B', lw=1.8, zorder=4)
        ax.text(x, y - 0.9, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0F172A')

    draw_actor(ax, 0.9, 7.0, "Citizen / Resident")
    draw_actor(ax, 0.9, 2.8, "Verification Officer")
    draw_actor(ax, 9.1, 5.0, "CONVELINA Core AI / CA")

    # Boundary
    system_box = FancyBboxPatch((2.2, 0.4), 5.6, 9.2, boxstyle="round,pad=0.02",
                                facecolor="#F8FAFC", edgecolor="#475569", lw=1.5, zorder=1)
    ax.add_patch(system_box)
    ax.text(5.0, 9.3, "CONVELINA SYSTEM BOUNDARY", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1E293B')

    # Use Cases (Ellipses)
    def draw_use_case(ax, x, y, text):
        ellipse = patches.Ellipse((x, y), 3.4, 0.95, facecolor="#EFF6FF", edgecolor="#2563EB", lw=1.2, zorder=2)
        ax.add_patch(ellipse)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='medium', color='#1E3A8A', zorder=3)

    draw_use_case(ax, 5.0, 8.4, "Upload & Mask Identity Docs")
    draw_use_case(ax, 5.0, 7.1, "Detect Clerical Inconsistencies")
    draw_use_case(ax, 5.0, 5.8, "Consult Statutory RAG Assistant")
    draw_use_case(ax, 5.0, 4.5, "Generate Rectification Affidavit")
    draw_use_case(ax, 5.0, 3.2, "Review & Audit Discrepancies")
    draw_use_case(ax, 5.0, 1.9, "Issue Ed25519 PKI Attestation")
    draw_use_case(ax, 5.0, 0.8, "Verify Tamper-Evident Logs")

    # Actor associations
    ax.plot([1.2, 3.3], [7.0, 8.4], color="#475569", lw=1.2)
    ax.plot([1.2, 3.3], [7.0, 7.1], color="#475569", lw=1.2)
    ax.plot([1.2, 3.3], [7.0, 5.8], color="#475569", lw=1.2)
    ax.plot([1.2, 3.3], [7.0, 4.5], color="#475569", lw=1.2)

    ax.plot([1.2, 3.3], [2.8, 3.2], color="#475569", lw=1.2)
    ax.plot([1.2, 3.3], [2.8, 1.9], color="#475569", lw=1.2)
    ax.plot([1.2, 3.3], [2.8, 0.8], color="#475569", lw=1.2)

    ax.plot([6.7, 8.8], [7.1, 5.0], color="#475569", lw=1.2)
    ax.plot([6.7, 8.8], [5.8, 5.0], color="#475569", lw=1.2)
    ax.plot([6.7, 8.8], [4.5, 5.0], color="#475569", lw=1.2)
    ax.plot([6.7, 8.8], [1.9, 5.0], color="#475569", lw=1.2)

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_4_usecase.png", dpi=300, bbox_inches='tight')
    plt.close()

# ==============================================================================
# 5. FIG 4.5: COLLABORATION DIAGRAM
# ==============================================================================
def make_fig_4_5():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    draw_box(ax, 0.8, 6.8, 2.2, 1.4, ":ClientApp", "Web Dashboard", "#DBEAFE", "#2563EB")
    draw_box(ax, 4.0, 6.8, 2.2, 1.4, ":FastAPIGateway", "Auth & Dispatch", "#FEF3C7", "#D97706")
    draw_box(ax, 7.2, 6.8, 2.2, 1.4, ":ConflictEngine", "Fuzzy Evaluator", "#ECFDF5", "#059669")
    draw_box(ax, 0.8, 1.8, 2.2, 1.4, ":PostgreSQL_RLS", "Tenant Storage", "#F1F5F9", "#475569")
    draw_box(ax, 4.0, 1.8, 2.2, 1.4, ":RAGVectorEngine", "Qdrant & Gemini", "#FDF4FF", "#9333EA")
    draw_box(ax, 7.2, 1.8, 2.2, 1.4, ":PKISigningCA", "Ed25519 Engine", "#FFF1F2", "#E11D48")

    # Links with numbered messages
    ax.plot([3.0, 4.0], [7.5, 7.5], color="#334155", lw=1.5)
    ax.text(3.5, 7.8, "1: uploadDoc()\n4: requestGuidance()", ha='center', fontsize=7, color='#1E293B', fontweight='bold')

    ax.plot([6.2, 7.2], [7.5, 7.5], color="#334155", lw=1.5)
    ax.text(6.7, 7.8, "2: detectConflicts()\n3: returnScores()", ha='center', fontsize=7, color='#1E293B', fontweight='bold')

    ax.plot([1.9, 1.9], [6.8, 3.2], color="#334155", lw=1.5)
    ax.text(1.3, 5.0, "1.1: enforceRLS()\n1.2: persistFields()", ha='center', fontsize=7, color='#1E293B', fontweight='bold')

    ax.plot([5.1, 5.1], [6.8, 3.2], color="#334155", lw=1.5)
    ax.text(5.7, 5.0, "5: semanticSearch()\n6: synthesizeAnswer()", ha='center', fontsize=7, color='#1E293B', fontweight='bold')

    ax.plot([8.3, 8.3], [6.8, 3.2], color="#334155", lw=1.5)
    ax.text(8.9, 5.0, "7: signAffidavit()\n8: appendAuditLedger()", ha='center', fontsize=7, color='#1E293B', fontweight='bold')

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_5_collaboration.png", dpi=300, bbox_inches='tight')
    plt.close()

# ==============================================================================
# 6. FIG 4.6: SEQUENCE DIAGRAM
# ==============================================================================
def make_fig_4_6():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    lifelines = [
        ("Citizen", 1.0),
        ("Frontend UI", 2.6),
        ("FastAPI / RLS", 4.3),
        ("OCR & Conflict", 6.0),
        ("RAG Engine", 7.6),
        ("PostgreSQL", 9.1)
    ]

    for name, x in lifelines:
        draw_box(ax, x - 0.7, 8.8, 1.4, 0.8, name, color="#E2E8F0", border="#475569")
        ax.plot([x, x], [8.8, 0.5], color="#94A3B8", lw=1, ls="--", zorder=1)

    steps = [
        (1.0, 2.6, 8.2, "1. Upload Identity Docs (PDF/Img)"),
        (2.6, 4.3, 7.4, "2. POST /api/v1/documents (Bearer JWT)"),
        (4.3, 9.1, 6.6, "3. Set tenant_id & Force RLS session"),
        (4.3, 6.0, 5.8, "4. Ingest, Parse OCR, Extract Fields"),
        (6.0, 6.0, 5.0, "5. Run Jaro-Winkler Token Split"),
        (6.0, 4.3, 4.2, "6. Return Conflicts & Precedence"),
        (4.3, 7.6, 3.4, "7. Query Resolution Rules (Cosine Sim >= 0.55)"),
        (7.6, 4.3, 2.6, "8. Return Grounded Legal Correction Steps"),
        (4.3, 9.1, 1.8, "9. Append-Only Tamper Log (SHA-256 Chain)"),
        (4.3, 2.6, 1.1, "10. Render Conflicts, Steps & Pre-filled Affidavit"),
        (2.6, 1.0, 0.6, "11. Display Discrepancy Dashboard to User")
    ]

    for x1, x2, y, label in steps:
        draw_arrow(ax, x1, y, x2, y, color="#1E293B", lw=1.2)
        mx = (x1 + x2) / 2
        ax.text(mx, y + 0.12, label, ha='center', va='bottom', fontsize=7, color='#0F172A',
                bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFFFF", edgecolor="#E2E8F0", lw=0.6), zorder=5)

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_6_sequence.png", dpi=300, bbox_inches='tight')
    plt.close()

# ==============================================================================
# 7. FIG 4.7: ACTIVITY DIAGRAM
# ==============================================================================
def make_fig_4_7():
    fig, ax = plt.subplots(figsize=(10, 7.0), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Start Node
    start = plt.Circle((5.0, 9.5), 0.18, color='#0F172A', zorder=3)
    ax.add_patch(start)
    ax.text(5.0, 9.8, "Start", ha='center', fontsize=8, fontweight='bold')

    draw_arrow(ax, 5.0, 9.32, 5.0, 8.8)
    draw_box(ax, 3.8, 8.3, 2.4, 0.6, "User Ingests Identity Docs", color="#EFF6FF", border="#2563EB")

    draw_arrow(ax, 5.0, 8.3, 5.0, 7.8)
    draw_box(ax, 3.8, 7.2, 2.4, 0.6, "OCR & Entity Extraction", color="#EFF6FF", border="#2563EB")

    draw_arrow(ax, 5.0, 7.2, 5.0, 6.7)
    # Decision Diamond
    d1 = patches.Polygon([[5.0, 6.7], [5.8, 6.3], [5.0, 5.9], [4.2, 6.3]], facecolor="#FEF3C7", edgecolor="#D97706", lw=1.2, zorder=3)
    ax.add_patch(d1)
    ax.text(5.0, 6.3, "Confidence\n>= 80%?", ha='center', va='center', fontsize=7, fontweight='bold', zorder=4)

    # Low OCR Branch
    draw_arrow(ax, 4.2, 6.3, 2.0, 6.3, "[No: Ambiguous]")
    draw_box(ax, 0.8, 5.9, 2.2, 0.8, "Flag as Unresolvable\nManual Review Required", color="#FEE2E2", border="#DC2626")
    draw_arrow(ax, 1.9, 5.9, 1.9, 1.0)

    # High OCR Branch
    draw_arrow(ax, 5.0, 5.9, 5.0, 5.3, "[Yes: High Quality]")
    draw_box(ax, 3.8, 4.7, 2.4, 0.6, "Cross-Document Comparison", color="#EFF6FF", border="#2563EB")

    draw_arrow(ax, 5.0, 4.7, 5.0, 4.2)
    # Decision Diamond 2
    d2 = patches.Polygon([[5.0, 4.2], [5.8, 3.8], [5.0, 3.4], [4.2, 3.8]], facecolor="#FEF3C7", edgecolor="#D97706", lw=1.2, zorder=3)
    ax.add_patch(d2)
    ax.text(5.0, 3.8, "Inconsistency\nDetected?", ha='center', va='center', fontsize=7, fontweight='bold', zorder=4)

    # No conflict branch
    draw_arrow(ax, 5.8, 3.8, 8.0, 3.8, "[No Inconsistency]")
    draw_box(ax, 7.0, 3.2, 2.2, 0.8, "Mark Verified\nNo Rectification Needed", color="#ECFDF5", border="#059669")
    draw_arrow(ax, 8.1, 3.2, 8.1, 1.0)

    # Conflict branch
    draw_arrow(ax, 5.0, 3.4, 5.0, 2.8, "[Yes: Inconsistent]")
    draw_box(ax, 3.7, 2.2, 2.6, 0.7, "RAG Statutory Retrieval &\nEd25519 Certified Affidavit", color="#FDF4FF", border="#9333EA")

    draw_arrow(ax, 5.0, 2.2, 5.0, 1.4)
    draw_box(ax, 3.7, 0.7, 2.6, 0.7, "Append to Audit Ledger &\nNotify Citizen Workspace", color="#EFF6FF", border="#2563EB")

    # Merge to End
    draw_arrow(ax, 1.9, 1.0, 4.7, 0.2)
    draw_arrow(ax, 5.0, 0.7, 5.0, 0.35)
    draw_arrow(ax, 8.1, 1.0, 5.3, 0.2)

    # End Node (double circle)
    c1 = plt.Circle((5.0, 0.2), 0.18, color='#0F172A', fill=False, lw=1.5, zorder=3)
    c2 = plt.Circle((5.0, 0.2), 0.12, color='#0F172A', fill=True, zorder=4)
    ax.add_patch(c1)
    ax.add_patch(c2)
    ax.text(5.0, -0.15, "End Process", ha='center', fontsize=8, fontweight='bold')

    fig.tight_layout()
    fig.savefig("report_assets/fig_4_7_activity.png", dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    print("Generating Chapter 4 Architectural Diagrams...")
    make_fig_4_1()
    print("  -> fig_4_1_architecture.png")
    make_fig_4_2()
    print("  -> fig_4_2_dfd.png")
    make_fig_4_3()
    print("  -> fig_4_3_class.png")
    make_fig_4_4()
    print("  -> fig_4_4_usecase.png")
    make_fig_4_5()
    print("  -> fig_4_5_collaboration.png")
    make_fig_4_6()
    print("  -> fig_4_6_sequence.png")
    make_fig_4_7()
    print("  -> fig_4_7_activity.png")
    print("All 7 diagrams generated successfully!")
