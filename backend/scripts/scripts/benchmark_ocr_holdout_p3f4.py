"""
CONVELINA — Phase P3F.4
Independent Holdout Evaluation Suite (Part F)

Evaluates OCR extraction, image quality penalties, and confidence calibration
on 24 completely fresh holdout scenarios with unseen personas, distinct fonts,
and authentic degradation simulations.
"""

import io
import os
import sys
import re
import json
import time
import math
import random
import tempfile
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

sys.path.insert(0, "/app")
sys.stdout.reconfigure(line_buffering=True)

from app.ocr.engine import default_ocr_engine
from app.ocr.field_extractor import FieldExtractor, CATEGORY_SCHEMAS


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def apply_mobile_camera_simulation(img: Image.Image) -> Image.Image:
    """
    Simulates mobile phone camera capture:
    1. Perspective distortion (subtle camera tilt).
    2. Vignette shadow (non-uniform ambient lighting).
    3. Lens soften.
    """
    w, h = img.size
    coeffs = [
        1.0, random.uniform(-0.01, 0.01), random.uniform(-6, 6),
        random.uniform(-0.01, 0.01), 1.0, random.uniform(-6, 6),
        0.00002, 0.00001
    ]
    transformed = img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BILINEAR)

    # Vignette
    vignette = Image.new("L", (w, h), 255)
    v_draw = ImageDraw.Draw(vignette)
    for r in range(max(w, h), 0, -20):
        alpha = int(255 * (r / max(w, h)) ** 0.8)
        v_draw.ellipse([w // 4 - r, h // 4 - r, w // 4 + r, h // 4 + r], fill=max(180, alpha))

    bg = Image.new("RGB", (w, h), (242, 240, 232))
    shadowed = Image.composite(transformed, bg, vignette)
    return shadowed.filter(ImageFilter.GaussianBlur(radius=0.4))


def render_holdout_image(
    lines: List[Tuple[str, int, Tuple[int, int, int]]],
    width: int = 1200,
    height: int = 800,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    is_tamil: bool = False,
    mobile_sim: bool = False,
    rotate_deg: float = 0.0,
    blur: bool = False,
    low_contrast: bool = False,
) -> Image.Image:
    """Renders text lines onto an image canvas with TrueType scalable fonts."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    dejavu_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    tamil_font = "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf"

    # Header banner
    draw.rectangle([0, 0, width, 50], fill=(235, 240, 250))
    header_font = ImageFont.truetype(dejavu_font, 16) if os.path.exists(dejavu_font) else ImageFont.load_default()
    draw.text((20, 15), "SYNTHETIC_TEST_ASSET • P3F.4 INDEPENDENT HOLDOUT • NOT OFFICIAL", fill=(100, 100, 120), font=header_font)

    y = 70
    for text, size, color in lines:
        has_tamil_char = bool(re.search(r"[\u0B80-\u0BFF]", text))
        chosen_font = tamil_font if (has_tamil_char and os.path.exists(tamil_font)) else dejavu_font
        try:
            line_font = ImageFont.truetype(chosen_font, size) if os.path.exists(chosen_font) else ImageFont.load_default()
        except Exception:
            line_font = ImageFont.load_default()
        draw.text((40, y), text, fill=color, font=line_font)
        y += size + 14

    if rotate_deg != 0.0:
        img = img.rotate(rotate_deg, expand=True, fillcolor=bg_color)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    if low_contrast:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(0.45)
    if mobile_sim:
        img = apply_mobile_camera_simulation(img)

    return img


# ==============================================================================
# P3F.4 BRAND-NEW INDEPENDENT HOLDOUT DATASET (24 SCENARIOS)
# ==============================================================================
HOLDOUT_DATASET_P3F4: List[Dict[str, Any]] = [
    # ---------------- AADHAAR (Persona: Suresh Krishnamurthy) ----------------
    {
        "id": "aadhaar_p3f4_01_digital",
        "category": "aadhaar",
        "condition": "Clean High-Res Digital Scan",
        "persona": "Suresh Krishnamurthy",
        "lines": [
            ("GOVERNMENT OF INDIA", 22, (0, 0, 0)),
            ("UNIQUE IDENTIFICATION AUTHORITY OF INDIA", 18, (40, 40, 40)),
            ("Enrolment No: 2045/88912/04512", 16, (80, 80, 80)),
            ("Name: Suresh Krishnamurthy", 22, (0, 0, 0)),
            ("DOB: 14/05/1989", 20, (0, 0, 0)),
            ("Gender: Male", 20, (0, 0, 0)),
            ("Address: 82 Luz Church Road, Mylapore, Chennai - 600004", 16, (50, 50, 50)),
            ("Aadhaar No: 9182 7364 5019", 24, (0, 0, 120)),
        ],
        "ground_truth": {
            "full_name": "Suresh Krishnamurthy",
            "date_of_birth": "1989-05-14",
            "gender": "Male",
            "pincode": "600004",
        },
        "expect_review": False,
        "is_tamil": False,
        "mobile_sim": False,
    },
    {
        "id": "aadhaar_p3f4_02_mobile_photo",
        "category": "aadhaar",
        "condition": "Mobile Camera Photo (Perspective + Vignette)",
        "persona": "Suresh Krishnamurthy",
        "lines": [
            ("GOVERNMENT OF INDIA", 22, (0, 0, 0)),
            ("Aadhaar Card", 20, (40, 40, 40)),
            ("Name: Suresh Krishnamurthy", 22, (0, 0, 0)),
            ("DOB: 14/05/1989", 20, (0, 0, 0)),
            ("Gender: Male", 20, (0, 0, 0)),
            ("Aadhaar No: 9182 7364 5019", 24, (0, 0, 0)),
        ],
        "ground_truth": {
            "full_name": "Suresh Krishnamurthy",
            "date_of_birth": "1989-05-14",
            "gender": "Male",
        },
        "expect_review": False,
        "is_tamil": False,
        "mobile_sim": True,
    },
    {
        "id": "aadhaar_p3f4_03_tamil_bilingual",
        "category": "aadhaar",
        "condition": "Tamil-English Bilingual Regional Identity Card",
        "persona": "Suresh Krishnamurthy",
        "lines": [
            ("இந்திய தனித்துவ அடையாள ஆணையம்", 20, (0, 0, 0)),
            ("UNIQUE IDENTIFICATION AUTHORITY OF INDIA", 18, (40, 40, 40)),
            ("பெயர்: சுரேஷ் கிருஷ்ணமூர்த்தி", 22, (0, 0, 0)),
            ("Name: Suresh Krishnamurthy", 22, (0, 0, 0)),
            ("பிறந்த தேதி: 14/05/1989", 20, (0, 0, 0)),
            ("DOB: 14/05/1989", 20, (0, 0, 0)),
            ("பாலினம்: ஆண் / Gender: Male", 20, (0, 0, 0)),
            ("Aadhaar No: 9182 7364 5019", 24, (0, 0, 100)),
        ],
        "ground_truth": {
            "full_name": "Suresh Krishnamurthy",
            "date_of_birth": "1989-05-14",
            "gender": "Male",
        },
        "expect_review": False,
        "is_tamil": True,
        "mobile_sim": False,
    },
    {
        "id": "aadhaar_p3f4_04_low_contrast_blur",
        "category": "aadhaar",
        "condition": "Severe Blur & Low Contrast (Requires Quality Penalty & Review)",
        "persona": "Suresh Krishnamurthy",
        "lines": [
            ("GOVERNMENT OF INDIA", 22, (100, 100, 100)),
            ("Name: Suresh Krishnamurthy", 22, (100, 100, 100)),
            ("DOB: 14/05/1989", 20, (100, 100, 100)),
            ("Gender: Male", 20, (100, 100, 100)),
            ("Aadhaar No: 9182 7364 5019", 24, (100, 100, 100)),
        ],
        "ground_truth": {
            "full_name": "Suresh Krishnamurthy",
            "date_of_birth": "1989-05-14",
            "gender": "Male",
        },
        "expect_review": True,
        "is_tamil": False,
        "mobile_sim": False,
        "blur": True,
        "low_contrast": True,
    },

    # ---------------- PAN (Persona: Divya Venkataraman) ----------------
    {
        "id": "pan_p3f4_05_digital",
        "category": "pan",
        "condition": "Clean High-Res Digital PAN Card",
        "persona": "Divya Venkataraman",
        "lines": [
            ("INCOME TAX DEPARTMENT", 22, (0, 0, 0)),
            ("GOVT. OF INDIA", 18, (40, 40, 40)),
            ("Permanent Account Number", 18, (50, 50, 50)),
            ("ABCDV1234E", 26, (0, 0, 140)),
            ("Name: Divya Venkataraman", 22, (0, 0, 0)),
            ("Father's Name: Venkataraman R", 20, (0, 0, 0)),
            ("Date of Birth: 22/08/1994", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "pan": "ABCDV1234E",
            "full_name": "Divya Venkataraman",
            "father_name": "Venkataraman R",
            "date_of_birth": "1994-08-22",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "pan_p3f4_06_mobile_photo",
        "category": "pan",
        "condition": "Mobile Phone Photo with Ambient Glare Simulation",
        "persona": "Divya Venkataraman",
        "lines": [
            ("INCOME TAX DEPARTMENT", 22, (20, 20, 20)),
            ("Permanent Account Number Card", 18, (50, 50, 50)),
            ("ABCDV1234E", 26, (0, 0, 100)),
            ("Divya Venkataraman", 22, (0, 0, 0)),
            ("Venkataraman R", 20, (0, 0, 0)),
            ("22/08/1994", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "pan": "ABCDV1234E",
            "full_name": "Divya Venkataraman",
            "father_name": "Venkataraman R",
            "date_of_birth": "1994-08-22",
        },
        "expect_review": False,
        "mobile_sim": True,
    },
    {
        "id": "pan_p3f4_07_iso_date_format",
        "category": "pan",
        "condition": "PAN with ISO Date Format (YYYY-MM-DD)",
        "persona": "Divya Venkataraman",
        "lines": [
            ("INCOME TAX DEPARTMENT", 22, (0, 0, 0)),
            ("ABCDV1234E", 26, (0, 0, 120)),
            ("Name: Divya Venkataraman", 22, (0, 0, 0)),
            ("Father's Name: Venkataraman R", 20, (0, 0, 0)),
            ("Date of Birth: 1994-08-22", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "pan": "ABCDV1234E",
            "full_name": "Divya Venkataraman",
            "father_name": "Venkataraman R",
            "date_of_birth": "1994-08-22",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "pan_p3f4_08_degraded_contrast",
        "category": "pan",
        "condition": "Low Contrast Degraded Image (Quality Penalty Triggers Review)",
        "persona": "Divya Venkataraman",
        "lines": [
            ("INCOME TAX DEPARTMENT", 22, (120, 120, 120)),
            ("ABCDV1234E", 26, (100, 100, 100)),
            ("Divya Venkataraman", 22, (100, 100, 100)),
            ("Venkataraman R", 20, (100, 100, 100)),
            ("22/08/1994", 20, (100, 100, 100)),
        ],
        "ground_truth": {
            "pan": "ABCDV1234E",
            "full_name": "Divya Venkataraman",
            "father_name": "Venkataraman R",
            "date_of_birth": "1994-08-22",
        },
        "expect_review": True,
        "blur": True,
        "low_contrast": True,
    },

    # ---------------- PASSPORT (Persona: Arvind Raghavan) ----------------
    {
        "id": "passport_p3f4_09_digital",
        "category": "passport",
        "condition": "Clean Passport Bio Page (Separated Given Name & Surname)",
        "persona": "Arvind Raghavan",
        "lines": [
            ("PASSPORT", 22, (0, 0, 0)),
            ("REPUBLIC OF INDIA", 20, (0, 0, 0)),
            ("Type: P   Country Code: IND   Passport No: Z1234567", 20, (0, 0, 100)),
            ("Surname: Raghavan", 22, (0, 0, 0)),
            ("Given Name(s): Arvind", 22, (0, 0, 0)),
            ("Nationality: INDIAN", 18, (0, 0, 0)),
            ("Sex: M", 18, (0, 0, 0)),
            ("Date of Birth: 30/03/1991", 20, (0, 0, 0)),
            ("Place of Birth: MUMBAI", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "passport_number": "Z1234567",
            "given_name": "Arvind",
            "surname": "Raghavan",
            "full_name": "Arvind Raghavan",
            "date_of_birth": "1991-03-30",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "passport_p3f4_10_multiline_slash",
        "category": "passport",
        "condition": "Passport with French/English Slash Subheadings",
        "persona": "Arvind Raghavan",
        "lines": [
            ("REPUBLIC OF INDIA / REPUBLIQUE D'INDE", 20, (0, 0, 0)),
            ("Passport No. / Passeport No: Z1234567", 20, (0, 0, 100)),
            ("Surname / Nom: Raghavan", 22, (0, 0, 0)),
            ("Given Names / Prenoms: Arvind", 22, (0, 0, 0)),
            ("Date of Birth / Date de naissance: 30/03/1991", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "passport_number": "Z1234567",
            "given_name": "Arvind",
            "surname": "Raghavan",
            "full_name": "Arvind Raghavan",
            "date_of_birth": "1991-03-30",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "passport_p3f4_11_mobile_camera",
        "category": "passport",
        "condition": "Mobile Photo of Passport (Camera Perspective Angle)",
        "persona": "Arvind Raghavan",
        "lines": [
            ("PASSPORT - REPUBLIC OF INDIA", 20, (0, 0, 0)),
            ("Passport No: Z1234567", 20, (0, 0, 80)),
            ("Surname: Raghavan", 22, (0, 0, 0)),
            ("Given Name(s): Arvind", 22, (0, 0, 0)),
            ("Date of Birth: 30/03/1991", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "passport_number": "Z1234567",
            "given_name": "Arvind",
            "surname": "Raghavan",
            "full_name": "Arvind Raghavan",
            "date_of_birth": "1991-03-30",
        },
        "expect_review": False,
        "mobile_sim": True,
    },
    {
        "id": "passport_p3f4_12_degraded_blur",
        "category": "passport",
        "condition": "Degraded Bio Page (Heavy Blur & Lighting Deficiency)",
        "persona": "Arvind Raghavan",
        "lines": [
            ("PASSPORT - REPUBLIC OF INDIA", 20, (110, 110, 110)),
            ("Passport No: Z1234567", 20, (100, 100, 100)),
            ("Surname: Raghavan", 22, (100, 100, 100)),
            ("Given Name(s): Arvind", 22, (100, 100, 100)),
            ("Date of Birth: 30/03/1991", 20, (100, 100, 100)),
        ],
        "ground_truth": {
            "passport_number": "Z1234567",
            "given_name": "Arvind",
            "surname": "Raghavan",
            "date_of_birth": "1991-03-30",
        },
        "expect_review": True,
        "blur": True,
        "low_contrast": True,
    },

    # ---------------- CLASS 10 (Persona: Pooja Swaminathan) ----------------
    {
        "id": "class10_p3f4_13_digital",
        "category": "education_10th",
        "condition": "Clean CBSE Class X Certificate",
        "persona": "Pooja Swaminathan",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (0, 0, 120)),
            ("SECONDARY SCHOOL EXAMINATION 2012", 20, (0, 0, 0)),
            ("This is to certify that: Pooja Swaminathan", 22, (0, 0, 0)),
            ("Father's Name: Swaminathan K", 20, (0, 0, 0)),
            ("Roll No: 4123890", 20, (0, 0, 0)),
            ("Date of Birth: 18/07/1996", 20, (0, 0, 0)),
            ("Year of Passing: 2012", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "student_name": "Pooja Swaminathan",
            "father_name": "Swaminathan K",
            "roll_number": "4123890",
            "year_of_passing": "2012",
            "board_name": "CBSE",
            "date_of_birth": "1996-07-18",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "class10_p3f4_14_mobile_photo",
        "category": "education_10th",
        "condition": "Mobile Photo of Class X Certificate",
        "persona": "Pooja Swaminathan",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (0, 0, 80)),
            ("SECONDARY SCHOOL CERTIFICATE", 20, (0, 0, 0)),
            ("Candidate Name: Pooja Swaminathan", 22, (0, 0, 0)),
            ("Father's Name: Swaminathan K", 20, (0, 0, 0)),
            ("Roll No: 4123890", 20, (0, 0, 0)),
            ("DOB: 18/07/1996", 20, (0, 0, 0)),
            ("Year: 2012", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "student_name": "Pooja Swaminathan",
            "father_name": "Swaminathan K",
            "roll_number": "4123890",
            "year_of_passing": "2012",
            "board_name": "CBSE",
            "date_of_birth": "1996-07-18",
        },
        "expect_review": False,
        "mobile_sim": True,
    },
    {
        "id": "class10_p3f4_15_multiline_candidate_label",
        "category": "education_10th",
        "condition": "Certificate with 'Name of Student:' Prefix and Distinct Roll Label",
        "persona": "Pooja Swaminathan",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (0, 0, 100)),
            ("Name of Student: Pooja Swaminathan", 22, (0, 0, 0)),
            ("Father's Name: Swaminathan K", 20, (0, 0, 0)),
            ("Registration / Roll: 4123890", 20, (0, 0, 0)),
            ("Date of Birth: 18/07/1996", 20, (0, 0, 0)),
            ("Year: 2012", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "student_name": "Pooja Swaminathan",
            "father_name": "Swaminathan K",
            "roll_number": "4123890",
            "year_of_passing": "2012",
            "board_name": "CBSE",
            "date_of_birth": "1996-07-18",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "class10_p3f4_16_degraded_blur",
        "category": "education_10th",
        "condition": "Severely Blurred Certificate (Triggers Manual Review)",
        "persona": "Pooja Swaminathan",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (110, 110, 110)),
            ("Pooja Swaminathan", 22, (100, 100, 100)),
            ("Father: Swaminathan K", 20, (100, 100, 100)),
            ("Roll No: 4123890", 20, (100, 100, 100)),
            ("DOB: 18/07/1996", 20, (100, 100, 100)),
        ],
        "ground_truth": {
            "student_name": "Pooja Swaminathan",
            "father_name": "Swaminathan K",
            "roll_number": "4123890",
        },
        "expect_review": True,
        "blur": True,
        "low_contrast": True,
    },

    # ---------------- CLASS 12 (Persona: Gautham Balasubramanian) ----------------
    {
        "id": "class12_p3f4_17_digital",
        "category": "education_12th",
        "condition": "Clean CBSE Class XII Certificate",
        "persona": "Gautham Balasubramanian",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (0, 0, 120)),
            ("SENIOR SCHOOL CERTIFICATE EXAMINATION 2014", 20, (0, 0, 0)),
            ("This is to certify that: Gautham Balasubramanian", 22, (0, 0, 0)),
            ("Father's Name: Balasubramanian N", 20, (0, 0, 0)),
            ("Roll No: 6219845", 20, (0, 0, 0)),
            ("Year of Passing: 2014", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "student_name": "Gautham Balasubramanian",
            "father_name": "Balasubramanian N",
            "roll_number": "6219845",
            "year_of_passing": "2014",
            "board_name": "CBSE",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "class12_p3f4_18_mobile_photo",
        "category": "education_12th",
        "condition": "Mobile Photo of Class XII Marksheet",
        "persona": "Gautham Balasubramanian",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (0, 0, 100)),
            ("CLASS XII MARKSHEET 2014", 20, (0, 0, 0)),
            ("Candidate: Gautham Balasubramanian", 22, (0, 0, 0)),
            ("Father's Name: Balasubramanian N", 20, (0, 0, 0)),
            ("Roll No: 6219845", 20, (0, 0, 0)),
            ("Year: 2014", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "student_name": "Gautham Balasubramanian",
            "father_name": "Balasubramanian N",
            "roll_number": "6219845",
            "year_of_passing": "2014",
            "board_name": "CBSE",
        },
        "expect_review": False,
        "mobile_sim": True,
    },
    {
        "id": "class12_p3f4_19_alt_roll_format",
        "category": "education_12th",
        "condition": "Class XII with Registration Roll Format",
        "persona": "Gautham Balasubramanian",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (0, 0, 100)),
            ("Name of Candidate: Gautham Balasubramanian", 22, (0, 0, 0)),
            ("Father: Balasubramanian N", 20, (0, 0, 0)),
            ("Roll Number: 6219845", 20, (0, 0, 0)),
            ("Year of Examination: 2014", 18, (0, 0, 0)),
        ],
        "ground_truth": {
            "student_name": "Gautham Balasubramanian",
            "father_name": "Balasubramanian N",
            "roll_number": "6219845",
            "year_of_passing": "2014",
            "board_name": "CBSE",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "class12_p3f4_20_low_contrast_blur",
        "category": "education_12th",
        "condition": "Low Contrast Degraded Class XII Certificate",
        "persona": "Gautham Balasubramanian",
        "lines": [
            ("CENTRAL BOARD OF SECONDARY EDUCATION", 24, (120, 120, 120)),
            ("Gautham Balasubramanian", 22, (100, 100, 100)),
            ("Roll No: 6219845", 20, (100, 100, 100)),
            ("Year: 2014", 18, (100, 100, 100)),
        ],
        "ground_truth": {
            "student_name": "Gautham Balasubramanian",
            "roll_number": "6219845",
        },
        "expect_review": True,
        "blur": True,
        "low_contrast": True,
    },

    # ---------------- EPF/UAN (Persona: Madhavan Srinivasan) ----------------
    {
        "id": "epf_p3f4_21_digital",
        "category": "epf_uan",
        "condition": "Clean EPFO Member Profile (Date of Exit = None/Present)",
        "persona": "Madhavan Srinivasan",
        "lines": [
            ("EMPLOYEES' PROVIDENT FUND ORGANISATION", 22, (0, 0, 0)),
            ("Member Profile & UAN Card", 20, (40, 40, 40)),
            ("Universal Account Number (UAN): 100987654321", 22, (0, 0, 120)),
            ("Member Name: Madhavan Srinivasan", 22, (0, 0, 0)),
            ("Father's Name: Srinivasan M", 20, (0, 0, 0)),
            ("Member ID: TN/MAS/0012345/000/0007890", 20, (0, 0, 0)),
            ("Date of Joining: 01/04/2018", 20, (0, 0, 0)),
            ("Date of Exit: -", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "uan": "100987654321",
            "member_name": "Madhavan Srinivasan",
            "father_name": "Srinivasan M",
            "member_id": "TN/MAS/0012345/000/0007890",
            "date_of_joining": "2018-04-01",
            "date_of_exit": None,
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "epf_p3f4_22_mobile_photo",
        "category": "epf_uan",
        "condition": "Mobile Photo of EPF Profile (Non-Adjacent Name)",
        "persona": "Madhavan Srinivasan",
        "lines": [
            ("EMPLOYEES' PROVIDENT FUND ORGANISATION", 22, (0, 0, 0)),
            ("UAN: 100987654321", 22, (0, 0, 100)),
            ("Establishment: ABC TECHNOLOGIES PVT LTD", 18, (0, 0, 0)),
            ("Member ID: TN/MAS/0012345/000/0007890", 20, (0, 0, 0)),
            ("Name: Madhavan Srinivasan", 22, (0, 0, 0)),
            ("DOJ: 01/04/2018", 20, (0, 0, 0)),
            ("DOE: N.A.", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "uan": "100987654321",
            "member_name": "Madhavan Srinivasan",
            "member_id": "TN/MAS/0012345/000/0007890",
            "date_of_joining": "2018-04-01",
            "date_of_exit": None,
        },
        "expect_review": False,
        "mobile_sim": True,
    },
    {
        "id": "epf_p3f4_23_reordered_layout",
        "category": "epf_uan",
        "condition": "EPFO Record with Reordered Columns and Valid Exit Date",
        "persona": "Madhavan Srinivasan",
        "lines": [
            ("EPFO - UNIFIED PORTAL", 22, (0, 0, 0)),
            ("Member ID: TN/MAS/0012345/000/0007890", 20, (0, 0, 0)),
            ("UAN: 100987654321", 22, (0, 0, 120)),
            ("Full Name: Madhavan Srinivasan", 22, (0, 0, 0)),
            ("Father: Srinivasan M", 20, (0, 0, 0)),
            ("Date of Exit: 31/12/2022", 20, (0, 0, 0)),
            ("Date of Joining: 01/04/2018", 20, (0, 0, 0)),
        ],
        "ground_truth": {
            "uan": "100987654321",
            "member_name": "Madhavan Srinivasan",
            "father_name": "Srinivasan M",
            "member_id": "TN/MAS/0012345/000/0007890",
            "date_of_joining": "2018-04-01",
            "date_of_exit": "2022-12-31",
        },
        "expect_review": False,
        "mobile_sim": False,
    },
    {
        "id": "epf_p3f4_24_degraded_blur",
        "category": "epf_uan",
        "condition": "Degraded EPF Profile (Severe Blur Triggers Review)",
        "persona": "Madhavan Srinivasan",
        "lines": [
            ("EMPLOYEES' PROVIDENT FUND ORGANISATION", 22, (110, 110, 110)),
            ("UAN: 100987654321", 22, (100, 100, 100)),
            ("Madhavan Srinivasan", 22, (100, 100, 100)),
            ("DOJ: 01/04/2018", 20, (100, 100, 100)),
        ],
        "ground_truth": {
            "uan": "100987654321",
            "member_name": "Madhavan Srinivasan",
            "date_of_joining": "2018-04-01",
        },
        "expect_review": True,
        "blur": True,
        "low_contrast": True,
    },
]


def run_holdout_evaluation():
    print("==================================================================")
    print("CONVELINA — Phase P3F.4: Independent Holdout Evaluation Suite")
    print("==================================================================")
    print(f"Total Scenarios in P3F.4 Dataset: {len(HOLDOUT_DATASET_P3F4)}")
    print("Zero Overlap with P3F.1, P3F.2, and P3F.3 Personas\n")

    total_fields_evaluated = 0
    exact_matches = 0
    total_cer_sum = 0.0
    cer_count = 0
    false_auto_acceptances = 0
    false_rejections = 0
    correct_acceptances = 0
    correct_reviews = 0

    confidences: List[float] = []
    correct_labels: List[int] = []
    review_decisions: List[bool] = []
    expected_reviews: List[bool] = []

    category_results: Dict[str, Dict[str, Any]] = {}
    for cat in ["aadhaar", "pan", "passport", "education_10th", "education_12th", "epf_uan"]:
        category_results[cat] = {
            "scenarios": 0,
            "fields_evaluated": 0,
            "exact_matches": 0,
            "cer_sum": 0.0,
            "cer_count": 0,
            "expected_review_matches": 0,
        }

    for item in HOLDOUT_DATASET_P3F4:
        scenario_id = item["id"]
        category = item["category"]
        gt = item["ground_truth"]
        expect_review = item["expect_review"]

        cat_stat = category_results[category]
        cat_stat["scenarios"] += 1

        img = render_holdout_image(
            lines=item["lines"],
            width=item.get("width", 1200),
            height=item.get("height", 800),
            is_tamil=item.get("is_tamil", False),
            mobile_sim=item.get("mobile_sim", False),
            rotate_deg=item.get("rotate_deg", 0.0),
            blur=item.get("blur", False),
            low_contrast=item.get("low_contrast", False),
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_f:
            tmp_path = tmp_f.name
            img.save(tmp_path, format="PNG")

        try:
            raw_text, ocr_conf = default_ocr_engine.extract_text_and_confidence(tmp_path, is_pdf=False)
            extraction = FieldExtractor.extract_category_fields(
                document_type=category,
                raw_text=raw_text,
                overall_confidence=ocr_conf
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        extracted_flat = extraction.fields_flat
        requires_review = extraction.requires_manual_review

        review_matched = (requires_review == expect_review)
        if review_matched:
            cat_stat["expected_review_matches"] += 1
        review_decisions.append(requires_review)
        expected_reviews.append(expect_review)

        print(f"[{category.upper()}] Scenario '{scenario_id}': {item['condition']}")
        print(f"  OCR Engine Conf: {ocr_conf:.3f} | Requires Manual Review: {requires_review} (Expected: {expect_review}) -> {'MATCH' if review_matched else 'DIVERGE'}")

        for field_name, expected_val in gt.items():
            total_fields_evaluated += 1
            cat_stat["fields_evaluated"] += 1

            extracted_val = extracted_flat.get(field_name)
            field_meta = extraction.field_extractions.get(field_name)
            f_conf = field_meta.confidence if field_meta else 0.0
            confidences.append(f_conf)

            # Missing optional field check (e.g. date_of_exit = None)
            if expected_val is None:
                is_correct = (extracted_val is None or extracted_val == "")
                if is_correct:
                    exact_matches += 1
                    cat_stat["exact_matches"] += 1
                    correct_labels.append(1)
                else:
                    correct_labels.append(0)
                print(f"  • {field_name}: (Optional None) -> Extracted: '{extracted_val}' [{'OK' if is_correct else 'FAIL'}]")
                continue

            s_exp = str(expected_val).strip()
            s_ext = str(extracted_val).strip() if extracted_val is not None else ""

            is_exact = (s_exp.lower() == s_ext.lower())

            if is_exact:
                exact_matches += 1
                cat_stat["exact_matches"] += 1
                correct_labels.append(1)
                cer = 0.0
            else:
                correct_labels.append(0)
                dist = levenshtein_distance(s_exp.lower(), s_ext.lower())
                cer = dist / max(len(s_exp), 1)

            total_cer_sum += cer
            cer_count += 1
            cat_stat["cer_sum"] += cer
            cat_stat["cer_count"] += 1

            f_requires_review = field_meta.review_required if field_meta else True
            if not is_exact and not f_requires_review:
                false_auto_acceptances += 1
            elif is_exact and f_requires_review:
                false_rejections += 1
            elif is_exact and not f_requires_review:
                correct_acceptances += 1
            elif not is_exact and f_requires_review:
                correct_reviews += 1

            status_str = "EXACT" if is_exact else f"DIFF (CER={cer:.2f})"
            print(f"  • {field_name}: Expected='{s_exp}' | Extracted='{s_ext}' (conf={f_conf:.2f}, rev={f_requires_review}) [{status_str}]")

        print("")

    exact_acc_pct = (exact_matches / total_fields_evaluated) * 100.0 if total_fields_evaluated else 0.0
    mean_cer_pct = (total_cer_sum / cer_count) * 100.0 if cer_count else 0.0
    overall_review_acc = (sum(1 for a, b in zip(review_decisions, expected_reviews) if a == b) / len(HOLDOUT_DATASET_P3F4)) * 100.0

    print("==================================================================")
    print("P3F.4 HOLDOUT OCR VALIDATION SUMMARY")
    print("==================================================================")
    print(f"Total Scenarios Evaluated       : {len(HOLDOUT_DATASET_P3F4)}")
    print(f"Total Demographic Fields Tested : {total_fields_evaluated}")
    print(f"Exact Match Field Accuracy      : {exact_acc_pct:.2f}% ({exact_matches}/{total_fields_evaluated})")
    print(f"Mean Character Error Rate (CER) : {mean_cer_pct:.2f}%")
    print(f"Document Review Trigger Accuracy: {overall_review_acc:.2f}% ({sum(1 for a, b in zip(review_decisions, expected_reviews) if a == b)}/{len(HOLDOUT_DATASET_P3F4)})")
    print(f"False Auto-Acceptance Count     : {false_auto_acceptances} (Defective extractions accepted without review)")
    print(f"False Rejection Count           : {false_rejections} (Correct extractions flagged for manual review)")
    print("------------------------------------------------------------------\n")

    print("CATEGORY-BY-CATEGORY BREAKDOWN:")
    for cat, stat in category_results.items():
        cat_acc = (stat["exact_matches"] / stat["fields_evaluated"]) * 100.0 if stat["fields_evaluated"] else 0.0
        cat_cer = (stat["cer_sum"] / stat["cer_count"]) * 100.0 if stat["cer_count"] else 0.0
        cat_rev = (stat["expected_review_matches"] / stat["scenarios"]) * 100.0 if stat["scenarios"] else 0.0
        print(f"  {cat.upper():<16}: Exact Match={cat_acc:6.2f}% | CER={cat_cer:5.2f}% | Review Trigger={cat_rev:6.2f}% ({stat['scenarios']} scenarios, {stat['fields_evaluated']} fields)")

    print("\n==================================================================")
    print("P3F.4 CONFIDENCE CALIBRATION & THRESHOLD ANALYSIS")
    print("==================================================================")

    # 1. Brier Score
    brier_score = sum((c - y) ** 2 for c, y in zip(confidences, correct_labels)) / len(confidences)
    print(f"Brier Score: {brier_score:.4f} (lower is better; 0.0 is perfect calibration)")

    # 2. Expected Calibration Error (ECE) across 10 bins
    num_bins = 10
    bins = [[] for _ in range(num_bins)]
    for c, y in zip(confidences, correct_labels):
        bin_idx = min(int(c * num_bins), num_bins - 1)
        bins[bin_idx].append((c, y))

    ece = 0.0
    mce = 0.0
    print("\nReliability Diagram / Calibration Bands:")
    print(f"{'Band':<14} | {'Count':<6} | {'Avg Conf':<10} | {'Empirical Acc':<14} | {'Gap (|Acc - Conf|)':<18}")
    print("-" * 72)
    for b_idx, b_items in enumerate(bins):
        low = b_idx / num_bins
        high = (b_idx + 1) / num_bins
        band_str = f"[{low:.1f}, {high:.1f})"
        if not b_items:
            print(f"{band_str:<14} | {0:<6} | {'N/A':<10} | {'N/A':<14} | {'N/A':<18}")
            continue
        avg_conf = sum(x[0] for x in b_items) / len(b_items)
        emp_acc = sum(x[1] for x in b_items) / len(b_items)
        gap = abs(emp_acc - avg_conf)
        ece += (len(b_items) / len(confidences)) * gap
        if gap > mce:
            mce = gap
        print(f"{band_str:<14} | {len(b_items):<6} | {avg_conf:<10.3f} | {emp_acc:<14.3f} | {gap:<18.3f}")

    print("-" * 72)
    print(f"Expected Calibration Error (ECE): {ece:.4f} ({ece * 100:.2f}%)")
    print(f"Maximum Calibration Error (MCE) : {mce:.4f} ({mce * 100:.2f}%)")

    # 3. Threshold Sweep Analysis: comparing thresholds theta in [0.60, 0.65, 0.70, 0.75, 0.80, 0.85]
    print("\nReview Threshold (theta) Trade-off Sweep Analysis:")
    print(f"{'Threshold':<10} | {'Auto-Accept Acc':<16} | {'False Auto-Accept':<18} | {'Manual Review Rate':<18}")
    print("-" * 70)
    for theta in [0.60, 0.65, 0.70, 0.75, 0.80, 0.85]:
        auto_accepted = [(c, y) for c, y in zip(confidences, correct_labels) if c >= theta]
        manual_review = [y for c, y in zip(confidences, correct_labels) if c < theta]

        aa_count = len(auto_accepted)
        mr_count = len(manual_review)
        aa_acc = (sum(y for _, y in auto_accepted) / aa_count * 100.0) if aa_count else 100.0
        faa_count = sum(1 for _, y in auto_accepted if y == 0)
        mr_rate = (mr_count / len(confidences)) * 100.0

        marker = " <-- CURRENT SETTING" if theta == 0.75 else ""
        print(f"{theta:<10.2f} | {aa_acc:6.2f}% ({aa_count:>2}/{len(confidences)}) | {faa_count:>2} leaking errors   | {mr_rate:6.2f}% ({mr_count:>2}/{len(confidences)}){marker}")

    print("==================================================================")
    print("P3F.4 INDEPENDENT HOLDOUT BENCHMARK EXECUTION COMPLETE")
    print("==================================================================")


if __name__ == "__main__":
    run_holdout_evaluation()
