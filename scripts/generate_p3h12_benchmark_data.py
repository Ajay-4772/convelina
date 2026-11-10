"""
CONVELINA — P3H.12 Realistic Document Intelligence Benchmark Generator
Creates a reproducible, entirely synthetic benchmark across all six Tier 1 categories:
1. Aadhaar Card
2. PAN Card
3. Passport
4. Class 10 Certificate
5. Class 12 Certificate
6. EPFO/UAN Records

Generates realistic visual variations:
- Clean high-resolution scans
- Photographed appearances (shadow gradients, uneven lighting)
- Rotation and skew (-7.0 deg, +5.0 deg)
- Low resolution and downsampling
- Blur and noise
- JPEG compression artifacts
- Partially obscured text / crease smudges
- Multi-script support (English, Hindi, Tamil)

Every image is paired with a machine-readable ground-truth annotation JSON file.
STRICT SAFETY: Uses 100% fictional names, synthetic numbers, and test profiles.
"""

import os
import sys
import json
import math
import random
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Output directories
BASE_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = BASE_DIR / "benchmarks" / "p3h12"
IMAGES_DIR = BENCHMARK_DIR / "images"
ANNOTATIONS_DIR = BENCHMARK_DIR / "annotations"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, font_type: str = "sans", script: str = "latin") -> ImageFont.ImageFont:
    """Selects available TrueType font based on style, script, and OS."""
    font_paths = []
    
    if script in ("indic", "hindi", "tamil"):
        font_paths.extend([
            "C:/Windows/Fonts/nirmala.ttf",
            "C:/Windows/Fonts/Nirmala.ttf",
            "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])
    
    if font_type == "serif":
        font_paths.extend([
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/georgia.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ])
    elif font_type == "mono":
        font_paths.extend([
            "C:/Windows/Fonts/cour.ttf",
            "C:/Windows/Fonts/consola.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ])
    else:  # sans
        font_paths.extend([
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])
    
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# 6 Synthetic Profiles (100% fictional)
PROFILES = [
    {
        "id": "prof_1",
        "full_name": "RAJESH KUMAR VERMA",
        "name_hindi": "राजेश कुमार वर्मा",
        "name_tamil": "ராஜேஷ் குமார் வர்மா",
        "father_name": "SURESH CHANDRA VERMA",
        "mother_name": "SUNITA VERMA",
        "gender": "Male",
        "dob": "12/04/1988",
        "dob_iso": "1988-04-12",
        "address": "42, Shanti Vihar, Ring Road, New Delhi",
        "pincode": "110001",
        "aadhaar": "9876 5432 1098",
        "pan": "ABCDE1234F",
        "passport": "Z1234567",
        "roll_10": "6124589",
        "reg_10": "R/2004/6124589",
        "year_10": "2004",
        "roll_12": "8245190",
        "reg_12": "R/2006/8245190",
        "year_12": "2006",
        "uan": "100912345678",
        "member_id": "DLCPM00123450000067890",
        "establishment": "TECHCON CLOUD SOLUTIONS PRIVATE LIMITED",
        "establishment_id": "DLCPM0012345000",
        "doj": "01/07/2012",
        "doe": "31/03/2018",
    },
    {
        "id": "prof_2",
        "full_name": "PRIYA RAMANATHAN",
        "name_hindi": "प्रिया रामनाथन",
        "name_tamil": "பிரியா ராமநாதன்",
        "father_name": "K. RAMANATHAN",
        "mother_name": "MEENAKSHI RAMANATHAN",
        "gender": "Female",
        "dob": "25/08/1994",
        "dob_iso": "1994-08-25",
        "address": "15, Anna Salai, T Nagar, Chennai, Tamil Nadu",
        "pincode": "600017",
        "aadhaar": "8765 4321 0987",
        "pan": "BKPPR5678G",
        "passport": "M9876543",
        "roll_10": "4512789",
        "reg_10": "TN/2010/4512789",
        "year_10": "2010",
        "roll_12": "7823410",
        "reg_12": "TN/2012/7823410",
        "year_12": "2012",
        "uan": "100823456789",
        "member_id": "TNMAS00456780000012345",
        "establishment": "CHENNAI INFOTECH ENTERPRISES LIMITED",
        "establishment_id": "TNMAS0045678000",
        "doj": "15/06/2016",
        "doe": "28/02/2021",
    },
    {
        "id": "prof_3",
        "full_name": "ANIRBAN BANERJEE",
        "name_hindi": "अनिर्बान बनर्जी",
        "name_tamil": "அனிர்பன் பானர்ஜி",
        "father_name": "SUBRATA BANERJEE",
        "mother_name": "APARNA BANERJEE",
        "gender": "Male",
        "dob": "14/11/1985",
        "dob_iso": "1985-11-14",
        "address": "88/2, Rashbehari Avenue, Ballygunge, Kolkata",
        "pincode": "700029",
        "aadhaar": "7654 3210 9876",
        "pan": "CDBAB9012H",
        "passport": "K3456789",
        "roll_10": "3129845",
        "reg_10": "WB/2001/3129845",
        "year_10": "2001",
        "roll_12": "5421098",
        "reg_12": "WB/2003/5421098",
        "year_12": "2003",
        "uan": "100734567890",
        "member_id": "WBCAL00789010000023456",
        "establishment": "BENGAL CONSULTING SERVICES LLP",
        "establishment_id": "WBCAL0078901000",
        "doj": "10/01/2008",
        "doe": "15/09/2015",
    },
    {
        "id": "prof_4",
        "full_name": "NEHA PATEL",
        "name_hindi": "नेहा पटेल",
        "name_tamil": "நேகா படேல்",
        "father_name": "BHAVESH PATEL",
        "mother_name": "GITABEN PATEL",
        "gender": "Female",
        "dob": "03/02/1992",
        "dob_iso": "1992-02-03",
        "address": "204, Shreerang Society, SG Highway, Ahmedabad",
        "pincode": "380054",
        "aadhaar": "6543 2109 8765",
        "pan": "DFGNP3456J",
        "passport": "J7890123",
        "roll_10": "5123987",
        "reg_10": "GJ/2008/5123987",
        "year_10": "2008",
        "roll_12": "8934521",
        "reg_12": "GJ/2010/8934521",
        "year_12": "2010",
        "uan": "100645678901",
        "member_id": "GJAHD00234560000034567",
        "establishment": "GUJARAT POLYMERS & CHEMICALS LTD",
        "establishment_id": "GJAHD0023456000",
        "doj": "01/08/2014",
        "doe": None,
    },
    {
        "id": "prof_5",
        "full_name": "S. K. SHARMA",
        "name_hindi": "एस. के. शर्मा",
        "name_tamil": "எஸ். கே. சர்மா",
        "father_name": "MAHESH SHARMA",
        "mother_name": "KAVITA SHARMA",
        "gender": "Male",
        "dob": "19/09/1990",
        "dob_iso": "1990-09-19",
        "address": "12, Malviya Nagar, Jaipur, Rajasthan",
        "pincode": "302017",
        "aadhaar": "5432 1098 7654",
        "pan": "EGHPS7890K",
        "passport": "H2345678",
        "roll_10": "6234890",
        "reg_10": "RJ/2006/6234890",
        "year_10": "2006",
        "roll_12": "9123456",
        "reg_12": "RJ/2008/9123456",
        "year_12": "2008",
        "uan": "100556789012",
        "member_id": "RJJAI00567890000045678",
        "establishment": "RAJASTHAN TEXTILE TRADERS PRIVATE LTD",
        "establishment_id": "RJJAI0056789000",
        "doj": "12/03/2013",
        "doe": "30/11/2019",
    },
    {
        "id": "prof_6",
        "full_name": "LAKSHMI SUNDARAM",
        "name_hindi": "लक्ष्मी सुंदरम",
        "name_tamil": "லட்சுமி சுந்தரம்",
        "father_name": "R. SUNDARAM",
        "mother_name": "VASANTHA SUNDARAM",
        "gender": "Female",
        "dob": "30/06/1996",
        "dob_iso": "1996-06-30",
        "address": "77, Gandhi Road, West Mambalam, Chennai",
        "pincode": "600033",
        "aadhaar": "4321 0987 6543",
        "pan": "FHJLS1234L",
        "passport": "G5678901",
        "roll_10": "7124901",
        "reg_10": "CBSE/2012/7124901",
        "year_10": "2012",
        "roll_12": "9456123",
        "reg_12": "CBSE/2014/9456123",
        "year_12": "2014",
        "uan": "100467890123",
        "member_id": "TNMAS00890120000056789",
        "establishment": "SOUTHERN HEALTHCARE DIAGNOSTICS",
        "establishment_id": "TNMAS0089012000",
        "doj": "01/09/2018",
        "doe": None,
    }
]

# 8 Visual Conditions
CONDITIONS = [
    {
        "code": "clean_scan",
        "name": "Clean High-Resolution Scan",
        "description": "High resolution, sharp contrast, neutral white background (300 DPI baseline)",
        "expected_review": False,
    },
    {
        "code": "photo_shadow",
        "name": "Photographed Appearance with Shadow",
        "description": "Mobile camera capture with radial gradient lighting and uneven falloff",
        "expected_review": False,
    },
    {
        "code": "skewed_rot",
        "name": "Rotated & Skewed Alignment",
        "description": "Image rotated by 5.5 degrees clockwise testing deskewing pipeline",
        "expected_review": False,
    },
    {
        "code": "low_resolution",
        "name": "Low Resolution Downsampling",
        "description": "Image downsampled to 480x300 and scaled up; pixelation noise",
        "expected_review": True,
    },
    {
        "code": "blur_noise",
        "name": "Optical Blur & Sensor Noise",
        "description": "Gaussian blur (radius 1.8) and additive Gaussian speckle noise",
        "expected_review": True,
    },
    {
        "code": "compression",
        "name": "Heavy JPEG Compression Artifacts",
        "description": "Low quality JPEG compression (Q=28) with 8x8 DCT boundary ringing",
        "expected_review": False,
    },
    {
        "code": "obscured_crease",
        "name": "Partially Obscured / Paper Crease",
        "description": "Paper crease and minor ink smudge across field boundaries",
        "expected_review": True,
    },
    {
        "code": "bilingual_script",
        "name": "Bilingual Multi-Script Formatting",
        "description": "Official layout with dual English and Indic (Hindi/Tamil) field values",
        "expected_review": False,
    },
]


def render_document_card(
    category: str,
    profile: dict,
    condition: dict,
    width: int = 1200,
    height: int = 750,
) -> Tuple[Image.Image, dict, str]:
    """
    Renders a realistic synthetic card image and returns (image, ground_truth_fields, full_text).
    """
    bg_color = (255, 255, 255)
    text_color = (20, 20, 20)
    label_color = (80, 80, 80)
    border_color = (180, 180, 180)
    accent_color = (30, 60, 120)

    if category == "pan":
        accent_color = (30, 90, 140)
        width, height = 1100, 700
    elif category == "passport":
        accent_color = (20, 40, 90)
        width, height = 1200, 850
    elif category in ("education_10th", "education_12th"):
        accent_color = (120, 40, 30)
        width, height = 1250, 850
    elif category == "epf":
        accent_color = (20, 100, 60)
        width, height = 1200, 800

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_type = "serif" if category in ("education_10th", "education_12th") else ("mono" if category == "epf" else "sans")
    is_bilingual = condition["code"] == "bilingual_script"
    
    f_title = get_font(24, font_type=font_type)
    f_sub = get_font(14, font_type=font_type)
    f_label = get_font(13, font_type="sans")
    f_val = get_font(16, font_type=font_type)
    f_indic = get_font(15, script="indic")
    f_banner = get_font(11, font_type="sans")

    # Card outer border
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=border_color, width=2)
    draw.rectangle([(24, 24), (width - 24, height - 24)], outline=accent_color, width=1)

    # Top banner: Mandatory Synthetic Development Notice
    draw.rectangle([(25, 25), (width - 25, 60)], fill=(254, 242, 242))
    draw.text(
        (width // 2, 42),
        "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
        font=f_banner,
        fill=(185, 28, 28),
        anchor="mm"
    )

    y_offset = 75
    full_text_lines = ["SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM"]
    ground_truth = {}

    # Category-Specific Layout and Fields
    if category == "aadhaar":
        auth_title = "GOVERNMENT OF INDIA / भारत सरकार" if is_bilingual else "GOVERNMENT OF INDIA"
        doc_title = "Unique Identification Authority of India (Sample)"
        draw.text((width // 2, y_offset), auth_title, font=f_title, fill=accent_color, anchor="mt")
        y_offset += 32
        draw.text((width // 2, y_offset), doc_title, font=f_sub, fill=label_color, anchor="mt")
        y_offset += 40
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=accent_color, width=2)
        y_offset += 25

        full_text_lines.extend([auth_title, doc_title])

        # Photo placeholder
        draw.rectangle([(60, y_offset), (220, y_offset + 200)], fill=(240, 240, 240), outline=(200, 200, 200), width=1)
        draw.text((140, y_offset + 100), "[ PHOTOGRAPH ]", font=f_banner, fill=(150, 150, 150), anchor="mm")

        # Details
        x_text = 260
        name_str = profile["full_name"]
        if is_bilingual:
            draw.text((x_text, y_offset), profile["name_hindi"], font=f_indic, fill=text_color)
            y_offset += 26
        draw.text((x_text, y_offset), f"Name: {name_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Name: {name_str}")
        ground_truth["full_name"] = name_str
        y_offset += 35

        dob_str = profile["dob"]
        draw.text((x_text, y_offset), f"DOB: {dob_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"DOB: {dob_str}")
        ground_truth["date_of_birth"] = profile["dob_iso"]
        y_offset += 35

        gender_str = profile["gender"]
        draw.text((x_text, y_offset), f"Gender: {gender_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Gender: {gender_str}")
        ground_truth["gender"] = gender_str
        y_offset += 35

        addr_str = profile["address"]
        draw.text((x_text, y_offset), f"Address: {addr_str}", font=f_label, fill=text_color)
        full_text_lines.append(f"Address: {addr_str}")
        ground_truth["address"] = addr_str
        ground_truth["pincode"] = profile["pincode"]
        y_offset += 65

        # Aadhaar Number block
        aadhaar_num = profile["aadhaar"]
        draw.rectangle([(width // 2 - 250, y_offset), (width // 2 + 250, y_offset + 50)], fill=(245, 245, 245), outline=border_color)
        f_num = get_font(24, font_type="mono")
        draw.text((width // 2, y_offset + 25), aadhaar_num, font=f_num, fill=accent_color, anchor="mm")
        full_text_lines.append(f"Aadhaar Number: {aadhaar_num}")
        ground_truth["aadhaar_number"] = aadhaar_num
        ground_truth["document_number"] = aadhaar_num
        ground_truth["issuing_authority"] = "UIDAI"

    elif category == "pan":
        auth_title = "INCOME TAX DEPARTMENT"
        doc_title = "GOVT. OF INDIA / भारत सरकार" if is_bilingual else "GOVT. OF INDIA"
        draw.text((width // 2, y_offset), auth_title, font=f_title, fill=accent_color, anchor="mt")
        y_offset += 30
        draw.text((width // 2, y_offset), doc_title, font=f_sub, fill=label_color, anchor="mt")
        y_offset += 35
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=accent_color, width=2)
        y_offset += 25

        full_text_lines.extend([auth_title, doc_title])

        # Photo placeholder
        draw.rectangle([(60, y_offset), (200, y_offset + 180)], fill=(240, 240, 240), outline=(200, 200, 200), width=1)
        draw.text((130, y_offset + 90), "[ PHOTO ]", font=f_banner, fill=(150, 150, 150), anchor="mm")

        # Fields
        x_text = 240
        pan_num = profile["pan"]
        f_pan_num = get_font(22, font_type="mono")
        draw.text((x_text, y_offset), f"Permanent Account Number: {pan_num}", font=f_pan_num, fill=accent_color)
        full_text_lines.append(f"Permanent Account Number: {pan_num}")
        ground_truth["pan_number"] = pan_num
        ground_truth["document_number"] = pan_num
        ground_truth["issuing_authority"] = "Income Tax Department"
        y_offset += 40

        name_str = profile["full_name"]
        draw.text((x_text, y_offset), "Name:", font=f_label, fill=label_color)
        draw.text((x_text + 120, y_offset), name_str, font=f_val, fill=text_color)
        full_text_lines.append(f"Name: {name_str}")
        ground_truth["full_name"] = name_str
        y_offset += 35

        father_str = profile["father_name"]
        draw.text((x_text, y_offset), "Father's Name:", font=f_label, fill=label_color)
        draw.text((x_text + 120, y_offset), father_str, font=f_val, fill=text_color)
        full_text_lines.append(f"Father's Name: {father_str}")
        ground_truth["father_name"] = father_str
        ground_truth["parent_guardian_name"] = father_str
        y_offset += 35

        dob_str = profile["dob"]
        draw.text((x_text, y_offset), "Date of Birth:", font=f_label, fill=label_color)
        draw.text((x_text + 120, y_offset), dob_str, font=f_val, fill=text_color)
        full_text_lines.append(f"Date of Birth: {dob_str}")
        ground_truth["date_of_birth"] = profile["dob_iso"]

    elif category == "passport":
        auth_title = "PASSPORT / पासपोर्ट" if is_bilingual else "PASSPORT"
        doc_title = "REPUBLIC OF INDIA / भारत गणराज्य" if is_bilingual else "REPUBLIC OF INDIA"
        draw.text((width // 2, y_offset), auth_title, font=f_title, fill=accent_color, anchor="mt")
        y_offset += 30
        draw.text((width // 2, y_offset), doc_title, font=f_sub, fill=label_color, anchor="mt")
        y_offset += 35
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=accent_color, width=2)
        y_offset += 25

        full_text_lines.extend([auth_title, doc_title])

        # Photo
        draw.rectangle([(50, y_offset), (210, y_offset + 220)], fill=(240, 240, 240), outline=(200, 200, 200), width=1)
        draw.text((130, y_offset + 110), "[ PASSPORT PHOTO ]", font=f_banner, fill=(150, 150, 150), anchor="mm")

        x_col1 = 250
        pass_num = profile["passport"]
        draw.text((x_col1, y_offset), f"Passport No: {pass_num}", font=f_val, fill=accent_color)
        full_text_lines.append(f"Passport No: {pass_num}")
        ground_truth["passport_number"] = pass_num
        ground_truth["document_number"] = pass_num
        ground_truth["issuing_authority"] = "Ministry of External Affairs"
        y_offset += 32

        name_str = profile["full_name"]
        draw.text((x_col1, y_offset), f"Given Name: {name_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Given Name: {name_str}")
        ground_truth["full_name"] = name_str
        y_offset += 32

        draw.text((x_col1, y_offset), f"Nationality: INDIAN", font=f_label, fill=text_color)
        y_offset += 28

        gender_str = profile["gender"]
        draw.text((x_col1, y_offset), f"Sex: {gender_str[0]}", font=f_label, fill=text_color)
        ground_truth["gender"] = gender_str
        y_offset += 28

        dob_str = profile["dob"]
        draw.text((x_col1, y_offset), f"Date of Birth: {dob_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Date of Birth: {dob_str}")
        ground_truth["date_of_birth"] = profile["dob_iso"]
        y_offset += 32

        father_str = profile["father_name"]
        draw.text((x_col1, y_offset), f"Name of Father: {father_str}", font=f_label, fill=text_color)
        full_text_lines.append(f"Name of Father: {father_str}")
        ground_truth["father_name"] = father_str
        ground_truth["parent_guardian_name"] = father_str
        y_offset += 28

        mother_str = profile["mother_name"]
        draw.text((x_col1, y_offset), f"Name of Mother: {mother_str}", font=f_label, fill=text_color)
        ground_truth["mother_name"] = mother_str
        y_offset += 40

        # Machine Readable Zone (MRZ)
        mrz_line1 = f"P<IND{name_str.replace(' ', '<')}<<<<<<<<<<<<<<<<<<<<"[:44]
        mrz_line2 = f"{pass_num}4IND{profile['dob_iso'].replace('-', '')[2:]}5M<<<<<<<<<<3"[:44]
        f_mrz = get_font(16, font_type="mono")
        draw.rectangle([(40, height - 90), (width - 40, height - 35)], fill=(248, 248, 248), outline=border_color)
        draw.text((50, height - 85), mrz_line1, font=f_mrz, fill=(40, 40, 40))
        draw.text((50, height - 60), mrz_line2, font=f_mrz, fill=(40, 40, 40))
        full_text_lines.extend([mrz_line1, mrz_line2])

    elif category in ("education_10th", "education_12th"):
        is_12th = category == "education_12th"
        auth_title = "CENTRAL BOARD OF SECONDARY EDUCATION"
        doc_title = "SENIOR SCHOOL CERTIFICATE EXAMINATION (CLASS XII)" if is_12th else "SECONDARY SCHOOL EXAMINATION (CLASS X)"
        sub_title = "MARKS STATEMENT AND PROVISIONAL CERTIFICATE"
        
        draw.text((width // 2, y_offset), auth_title, font=f_title, fill=accent_color, anchor="mt")
        y_offset += 32
        draw.text((width // 2, y_offset), doc_title, font=f_sub, fill=label_color, anchor="mt")
        y_offset += 24
        draw.text((width // 2, y_offset), sub_title, font=f_banner, fill=label_color, anchor="mt")
        y_offset += 30
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=accent_color, width=2)
        y_offset += 25

        full_text_lines.extend([auth_title, doc_title, sub_title])

        roll_key = "roll_12" if is_12th else "roll_10"
        reg_key = "reg_12" if is_12th else "reg_10"
        year_key = "year_12" if is_12th else "year_10"

        roll_num = profile[roll_key]
        reg_num = profile[reg_key]
        year_num = profile[year_key]

        draw.text((70, y_offset), f"Roll No: {roll_num}", font=f_val, fill=accent_color)
        draw.text((width - 350, y_offset), f"Registration No: {reg_num}", font=f_val, fill=accent_color)
        full_text_lines.append(f"Roll No: {roll_num}")
        full_text_lines.append(f"Registration No: {reg_num}")
        ground_truth["roll_number"] = roll_num
        ground_truth["registration_number"] = reg_num
        ground_truth["document_number"] = roll_num
        ground_truth["board"] = "CBSE"
        ground_truth["passing_year"] = year_num
        ground_truth["issuing_authority"] = "CBSE"
        y_offset += 40

        name_str = profile["full_name"]
        draw.text((70, y_offset), f"Candidate Name: {name_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Candidate Name: {name_str}")
        ground_truth["full_name"] = name_str
        y_offset += 35

        father_str = profile["father_name"]
        draw.text((70, y_offset), f"Father's Name: {father_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Father's Name: {father_str}")
        ground_truth["father_name"] = father_str
        ground_truth["parent_guardian_name"] = father_str
        y_offset += 35

        mother_str = profile["mother_name"]
        draw.text((70, y_offset), f"Mother's Name: {mother_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Mother's Name: {mother_str}")
        ground_truth["mother_name"] = mother_str
        y_offset += 35

        dob_str = profile["dob"]
        draw.text((70, y_offset), f"Date of Birth: {dob_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Date of Birth: {dob_str}")
        ground_truth["date_of_birth"] = profile["dob_iso"]
        y_offset += 45

        # Grades table snippet
        draw.rectangle([(70, y_offset), (width - 70, y_offset + 90)], fill=(250, 250, 250), outline=border_color)
        draw.text((90, y_offset + 15), "SUBJECT: ENGLISH CORE (301) - 088 MARKS - GRADE A1", font=f_banner, fill=label_color)
        draw.text((90, y_offset + 35), "SUBJECT: MATHEMATICS (041) - 092 MARKS - GRADE A1", font=f_banner, fill=label_color)
        draw.text((90, y_offset + 55), "FINAL RESULT: PASSED", font=f_val, fill=accent_color)
        full_text_lines.append("FINAL RESULT: PASSED")
        ground_truth["result"] = "PASSED"

    elif category == "epf":
        auth_title = "EMPLOYEES' PROVIDENT FUND ORGANISATION, INDIA"
        doc_title = "MEMBER PASSBOOK & REGISTRATION PARTICULARS"
        draw.text((width // 2, y_offset), auth_title, font=f_title, fill=accent_color, anchor="mt")
        y_offset += 30
        draw.text((width // 2, y_offset), doc_title, font=f_sub, fill=label_color, anchor="mt")
        y_offset += 30
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=accent_color, width=2)
        y_offset += 25

        full_text_lines.extend([auth_title, doc_title])

        uan_num = profile["uan"]
        draw.text((70, y_offset), f"Universal Account Number (UAN): {uan_num}", font=f_val, fill=accent_color)
        full_text_lines.append(f"Universal Account Number (UAN): {uan_num}")
        ground_truth["uan"] = uan_num
        ground_truth["document_number"] = uan_num
        ground_truth["issuing_authority"] = "EPFO"
        y_offset += 35

        member_id = profile["member_id"]
        draw.text((70, y_offset), f"Member ID: {member_id}", font=f_val, fill=text_color)
        full_text_lines.append(f"Member ID: {member_id}")
        ground_truth["member_id"] = member_id
        y_offset += 35

        name_str = profile["full_name"]
        draw.text((70, y_offset), f"Member Name: {name_str}", font=f_val, fill=text_color)
        full_text_lines.append(f"Member Name: {name_str}")
        ground_truth["full_name"] = name_str
        y_offset += 35

        est_name = profile["establishment"]
        draw.text((70, y_offset), f"Establishment: {est_name}", font=f_val, fill=text_color)
        full_text_lines.append(f"Establishment: {est_name}")
        ground_truth["employer_name"] = est_name
        ground_truth["establishment_id"] = profile["establishment_id"]
        y_offset += 35

        doj_str = profile["doj"]
        draw.text((70, y_offset), f"Date of Joining: {doj_str}", font=f_label, fill=text_color)
        full_text_lines.append(f"Date of Joining: {doj_str}")
        ground_truth["date_of_joining"] = doj_str

        doe_str = profile["doe"] or "N/A"
        draw.text((width // 2, y_offset), f"Date of Exit: {doe_str}", font=f_label, fill=text_color)
        full_text_lines.append(f"Date of Exit: {doe_str}")
        if profile["doe"]:
            ground_truth["date_of_exit"] = doe_str

    full_text = "\n".join(full_text_lines)

    # Apply Image Degradations according to condition
    cond_code = condition["code"]

    if cond_code == "clean_scan":
        # Baseline: clean high-res
        pass

    elif cond_code == "photo_shadow":
        # Radial / diagonal shadow overlay
        w, h = img.size
        shadow_arr = np.ones((h, w), dtype=np.float32)
        # Create gradient from top-left (1.05) to bottom-right (0.65)
        for y in range(h):
            for x in range(w):
                dist = math.sqrt((x / w)**2 + (y / h)**2)
                shadow_arr[y, x] = max(0.55, 1.05 - 0.45 * (x / w + y / h) / 2.0)
        
        img_arr = np.array(img, dtype=np.float32)
        for c in range(3):
            img_arr[:, :, c] = np.clip(img_arr[:, :, c] * shadow_arr, 0, 255)
        img = Image.fromarray(img_arr.astype(np.uint8))

    elif cond_code == "skewed_rot":
        # Rotate by +5.5 degrees
        img = img.rotate(5.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))

    elif cond_code == "low_resolution":
        # Downscale 2.5x and upscale
        orig_w, orig_h = img.size
        small = img.resize((orig_w // 3, orig_h // 3), Image.Resampling.BILINEAR)
        img = small.resize((orig_w, orig_h), Image.Resampling.NEAREST)

    elif cond_code == "blur_noise":
        # Gaussian blur + Gaussian noise
        img = img.filter(ImageFilter.GaussianBlur(radius=1.8))
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, 15, arr.shape)
        noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(noisy)

    elif cond_code == "compression":
        # Save as JPEG with Q=28 and reopen
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=28)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")

    elif cond_code == "obscured_crease":
        # Draw translucent smudge / crease across portion of image
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        d_over = ImageDraw.Draw(overlay)
        # Diagonal crease line
        w, h = img.size
        d_over.line([(w * 0.2, h * 0.4), (w * 0.7, h * 0.85)], fill=(120, 110, 100, 160), width=6)
        # Fingerprint / smudge oval
        d_over.ellipse([(w * 0.45, h * 0.5), (w * 0.65, h * 0.7)], fill=(150, 140, 130, 90))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    elif cond_code == "bilingual_script":
        # Already incorporated dual-script headers & names
        pass

    return img, ground_truth, full_text


def generate_all_benchmark_assets():
    """Generates 48 benchmark images (6 categories x 8 conditions) + annotation JSONs."""
    manifest = []
    print("Generating CONVELINA P3H.12 Benchmark Assets (48 samples)...")

    sample_idx = 0
    categories = ["aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"]

    for cat in categories:
        for c_idx, cond in enumerate(CONDITIONS):
            sample_idx += 1
            # Pick a synthetic profile (cycle through profiles 1-6)
            profile = PROFILES[(sample_idx - 1) % len(PROFILES)]
            
            sample_id = f"{cat}_{cond['code']}"
            img_filename = f"{sample_id}.png" if cond["code"] != "compression" else f"{sample_id}.jpg"
            img_path = IMAGES_DIR / img_filename
            ann_path = ANNOTATIONS_DIR / f"{sample_id}.json"

            img, ground_truth_fields, full_text = render_document_card(cat, profile, cond)
            
            # Save Image
            if img_filename.endswith(".jpg"):
                img.save(img_path, format="JPEG", quality=28)
            else:
                img.save(img_path, format="PNG")

            # Save Machine-Readable Ground Truth Annotation
            annotation = {
                "sample_id": sample_id,
                "category": cat,
                "condition": cond["code"],
                "condition_name": cond["name"],
                "condition_description": cond["description"],
                "expected_manual_review": cond["expected_review"],
                "profile_id": profile["id"],
                "image_filename": img_filename,
                "ground_truth_fields": ground_truth_fields,
                "ground_truth_text": full_text,
            }

            with open(ann_path, "w", encoding="utf-8") as f:
                json.dump(annotation, f, indent=2, ensure_ascii=False)

            manifest.append({
                "sample_id": sample_id,
                "category": cat,
                "condition": cond["code"],
                "image_path": str(img_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "annotation_path": str(ann_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "expected_review": cond["expected_review"],
            })

            print(f"  [{sample_idx:02d}/48] Generated {cat.upper()} - {cond['name']} -> {img_filename}")

    manifest_path = BENCHMARK_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSuccessfully generated 48 benchmark images and annotations at {BENCHMARK_DIR}")
    print(f"Manifest saved to {manifest_path}")


if __name__ == "__main__":
    generate_all_benchmark_assets()
