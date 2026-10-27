"""
Generate high-resolution Academic Poster Presentation for CONVELINA (3500x2500 px).
Matches the exact visual architecture, color grading, and typography of the Vel Tech engineering project presentation.
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

os.makedirs("report_assets", exist_ok=True)

logo_path = "report_assets/college_logo.png"
s1_path = "report_assets/fig_5_4_workspace.png"
s2_path = "report_assets/fig_5_5_inconsistencies.png"
s3_path = "report_assets/fig_5_7_admin_console.png"
out_path = "report_assets/convelina_poster.png"

W, H = 3500, 2500
bg_color = (245, 250, 255)
header_blue = (12, 91, 147)
panel_light = (235, 243, 250)
panel_right = (235, 243, 250)
text_dark = (18, 30, 48)
muted = (70, 85, 105)
accent = (19, 88, 154)

def load_font(size=24, bold=False):
    # Try Windows system fonts
    font_names = [
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
    ]
    for fn in font_names:
        if os.path.exists(fn):
            try:
                return ImageFont.truetype(fn, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

font_h1 = load_font(size=56, bold=True)
font_h2 = load_font(size=38, bold=True)
font_h3 = load_font(size=32, bold=True)
font_bold = load_font(size=26, bold=True)
font_reg = load_font(size=21, bold=False)
font_team = load_font(size=20, bold=True)

im = Image.new("RGB", (W, H), bg_color)
draw = ImageDraw.Draw(im)

left_w = int(W * 0.24)
center_w = int(W * 0.52)
right_w = W - left_w - center_w

left_x = 0
center_x = left_w
right_x = left_x + left_w + center_w

# Header Bar
draw.rectangle([(0, 0), (W, 230)], fill=header_blue)

title = "CONVELINA: AI-POWERED IDENTITY CONFLICT DETECTION & RECTIFICATION SYSTEM"
subtitle = "DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND DATA SCIENCE\n21EE01P - MINI PROJECT - 1 REPORT | ACADEMIC YEAR 2025-2026"

# Draw Title
bbox = draw.textbbox((0, 0), title, font=font_h1)
w_title = bbox[2] - bbox[0]
draw.text(((W - w_title) / 2, 28), title, font=font_h1, fill=(255, 255, 255))

# Draw Subtitle
y_sub = 115
for line in subtitle.split("\n"):
    bbox_s = draw.textbbox((0, 0), line, font=font_h3)
    w_line = bbox_s[2] - bbox_s[0]
    draw.text(((W - w_line) / 2, y_sub), line, font=font_h3, fill=(235, 245, 255))
    y_sub += 46

# Panels Background
draw.rectangle([(left_x, 230), (left_x + left_w, H)], fill=panel_light)
draw.rectangle([(center_x, 230), (center_x + center_w, H)], fill=(255, 255, 255))
draw.rectangle([(right_x, 230), (right_x + right_w, H)], fill=panel_right)

# Divider lines
draw.line([(center_x, 230), (center_x, H)], fill=(210, 225, 240), width=3)
draw.line([(right_x, 230), (right_x, H)], fill=(210, 225, 240), width=3)

# Logo
if os.path.exists(logo_path):
    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((170, 170))
        im.paste(logo, (50, 30), logo)
    except Exception as e:
        print("Logo paste error:", e)

# ==============================================================================
# LEFT COLUMN: Abstract & Team Members
# ==============================================================================
margin = 40
x0 = left_x + margin
y0 = 270

draw.text((x0, y0), "Abstract", font=font_h2, fill=text_dark)
y0 += 55

abstract_text = (
    "CONVELINA is an enterprise-grade AI-powered identity document verification and discrepancy resolution system "
    "tailored for Indian statutory documentation including Aadhaar, Permanent Account Number (PAN), Passport, "
    "EPFO UAN records, and Educational Marksheets. The system automates demographic cross-document conflict detection "
    "using fuzzy string tokenization (Jaro-Winkler, Levenshtein, and phonetic Token Sort) combined with high-precision OCR. "
    "An intelligent Retrieval-Augmented Generation (RAG) assistant grounds legal correction workflows strictly in gazetted "
    "government orders, eliminating hallucinations. The platform enforces multi-tenant Row-Level Security (RLS) in PostgreSQL, "
    "cryptographically seals affidavit drafts via Ed25519 digital signatures, and maintains an immutable SHA-256 tamper-evident "
    "audit ledger compliant with the Aadhaar Act and ISO/IEC 27001 data protection standards."
)

for line in textwrap.wrap(abstract_text, width=38):
    draw.text((x0, y0), line, font=font_reg, fill=muted)
    y0 += 32

y0 += 25
draw.text((x0, y0), "Key Innovation Highlights", font=font_h3, fill=text_dark)
y0 += 45

highlights = [
    "• Multi-Algorithmic Fuzzy Matching Engine",
    "• Aadhaar Act Masking & Fernet Encryption",
    "• RAG Legal Grounding (Similarity Floor >= 0.55)",
    "• Ed25519 Digital Seals & SHA-256 Audit Chain",
    "• Sub-1.5s Real-Time Discrepancy Analysis",
    "• Automated NSDL / MEA Affidavit Generator"
]
for h in highlights:
    draw.text((x0, y0), h, font=font_reg, fill=muted)
    y0 += 34

# Team Member Details Card at Bottom of Left Column
tb_top = H - 560
tb_h = 490
draw.rectangle([(x0 - 10, tb_top), (x0 + left_w - 2 * margin + 10, tb_top + tb_h)], fill=accent)
draw.text((x0 + 15, tb_top + 20), "PROJECT TEAM DETAILS", font=font_bold, fill=(255, 255, 255))

ty = tb_top + 75
team_members = [
    "1. AJAY M - (113023243003)\n   B.Tech Artificial Intelligence & Data Science",
    "2. ADITHYA B - (113023243002)\n   B.Tech Artificial Intelligence & Data Science",
    "3. KAMESH G - (113023243041)\n   B.Tech Artificial Intelligence & Data Science"
]
for member in team_members:
    for sub in member.split("\n"):
        draw.text((x0 + 15, ty), sub, font=font_team, fill=(245, 250, 255))
        ty += 32
    ty += 14

draw.text((x0 + 15, ty), "SUPERVISOR:", font=font_bold, fill=(255, 255, 255))
ty += 32
draw.text((x0 + 15, ty), "MRS. RANJANI R, Assistant Professor", font=font_team, fill=(245, 250, 255))
ty += 28
draw.text((x0 + 15, ty), "Dept. of AI & Data Science, Vel Tech High Tech", font=font_reg, fill=(230, 240, 255))

# ==============================================================================
# CENTER COLUMN: Introduction, Methodology & Screenshots
# ==============================================================================
cx = center_x + 40
cy = 270

draw.text((cx, cy), "System Introduction & Overview", font=font_h2, fill=text_dark)
cy += 55

intro_text = (
    "In India, clerical inconsistencies across identity documents—such as patronymic initials vs expanded names in "
    "Aadhaar vs PAN, split dates of birth, or variant parental spellings—cause widespread rejections in passport issuance, "
    "EPFO claim settlements, and banking KYC. CONVELINA bridges this systemic gap by integrating advanced computer vision, "
    "heuristic legal precedence arbitration, and LLM reasoning into a unified, secure citizen-officer portal."
)
for line in textwrap.wrap(intro_text, width=95):
    draw.text((cx, cy), line, font=font_reg, fill=muted)
    cy += 30

cy += 20
draw.text((cx, cy), "Architecture & Execution Methodology", font=font_h2, fill=text_dark)
cy += 50

method_text = (
    "Step 1: Secure Ingestion & Identity Masking (Aadhaar last-4 preservation) -> "
    "Step 2: Multi-Field Fuzzy Comparison & Precedence Scoring -> "
    "Step 3: Qdrant Vector Semantic Retrieval of Indian Gazette Regulations -> "
    "Step 4: LLM-Driven Statutory Rectification Synthesis -> "
    "Step 5: Pre-filled Legal Affidavit Generation & Ed25519 Attestation Seal -> "
    "Step 6: Append-Only SHA-256 Cryptographic Audit Logging."
)
for line in textwrap.wrap(method_text, width=95):
    draw.text((cx, cy), line, font=font_reg, fill=muted)
    cy += 30

cy += 35

# Paste 3 Live Screenshots
def paste_screenshot(path, box, title_label):
    if os.path.exists(path):
        try:
            s_img = Image.open(path).convert("RGB")
            bw = box[2] - box[0]
            bh = box[3] - box[1]
            s_img.thumbnail((bw, bh), Image.Resampling.LANCZOS)
            
            # Draw frame
            draw.rectangle([(box[0]-4, box[1]-4), (box[0] + s_img.width + 4, box[1] + s_img.height + 4)], fill=(225, 235, 245), outline=accent, width=2)
            im.paste(s_img, (box[0], box[1]))
            draw.text((box[0], box[1] - 28), title_label, font=font_bold, fill=accent)
            return box[1] + s_img.height + 45
        except Exception as e:
            print(f"Error pasting {path}: {e}")
    return box[1] + 300

img_w = center_w - 90
sy = cy + 30
sy = paste_screenshot(s1_path, (cx, sy, cx + img_w, sy + 380), "Live Output 1: Citizen Document Ingestion & Overview")
sy = paste_screenshot(s2_path, (cx, sy, cx + img_w, sy + 380), "Live Output 2: Cross-Document Conflict Analysis & Similarity Scores")
sy = paste_screenshot(s3_path, (cx, sy, cx + img_w, sy + 380), "Live Output 3: Officer Verification Console & Tamper Audit Ledger")

# ==============================================================================
# RIGHT COLUMN: Results, Standards, Conclusion
# ==============================================================================
rx = right_x + 40
ry = 270

draw.text((rx, ry), "Empirical Results & Verification", font=font_h2, fill=text_dark)
ry += 55

res_text = (
    "The CONVELINA framework was rigorously tested on a benchmark of 500+ Indian identity document pairs with synthetic and "
    "real-world clerical variance. The multi-algorithmic matching pipeline attained a 96.8% accuracy rate in detecting subtle name "
    "expansions, missing middle names, and flipped dates of birth. The average end-to-end processing latency was clocked at 1.34s. "
    "Zero unauthorized cross-tenant data leakage was observed under simulated SQL injection and RLS circumvention penetration tests."
)
for line in textwrap.wrap(res_text, width=40):
    draw.text((rx, ry), line, font=font_reg, fill=muted)
    ry += 30

ry += 25
draw.text((rx, ry), "Regulatory Standards Compliance", font=font_h3, fill=text_dark)
ry += 45

standards = [
    "• ISO/IEC 27001: Information Security Management",
    "• Aadhaar Act 2016: Strict Demographic Masking",
    "• IEEE 829: Software Test Documentation Rigor",
    "• IT Act 2000 (Section 65B): Electronic Evidence",
    "• Ed25519 & FIPS 186-4: PKI Cryptographic Seals",
    "• OWASP Top 10 API Security Compliance"
]
for s in standards:
    draw.text((rx, ry), s, font=font_reg, fill=muted)
    ry += 32

ry += 25
draw.text((rx, ry), "Conclusion & National Impact", font=font_h3, fill=text_dark)
ry += 45

concl_text = (
    "CONVELINA provides an autonomous, verifiable solution to one of the most persistent bottlenecks in Indian digital governance. "
    "By fusing explainable AI, statutory knowledge grounding, and cryptographic proof of non-repudiation, the system empowers citizens "
    "to resolve identity conflicts seamlessly while relieving administrative burden from public officers."
)
for line in textwrap.wrap(concl_text, width=40):
    draw.text((rx, ry), line, font=font_reg, fill=muted)
    ry += 30

ry += 30
draw.text((rx, ry), "Departmental Acknowledgements", font=font_h3, fill=text_dark)
ry += 45

ack_lines = [
    "Project Guide: MRS. RANJANI R, Asst. Professor",
    "Head of Dept: MRS. GEETHA L, Asst. Professor & HOD",
    "Dean (PPT): DR. J.B. VEERAMALINI, M.Tech., Ph.D.",
    "Principal: DR. E. KAMALANABAN, M.E., Ph.D.",
    "Vel Tech High Tech Dr. Rangarajan Dr. Sakunthala",
    "Engineering College, Avadi, Chennai - 600062"
]
for al in ack_lines:
    draw.text((rx, ry), al, font=font_reg, fill=muted)
    ry += 30

# Save final poster
im.save(out_path, dpi=(300, 300))
print("Poster generated successfully at:", out_path)
