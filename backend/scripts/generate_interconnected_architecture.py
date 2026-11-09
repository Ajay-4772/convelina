# -*- coding: utf-8 -*-
"""
Interconnected System Journey & Architecture Pipeline Generator for CONVELINA
Generates a true pipeline/journey-style diagram (matching User Reference Images 1 & 3)
on a clean white background with interconnected technology nodes, pipeline rails,
numbered journey steps, and direct service-to-service linkages.
"""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.abspath("."))
from scripts.test_icon_lib import (
    draw_icon_react, draw_icon_python, draw_icon_fastapi, draw_icon_nextjs,
    draw_icon_docker, draw_icon_git, draw_icon_postgres, draw_icon_qdrant,
    draw_icon_tesseract, draw_icon_gemini, draw_icon_ed25519, draw_icon_caddy,
    draw_icon_firebase, draw_icon_audit, draw_icon_user, draw_icon_server,
    draw_icon_email, draw_icon_testing, draw_icon_typescript, draw_icon_tailwind
)

OUTPUT_DIR = "docs/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Color Palette (Crisp, High-Contrast White-Background Pipeline)
WHITE = (255, 255, 255)
BG_WHITE = (255, 255, 255)
SLATE_50 = (248, 250, 252)
SLATE_100 = (241, 245, 249)
SLATE_200 = (226, 232, 240)
SLATE_300 = (203, 213, 225)
SLATE_400 = (148, 163, 184)
SLATE_500 = (100, 116, 139)
SLATE_600 = (71, 85, 105)
SLATE_700 = (51, 65, 85)
SLATE_800 = (30, 41, 59)
SLATE_900 = (15, 23, 42)

# Pipeline & Tech Colors
PIPE_MAIN = (14, 116, 144)        # Deep Cyan Main Pipeline Rail
PIPE_ACCENT = (14, 165, 233)      # Light Cyan Flow
PIPE_DATA = (16, 185, 129)        # Emerald Data Rail
PIPE_AI = (230, 57, 70)           # Coral AI Rail
PIPE_PKI = (139, 92, 246)         # Violet PKI Rail
PIPE_AUTH = (245, 158, 11)        # Amber Auth Rail
CLR_AUTH = (245, 158, 11)
CLR_TESSERACT = (14, 116, 144)
CLR_RAPIDFUZZ = (220, 38, 38)
CLR_QDRANT = (230, 57, 70)
CLR_GEMINI = (14, 165, 233)
CLR_ED25519 = (139, 92, 246)
CLR_POSTGRES = (51, 103, 145)

# Fonts
try:
    FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 46)
    FONT_SUBTITLE = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
    FONT_NODE_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
    FONT_NODE_SUB = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
    FONT_BADGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
    FONT_STEP = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
    FONT_LABEL = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
    FONT_STAGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
except Exception:
    FONT_TITLE = FONT_SUBTITLE = FONT_NODE_TITLE = FONT_NODE_SUB = FONT_BADGE = FONT_STEP = FONT_LABEL = FONT_STAGE = ImageFont.load_default()

def draw_icon_rapidfuzz(draw, cx, cy, size=56):
    s = size // 2
    draw.rounded_rectangle([cx - s, cy - s, cx + s, cy + s], radius=12, fill=CLR_RAPIDFUZZ)
    pts = [(cx + 2, cy - s + 9), (cx - 8, cy + 1), (cx, cy + 1), (cx - 4, cy + s - 9), (cx + 8, cy - 2), (cx, cy - 2)]
    draw.polygon(pts, fill=WHITE)

def draw_step_circle(draw, cx, cy, step_num, bg_color=SLATE_900):
    r = 18
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg_color, outline=WHITE, width=2)
    s = str(step_num)
    bbox = draw.textbbox((0, 0), s, font=FONT_STEP)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w // 2, cy - h // 2 - 2), s, fill=WHITE, font=FONT_STEP)

def draw_flowing_pipe(draw, pts, color=PIPE_MAIN, width=4, is_dashed=False):
    """Draws a pipeline segment through a series of waypoints with smooth turns."""
    for i in range(len(pts) - 1):
        p1 = pts[i]
        p2 = pts[i + 1]
        if is_dashed:
            # Draw dashed line
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            dashes = int(dist // 12)
            for d in range(dashes):
                if d % 2 == 0:
                    t1 = d / dashes
                    t2 = min((d + 1) / dashes, 1.0)
                    x1 = p1[0] + (p2[0] - p1[0]) * t1
                    y1 = p1[1] + (p2[1] - p1[1]) * t1
                    x2 = p1[0] + (p2[0] - p1[0]) * t2
                    y2 = p1[1] + (p2[1] - p1[1]) * t2
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
        else:
            draw.line([p1, p2], fill=color, width=width)

def draw_arrow_head(draw, tip, direction="right", color=PIPE_MAIN, size=10):
    tx, ty = tip
    if direction == "right":
        draw.polygon([(tx, ty), (tx - size, ty - size * 0.7), (tx - size, ty + size * 0.7)], fill=color)
    elif direction == "down":
        draw.polygon([(tx, ty), (tx - size * 0.7, ty - size), (tx + size * 0.7, ty - size)], fill=color)
    elif direction == "left":
        draw.polygon([(tx, ty), (tx + size, ty - size * 0.7), (tx + size, ty + size * 0.7)], fill=color)
    elif direction == "up":
        draw.polygon([(tx, ty), (tx - size * 0.7, ty + size), (tx + size * 0.7, ty + size)], fill=color)

def draw_node_card(draw, cx, cy, icon_fn, title, subtitle, badge_text="", badge_color=PIPE_MAIN, w=220, h=160):
    """Draws a standalone interactive node card with icon, title, subtitle, and badge."""
    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = cx + w // 2, cy + h // 2
    
    # Card container: clean white fill with crisp border and subtle rounded corners
    draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=WHITE, outline=SLATE_300, width=2)
    # Top colored border line
    draw.line([(x1 + 16, y1), (x2 - 16, y1)], fill=badge_color, width=4)

    # Icon centered at top of card
    icon_fn(draw, cx, y1 + 45, size=52)

    # Title
    bbox_t = draw.textbbox((0, 0), title, font=FONT_NODE_TITLE)
    tw = bbox_t[2] - bbox_t[0]
    draw.text((cx - tw // 2, y1 + 82), title, fill=SLATE_900, font=FONT_NODE_TITLE)

    # Subtitle
    bbox_s = draw.textbbox((0, 0), subtitle, font=FONT_NODE_SUB)
    sw = bbox_s[2] - bbox_s[0]
    draw.text((cx - sw // 2, y1 + 108), subtitle, fill=SLATE_600, font=FONT_NODE_SUB)

    # Pill Badge at bottom
    if badge_text:
        bbox_b = draw.textbbox((0, 0), badge_text, font=FONT_BADGE)
        bw = bbox_b[2] - bbox_b[0]
        bx1 = cx - bw // 2 - 8
        by1 = y2 - 24
        bx2 = cx + bw // 2 + 8
        by2 = y2 - 6
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=6, fill=SLATE_100, outline=badge_color, width=1)
        draw.text((bx1 + 8, by1 + 1), badge_text, fill=badge_color, font=FONT_BADGE)


# ==============================================================================
# 1. INTERCONNECTED SYSTEM JOURNEY & PIPELINE (Reference Image 3 & 1 Style)
# ==============================================================================
def generate_system_journey_pipeline():
    width, height = 3000, 1900
    img = Image.new("RGB", (width, height), BG_WHITE)
    draw = ImageDraw.Draw(img)

    # Header Banner
    draw.rounded_rectangle([50, 30, width - 50, 130], radius=16, fill=SLATE_900)
    draw.text((90, 48), "CONVELINA: END-TO-END ARCHITECTURE & DATA JOURNEY PIPELINE", fill=WHITE, font=FONT_TITLE)
    draw.text((94, 96), "Interconnected Workflow: Citizen Ingress -> Edge Gateway -> Cognitive Engines -> Forced RLS Storage -> Ed25519 PKI", fill=SLATE_400, font=FONT_SUBTITLE)

    # --------------------------------------------------------------------------
    # PIPELINE RAILS & CONNECTORS (Drawn first so node cards sit on top cleanly)
    # --------------------------------------------------------------------------

    # Main Horizontal Pipeline Rail from Users (Left) across to Caddy, Frontend, Backend
    y_rail_main = 350

    # User -> Edge Proxy (Caddy)
    draw_flowing_pipe(draw, [(260, y_rail_main), (560, y_rail_main)], color=PIPE_MAIN, width=5)
    draw_arrow_head(draw, (560, y_rail_main), "right", color=PIPE_MAIN, size=12)
    draw_step_circle(draw, 410, y_rail_main, 1, bg_color=PIPE_MAIN)
    draw.text((340, y_rail_main - 30), "HTTPS / TLS 1.3", fill=SLATE_700, font=FONT_LABEL)

    # Caddy splits to:
    # 1. Next.js Frontend Server
    draw_flowing_pipe(draw, [(700, y_rail_main), (700, 220), (980, 220)], color=PIPE_MAIN, width=4)
    draw_arrow_head(draw, (980, 220), "right", color=PIPE_MAIN, size=12)
    draw_step_circle(draw, 840, 220, "2a", bg_color=SLATE_800)
    draw.text((790, 190), "Proxy / (SSR)", fill=SLATE_700, font=FONT_LABEL)

    # 2. FastAPI Backend API Core
    draw_flowing_pipe(draw, [(700, y_rail_main), (980, y_rail_main)], color=PIPE_MAIN, width=5)
    draw_arrow_head(draw, (980, y_rail_main), "right", color=PIPE_MAIN, size=12)
    draw_step_circle(draw, 840, y_rail_main, "2b", bg_color=SLATE_800)
    draw.text((770, y_rail_main - 30), "Proxy /api/*", fill=SLATE_700, font=FONT_LABEL)

    # Next.js calls FastAPI Backend API
    draw_flowing_pipe(draw, [(1100, 290), (1100, y_rail_main - 80)], color=PIPE_MAIN, width=4, is_dashed=True)
    draw_arrow_head(draw, (1100, y_rail_main - 80), "down", color=PIPE_MAIN, size=10)
    draw.text((1115, 310), "REST API Calls", fill=SLATE_600, font=FONT_LABEL)

    # FastAPI connects to Identity Providers (Top Right Branch)
    draw_flowing_pipe(draw, [(1220, y_rail_main - 40), (1450, 180), (1700, 180)], color=PIPE_AUTH, width=4, is_dashed=True)
    draw_arrow_head(draw, (1700, 180), "right", color=PIPE_AUTH, size=10)
    draw.text((1380, 150), "RS256 JWT Auth", fill=PIPE_AUTH, font=FONT_LABEL)

    draw_flowing_pipe(draw, [(1820, 180), (2050, 180)], color=PIPE_AUTH, width=4, is_dashed=True)
    draw_arrow_head(draw, (2050, 180), "right", color=PIPE_AUTH, size=10)
    draw.text((1870, 150), "OTP Email Dispatch", fill=PIPE_AUTH, font=FONT_LABEL)

    # FastAPI Main Vertical Trunk down to the 4 Cognitive Engines
    x_trunk = 1100
    y_engine = 680
    draw_flowing_pipe(draw, [(x_trunk, y_rail_main + 80), (x_trunk, y_engine)], color=PIPE_MAIN, width=5)

    # Horizontal Distributor Rail for Engines
    draw_flowing_pipe(draw, [(360, y_engine), (2500, y_engine)], color=PIPE_MAIN, width=5)

    # Branch 1: Down to Tesseract 5.5 OCR Engine
    draw_flowing_pipe(draw, [(360, y_engine), (360, 780)], color=PIPE_MAIN, width=4)
    draw_arrow_head(draw, (360, 780), "down", color=PIPE_MAIN, size=12)
    draw_step_circle(draw, 360, 720, 3, bg_color=PIPE_MAIN)
    draw.text((380, 710), "1. Document Upload", fill=SLATE_700, font=FONT_LABEL)

    # Branch 2: Down to SIMD Conflict Engine (RapidFuzz)
    draw_flowing_pipe(draw, [(950, y_engine), (950, 780)], color=PIPE_MAIN, width=4)
    draw_arrow_head(draw, (950, 780), "down", color=PIPE_MAIN, size=12)
    draw_step_circle(draw, 950, 720, 4, bg_color=PIPE_MAIN)
    draw.text((970, 710), "2. Discrepancy Detect", fill=SLATE_700, font=FONT_LABEL)

    # Branch 3: Down to Grounded Legal RAG (Qdrant & Gemini)
    draw_flowing_pipe(draw, [(1650, y_engine), (1650, 780)], color=PIPE_AI, width=4)
    draw_arrow_head(draw, (1650, 780), "down", color=PIPE_AI, size=12)
    draw_step_circle(draw, 1650, 720, 5, bg_color=PIPE_AI)
    draw.text((1670, 710), "3. Legal RAG Search", fill=SLATE_700, font=FONT_LABEL)

    # Branch 4: Down to Ed25519 PKI Attestation Engine
    draw_flowing_pipe(draw, [(2350, y_engine), (2350, 780)], color=PIPE_PKI, width=4)
    draw_arrow_head(draw, (2350, 780), "down", color=PIPE_PKI, size=12)
    draw_step_circle(draw, 2350, 720, 6, bg_color=PIPE_PKI)
    draw.text((2370, 710), "4. Officer Verify & Sign", fill=SLATE_700, font=FONT_LABEL)

    # Connectors from Cognitive Engines down to Database & Storage Tier
    y_engine_bottom = 940
    y_db_top = 1180

    # Tesseract -> PostgreSQL (Encrypted Records with Fernet AES-256)
    draw_flowing_pipe(draw, [(360, y_engine_bottom), (360, 1080), (1050, 1080), (1050, y_db_top)], color=PIPE_DATA, width=4)
    draw_arrow_head(draw, (1050, y_db_top), "down", color=PIPE_DATA, size=12)
    draw_step_circle(draw, 360, 1020, 7, bg_color=PIPE_DATA)
    draw.text((380, 1010), "Store Encrypted Extracted Data", fill=PIPE_DATA, font=FONT_LABEL)

    # RapidFuzz Conflict Engine -> PostgreSQL (Upsert Conflict Records)
    draw_flowing_pipe(draw, [(950, y_engine_bottom), (950, y_db_top)], color=PIPE_DATA, width=4)
    draw_arrow_head(draw, (950, y_db_top), "down", color=PIPE_DATA, size=12)
    draw_step_circle(draw, 950, 1050, 8, bg_color=PIPE_DATA)
    draw.text((970, 1040), "Idempotent Conflict Upsert", fill=PIPE_DATA, font=FONT_LABEL)

    # Qdrant Vector DB <-> Gemini 1.5 Flash (Direct RAG Synthesis Pipeline)
    draw_flowing_pipe(draw, [(1650, y_engine_bottom), (1650, 1060), (1950, 1060), (1950, y_engine_bottom)], color=PIPE_AI, width=4)
    draw_arrow_head(draw, (1950, y_engine_bottom), "up", color=PIPE_AI, size=10)
    draw.text((1700, 1040), "Grounded Prompt (Floor >= 0.55)", fill=PIPE_AI, font=FONT_LABEL)

    # Gemini 1.5 -> PostgreSQL (Store Chat Message)
    draw_flowing_pipe(draw, [(1950, 1060), (1950, 1120), (1350, 1120), (1350, y_db_top)], color=PIPE_DATA, width=4)
    draw_arrow_head(draw, (1350, y_db_top), "down", color=PIPE_DATA, size=12)
    draw_step_circle(draw, 1950, 1100, 9, bg_color=PIPE_AI)
    draw.text((1720, 1135), "Persist Grounded Advice", fill=SLATE_700, font=FONT_LABEL)

    # Ed25519 PKI -> Outputs:
    # 1. Attestation Record in PostgreSQL
    draw_flowing_pipe(draw, [(2350, y_engine_bottom), (2350, 1140), (1500, 1140), (1500, y_db_top)], color=PIPE_PKI, width=4)
    draw_arrow_head(draw, (1500, y_db_top), "down", color=PIPE_PKI, size=12)
    draw_step_circle(draw, 2350, 1050, 10, bg_color=PIPE_PKI)
    draw.text((2370, 1040), "Save Verified Attestation", fill=PIPE_PKI, font=FONT_LABEL)

    # 2. Down to Offline Verifiable QR Code
    draw_flowing_pipe(draw, [(2350, y_engine_bottom), (2350, 1400)], color=PIPE_PKI, width=4)
    draw_arrow_head(draw, (2350, 1400), "down", color=PIPE_PKI, size=12)
    draw.text((2370, 1340), "Emit Verifiable QR Payload", fill=PIPE_PKI, font=FONT_LABEL)

    # PostgreSQL -> Chained Immutable Audit Ledger (Statement Trigger Link)
    draw_flowing_pipe(draw, [(1200, 1420), (1200, 1550)], color=SLATE_800, width=5)
    draw_arrow_head(draw, (1200, 1550), "down", color=SLATE_800, size=12)
    draw_step_circle(draw, 1200, 1480, 11, bg_color=SLATE_800)
    draw.text((1220, 1475), "Trigger: SHA-256 Hash Chain Link", fill=SLATE_800, font=FONT_LABEL)

    # CI/CD & DevSecOps connection to Caddy & Containers (Top Far Left)
    draw_flowing_pipe(draw, [(150, 180), (630, 180), (630, 270)], color=SLATE_500, width=3, is_dashed=True)
    draw_arrow_head(draw, (630, 270), "down", color=SLATE_500, size=10)
    draw_step_circle(draw, 390, 180, 12, bg_color=SLATE_700)
    draw.text((310, 150), "Deploy Verified Images", fill=SLATE_600, font=FONT_LABEL)

    # --------------------------------------------------------------------------
    # NODE CARDS (Drawn over pipeline rails for clean, crisp layering)
    # --------------------------------------------------------------------------

    # Ingress Stage (Left Column)
    draw_node_card(draw, 150, y_rail_main, draw_icon_user, "Citizen / Officer", "Client Browsers", "HTTPS / WSS", PIPE_MAIN, w=220, h=150)
    draw_node_card(draw, 150, 180, draw_icon_git, "CI/CD Pipeline", "OpenQodex + Pytest", "100% Tested", SLATE_700, w=220, h=140)

    # Edge Proxy
    draw_node_card(draw, 630, y_rail_main, draw_icon_caddy, "Caddy 2.8 Proxy", "Reverse Proxy Gateway", "Auto TLS 1.3 | 15MB", (0, 173, 216), w=240, h=160)

    # Frontend Server
    draw_node_card(draw, 1100, 220, draw_icon_nextjs, "Next.js 14 App", "Web App Server (SSR)", "React 18 + TS", (14, 165, 233), w=240, h=150)

    # Backend Core
    draw_node_card(draw, 1100, y_rail_main, draw_icon_fastapi, "FastAPI Backend", "Async ASGI Application", "Python 3.11 + Rust", (0, 150, 136), w=250, h=160)

    # External Identity Providers
    draw_node_card(draw, 1760, 180, draw_icon_firebase, "Firebase Auth", "Identity Provider", "RS256 JWT", CLR_AUTH, w=210, h=140)
    draw_node_card(draw, 2110, 180, draw_icon_email, "Resend Email", "OTP Code Dispatch", "60s Cooldown", CLR_AUTH, w=210, h=140)

    # Row of 4 Cognitive Engines
    # Engine 1: Tesseract OCR
    draw_node_card(draw, 360, 860, draw_icon_tesseract, "Tesseract 5.5 OCR", "Poppler C++ Rasterizer", "Aadhaar Act 29 Shred", CLR_TESSERACT, w=240, h=160)
    
    # Engine 2: SIMD Conflict Engine
    draw_node_card(draw, 950, 860, draw_icon_rapidfuzz, "RapidFuzz Engine", "SIMD AVX2 + Metaphone", "doc_a < doc_b Order", CLR_RAPIDFUZZ, w=240, h=160)

    # Engine 3: Qdrant Vector DB
    draw_node_card(draw, 1650, 860, draw_icon_qdrant, "Qdrant Vector DB", "HNSW Dense Semantic", "25 Official Circulars", CLR_QDRANT, w=240, h=160)

    # Engine 3b: Google Gemini 1.5 Flash
    draw_node_card(draw, 1950, 860, draw_icon_gemini, "Gemini 1.5 Flash", "Grounded RAG LLM", "Floor >= 0.55", CLR_GEMINI, w=240, h=160)

    # Engine 4: Ed25519 PKI
    draw_node_card(draw, 2350, 860, draw_icon_ed25519, "Ed25519 PKI Engine", "Asymmetric Signatures", "RFC 8032 & RFC 8785", CLR_ED25519, w=240, h=160)

    # Persistence Layer (Bottom Center)
    # PostgreSQL 16
    draw_node_card(draw, 1200, 1300, draw_icon_postgres, "PostgreSQL 16 Alpine", "Primary Relational Storage", "Forced RLS | consolith_app", CLR_POSTGRES, w=320, h=180)

    # Offline Verifiable QR Code
    draw_node_card(draw, 2350, 1490, draw_icon_audit, "Verifiable QR Code", "Offline Public Evidence", "Tamper-Evident Sign", CLR_ED25519, w=240, h=150)

    # Chained Immutable Audit Ledger
    draw_node_card(draw, 1200, 1660, draw_icon_audit, "SHA-256 Audit Ledger", "Cryptographic Hash Chain", "Trigger Blocks Mod", SLATE_800, w=320, h=160)

    # Network Boundary Callout Box in Bottom Left
    draw.rounded_rectangle([80, 1380, 780, 1780], radius=16, fill=SLATE_50, outline=PIPE_DATA, width=2)
    draw.text((110, 1400), "DOCKER NETWORK SEGREGATION TOPOLOGY", fill=PIPE_DATA, font=FONT_NODE_TITLE)
    draw.text((110, 1445), "[public-net]: Shared by Caddy, Next.js & FastAPI (Ingress 80/443)", fill=SLATE_700, font=FONT_LABEL)
    draw.text((110, 1485), "[internal-net]: Shared strictly by FastAPI, Postgres & Qdrant", fill=SLATE_700, font=FONT_LABEL)
    draw.text((110, 1525), "- ZERO Exposed Host Ports for Database & Vector Store", fill=PIPE_AI, font=FONT_LABEL)
    draw.text((110, 1565), "- ZERO External Internet Access for PostgreSQL & Qdrant", fill=PIPE_AI, font=FONT_LABEL)
    draw.text((110, 1605), "- Runtime connects strictly as unprivileged non-superuser role: consolith_app", fill=SLATE_700, font=FONT_LABEL)
    draw.text((110, 1645), "- Ephemeral documents unlinked immediately in finally block (Aadhaar Act 29)", fill=PIPE_DATA, font=FONT_LABEL)
    draw.text((110, 1685), "- Cryptographic link: Hash_n = SHA256(Hash_n-1 + event + timestamp)", fill=SLATE_700, font=FONT_LABEL)

    # Key Legend at Bottom Right
    draw.rounded_rectangle([width - 680, 1450, width - 80, 1780], radius=16, fill=SLATE_50, outline=SLATE_300, width=2)
    draw.text((width - 650, 1470), "PIPELINE FLOW LEGEND", fill=SLATE_900, font=FONT_NODE_TITLE)
    draw.line([(width - 650, 1520), (width - 550, 1520)], fill=PIPE_MAIN, width=4)
    draw.text((width - 530, 1510), "Core Synchronous HTTP Request / Response", fill=SLATE_700, font=FONT_NODE_SUB)
    draw.line([(width - 650, 1570), (width - 550, 1570)], fill=PIPE_DATA, width=4)
    draw.text((width - 530, 1560), "Encrypted RLS Persistence Stream (PostgreSQL)", fill=SLATE_700, font=FONT_NODE_SUB)
    draw.line([(width - 650, 1620), (width - 550, 1620)], fill=PIPE_AI, width=4)
    draw.text((width - 530, 1610), "Grounded Vector & LLM Pipeline (Qdrant & Gemini)", fill=SLATE_700, font=FONT_NODE_SUB)
    draw.line([(width - 650, 1670), (width - 550, 1670)], fill=PIPE_PKI, width=4)
    draw.text((width - 530, 1660), "Asymmetric Ed25519 PKI Attestation Stream", fill=SLATE_700, font=FONT_NODE_SUB)
    draw.line([(width - 650, 1720), (width - 550, 1720)], fill=PIPE_AUTH, width=4)
    draw.text((width - 530, 1710), "Identity & OTP Verification (Firebase & Resend)", fill=SLATE_700, font=FONT_NODE_SUB)

    # Save to disk
    out_path = os.path.join(OUTPUT_DIR, "convelina_master_system_architecture.png")
    img.save(out_path, "PNG", dpi=(300, 300))
    print(f"Generated {out_path} ({width}x{height})")
    return out_path


# ==============================================================================
# 2. FLOWING PIPELINE ROADMAP (Matching User's Reference Image 3)
# ==============================================================================
def generate_flowing_pipeline_roadmap():
    width, height = 3000, 1600
    img = Image.new("RGB", (width, height), BG_WHITE)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rounded_rectangle([50, 30, width - 50, 130], radius=16, fill=SLATE_900)
    draw.text((90, 48), "CONVELINA: END-TO-END FLOWING VERIFICATION PIPELINE", fill=WHITE, font=FONT_TITLE)
    draw.text((94, 96), "Direct Sequential Architecture: Ingress -> Security -> Compute -> OCR -> SIMD Matching -> Vector RAG -> PKI Attestation", fill=SLATE_400, font=FONT_SUBTITLE)

    # A grand, flowing pipeline from left to right with nodes mounted directly on the rail!
    # Central pipeline y-axis
    y_center = 750

    # Pipeline nodes in chronological journey order
    nodes = [
        {"x": 160, "icon": draw_icon_user, "title": "Citizen Request", "sub": "Browser Client", "badge": "Step 1: Upload"},
        {"x": 460, "icon": draw_icon_caddy, "title": "Caddy 2.8 Edge", "sub": "Reverse Proxy", "badge": "Step 2: Auto TLS"},
        {"x": 760, "icon": draw_icon_nextjs, "title": "Next.js 14 SSR", "sub": "Workspace UI", "badge": "Step 3: React 18"},
        {"x": 1060, "icon": draw_icon_fastapi, "title": "FastAPI Core", "sub": "Async ASGI Engine", "badge": "Step 4: Pydantic v2"},
        {"x": 1360, "icon": draw_icon_tesseract, "title": "Tesseract 5.5", "sub": "Ephemeral OCR", "badge": "Step 5: Verhoeff D5"},
        {"x": 1660, "icon": draw_icon_rapidfuzz, "title": "RapidFuzz AVX2", "sub": "SIMD Conflict Match", "badge": "Step 6: Metaphone"},
        {"x": 1960, "icon": draw_icon_qdrant, "title": "Qdrant Vector DB", "sub": "HNSW 25 Circulars", "badge": "Step 7: Floor >= 0.55"},
        {"x": 2260, "icon": draw_icon_gemini, "title": "Gemini 1.5 Flash", "sub": "Grounded Legal RAG", "badge": "Step 8: XML Output"},
        {"x": 2560, "icon": draw_icon_postgres, "title": "PostgreSQL 16", "sub": "Kernel Forced RLS", "badge": "Step 9: consolith_app"},
        {"x": 2840, "icon": draw_icon_ed25519, "title": "Ed25519 PKI", "sub": "Verifiable QR Sign", "badge": "Step 10: SHA-256 Link"}
    ]

    # Draw continuous glowing pipeline rail through all nodes
    rail_pts = [(n["x"], y_center) for n in nodes]
    draw_flowing_pipe(draw, rail_pts, color=PIPE_MAIN, width=6)

    # Draw nodes on top of the rail
    for i, node in enumerate(nodes):
        nx = node["x"]
        ny = y_center
        # Alternate cards slightly above and below the rail for clean reading and breathing room
        card_y = ny - 160 if i % 2 == 0 else ny + 160
        # Connector line from rail to card
        draw.line([(nx, ny), (nx, card_y)], fill=PIPE_MAIN, width=4)
        draw_step_circle(draw, nx, ny, i + 1, bg_color=PIPE_MAIN)
        draw_node_card(draw, nx, card_y, node["icon"], node["title"], node["sub"], node["badge"], PIPE_MAIN, w=220, h=150)

    # Add branch from Step 4 (FastAPI) up to Firebase & Resend
    draw_flowing_pipe(draw, [(1060, y_center - 240), (1060, 280), (1300, 280)], color=PIPE_AUTH, width=4, is_dashed=True)
    draw_arrow_head(draw, (1300, 280), "right", color=PIPE_AUTH, size=10)
    draw_node_card(draw, 1420, 280, draw_icon_firebase, "Firebase Auth", "RS256 JWT Verify", "Identity Check", PIPE_AUTH, w=200, h=140)

    draw_flowing_pipe(draw, [(1520, 280), (1700, 280)], color=PIPE_AUTH, width=4, is_dashed=True)
    draw_arrow_head(draw, (1700, 280), "right", color=PIPE_AUTH, size=10)
    draw_node_card(draw, 1820, 280, draw_icon_email, "Resend OTP", "Email Dispatch", "60s Rate Limit", PIPE_AUTH, w=200, h=140)

    # Add branch from Step 9 (Postgres) down to Immutable Audit Ledger
    draw_flowing_pipe(draw, [(2560, y_center + 240), (2560, 1300), (2700, 1300)], color=SLATE_800, width=4)
    draw_arrow_head(draw, (2700, 1300), "right", color=SLATE_800, size=10)
    draw_node_card(draw, 2840, 1300, draw_icon_audit, "SHA-256 Ledger", "Append-Only Audit", "DB Trigger Block", SLATE_800, w=220, h=140)

    out_path = os.path.join(OUTPUT_DIR, "convelina_tech_stack_roadmap.png")
    img.save(out_path, "PNG", dpi=(300, 300))
    print(f"Generated {out_path} ({width}x{height})")
    return out_path


# ==============================================================================
# 3. INTERCONNECTED DATA PIPELINES (Connected Step-by-Step Flow)
# ==============================================================================
def generate_connected_data_pipelines():
    width, height = 3000, 1600
    img = Image.new("RGB", (width, height), BG_WHITE)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rounded_rectangle([50, 30, width - 50, 130], radius=16, fill=SLATE_900)
    draw.text((90, 48), "CONVELINA: HIGH-ASSURANCE VERIFICATION & PRIVACY PIPELINES", fill=WHITE, font=FONT_TITLE)
    draw.text((94, 96), "End-to-End Cryptographic & Verification Data Flow: Ingestion, SIMD Conflict Resolution, Grounded RAG, and PKI Attestation", fill=SLATE_400, font=FONT_SUBTITLE)

    # We will lay out the 3 pipelines as 3 continuous connected horizontal flow rails!
    pipelines = [
        {
            "name": "PIPELINE 1: Ephemeral Ingestion & Zero-Storage Aadhaar Shredding (Aadhaar Act Sec 29)",
            "y": 340,
            "color": PIPE_MAIN,
            "steps": [
                ("1. Upload", "15MB Limit", draw_icon_user),
                ("2. Magic Bytes", "%PDF- Header", draw_icon_audit),
                ("3. POSIX 0600", "Ephemeral Scratch", draw_icon_server),
                ("4. Tesseract OCR", "Poppler C++", draw_icon_tesseract),
                ("5. Aadhaar Mask", "Verhoeff Check", draw_icon_ed25519),
                ("6. Fernet AES", "Encrypt at Rest", draw_icon_ed25519),
                ("7. RLS Insert", "PostgreSQL 16", draw_icon_postgres),
                ("8. Atomic Shred", "finally: unlink", draw_icon_testing)
            ]
        },
        {
            "name": "PIPELINE 2: Cross-Document Discrepancy Detection & SIMD Phonetic Evaluation",
            "y": 800,
            "color": CLR_RAPIDFUZZ,
            "steps": [
                ("1. Fetch Docs", "RLS Scoped Query", draw_icon_postgres),
                ("2. Canonical Pair", "doc_a < doc_b", draw_icon_audit),
                ("3. Normalizer", "Unicode NFKC", draw_icon_tesseract),
                ("4. RapidFuzz", "SIMD AVX2 C++", draw_icon_rapidfuzz),
                ("5. Jellyfish", "Double Metaphone", draw_icon_audit),
                ("6. Date Logic", "Year-Only YYYY", draw_icon_server),
                ("7. Idempotent DB", "uq_conflicts_pair", draw_icon_postgres),
                ("8. Audit Link", "SHA-256 Chained", draw_icon_audit)
            ]
        },
        {
            "name": "PIPELINE 3: Grounded Legal Circular RAG & Asymmetric Ed25519 PKI Attestation",
            "y": 1260,
            "color": CLR_ED25519,
            "steps": [
                ("1. Citizen Query", "POST /chat", draw_icon_user),
                ("2. Dense Embed", "1024-Dim Vector", draw_icon_qdrant),
                ("3. Qdrant HNSW", "25 Circulars", draw_icon_qdrant),
                ("4. Floor Guard", "Score >= 0.55", draw_icon_gemini),
                ("5. Gemini 1.5", "XML Grounding", draw_icon_gemini),
                ("6. Citation Test", "Anti-Hallucinate", draw_icon_testing),
                ("7. Officer Review", "Approve Dossier", draw_icon_user),
                ("8. Ed25519 Sign", "Verifiable QR", draw_icon_ed25519)
            ]
        }
    ]

    for p_idx, p in enumerate(pipelines):
        py = p["y"]
        pcolor = p["color"]
        # Section Header Banner
        draw.rounded_rectangle([60, py - 120, width - 60, py - 60], radius=10, fill=SLATE_100, outline=pcolor, width=2)
        draw.text((90, py - 105), p["name"], fill=SLATE_900, font=FONT_STAGE)

        # Flowing pipe line connecting all 8 steps in this pipeline
        steps = p["steps"]
        start_x = 180
        gap = 370
        pts = [(start_x + i * gap, py) for i in range(len(steps))]
        draw_flowing_pipe(draw, pts, color=pcolor, width=5)

        for i, (title, sub, icon_fn) in enumerate(steps):
            cx = start_x + i * gap
            cy = py
            draw_arrow_head(draw, (cx + gap // 2, cy), "right", color=pcolor, size=12) if i < len(steps) - 1 else None
            draw_step_circle(draw, cx, cy - 75, i + 1, bg_color=pcolor)
            draw_node_card(draw, cx, cy, icon_fn, title, sub, f"Step {i + 1}", pcolor, w=220, h=140)

    out_path = os.path.join(OUTPUT_DIR, "convelina_data_pipelines.png")
    img.save(out_path, "PNG", dpi=(300, 300))
    print(f"Generated {out_path} ({width}x{height})")
    return out_path


if __name__ == "__main__":
    generate_system_journey_pipeline()
    generate_flowing_pipeline_roadmap()
    generate_connected_data_pipelines()
