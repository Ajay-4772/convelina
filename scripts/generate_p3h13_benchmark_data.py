"""
CONVELINA — P3H.13 Independent Holdout Document Intelligence Benchmark Generator
Creates a reproducible, entirely synthetic holdout benchmark across all six Tier 1 categories:
1. Aadhaar Card
2. PAN Card
3. Passport
4. Class 10 Certificate
5. Class 12 Certificate
6. EPFO/UAN Records

CRITICAL METHODOLOGY REQUIREMENT:
- 100% INDEPENDENT from P3H.12 baseline (new fictional profiles, zero overlap)
- Evaluates real generalization across the 8 physical capture and degradation conditions
- Output folder: `benchmarks/p3h13/`
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

BASE_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = BASE_DIR / "benchmarks" / "p3h13"
IMAGES_DIR = BENCHMARK_DIR / "images"
ANNOTATIONS_DIR = BENCHMARK_DIR / "annotations"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, font_type: str = "sans", script: str = "latin") -> ImageFont.ImageFont:
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


# 6 Fictional Holdout Profiles (Zero overlap with P3H.12)
HOLDOUT_PROFILES = [
    {
        "id": "prof_h1",
        "full_name": "VIKRAMADITYA PRASAD SINGH",
        "name_hindi": "विक्रमादित्य प्रसाद सिंह",
        "name_tamil": "விக்ரமாதித்யா பிரசாத் சிங்",
        "father_name": "RAGHUVIR PRASAD SINGH",
        "mother_name": "KUNTI DEVI SINGH",
        "gender": "Male",
        "dob": "18/07/1987",
        "dob_iso": "1987-07-18",
        "address": "55, Gomti Nagar, Sector 4, Lucknow, Uttar Pradesh",
        "pincode": "226010",
        "aadhaar": "8901 2345 6789",
        "pan": "BNMVS5678P",
        "passport": "L4567890",
        "roll_10": "4512789",
        "reg_10": "UP/2003/4512789",
        "year_10": "2003",
        "roll_12": "6723891",
        "reg_12": "UP/2005/6723891",
        "year_12": "2005",
        "uan": "100812345678",
        "member_id": "UPLUC00123450000067890",
        "establishment": "LUCKNOW AGRO PRODUCTS PRIVATE LIMITED",
        "establishment_id": "UPLUC0012345000",
        "doj": "15/06/2009",
        "doe": "31/03/2016",
    },
    {
        "id": "prof_h2",
        "full_name": "MEENAKSHI SOUNDARARAJAN",
        "name_hindi": "मीनाक्षी सुंदरराजन",
        "name_tamil": "மீனாட்சி சௌந்தரராஜன்",
        "father_name": "K. SOUNDARARAJAN",
        "mother_name": "PADMA SOUNDARARAJAN",
        "gender": "Female",
        "dob": "22/10/1993",
        "dob_iso": "1993-10-22",
        "address": "14, TTK Road, Alwarpet, Chennai, Tamil Nadu",
        "pincode": "600018",
        "aadhaar": "7890 1234 5678",
        "pan": "CVBMS9012Q",
        "passport": "M5678901",
        "roll_10": "5823901",
        "reg_10": "TN/2009/5823901",
        "year_10": "2009",
        "roll_12": "7934012",
        "reg_12": "TN/2011/7934012",
        "year_12": "2011",
        "uan": "100923456789",
        "member_id": "TNMAS00456780000078901",
        "establishment": "CHENNAI PRECISION GEARS PVT LTD",
        "establishment_id": "TNMAS0045678000",
        "doj": "01/12/2015",
        "doe": None,
    },
    {
        "id": "prof_h3",
        "full_name": "HARPREET KAUR GREWAL",
        "name_hindi": "हरप्रीत कौर ग्रेवाल",
        "name_tamil": "ஹர்ப்ரீத் கவுர் க்ரேவால்",
        "father_name": "JASWINDER SINGH GREWAL",
        "mother_name": "AMRIT KAUR GREWAL",
        "gender": "Female",
        "dob": "05/05/1991",
        "dob_iso": "1991-05-05",
        "address": "108, Model Town, Ludhiana, Punjab",
        "pincode": "141002",
        "aadhaar": "6789 0123 4567",
        "pan": "DXPHK3456R",
        "passport": "N6789012",
        "roll_10": "6123450",
        "reg_10": "PB/2007/6123450",
        "year_10": "2007",
        "roll_12": "8234561",
        "reg_12": "PB/2009/8234561",
        "year_12": "2009",
        "uan": "100134567890",
        "member_id": "PBLUD00678900000089012",
        "establishment": "PUNJAB KNITWEAR EXPORTS LIMITED",
        "establishment_id": "PBLUD0067890000",
        "doj": "20/07/2013",
        "doe": "15/01/2021",
    },
    {
        "id": "prof_h4",
        "full_name": "ARJUN DEB CHAUDHURY",
        "name_hindi": "अर्जुन देब चौधरी",
        "name_tamil": "அர்ஜுன் தேப் சவுத்ரி",
        "father_name": "PRANAB KUMAR CHAUDHURY",
        "mother_name": "SHARMILA CHAUDHURY",
        "gender": "Male",
        "dob": "11/12/1986",
        "dob_iso": "1986-12-11",
        "address": "73, Salt Lake City, Sector 2, Kolkata, West Bengal",
        "pincode": "700091",
        "aadhaar": "5678 9012 3456",
        "pan": "EYZAC7890S",
        "passport": "P7890123",
        "roll_10": "3890124",
        "reg_10": "WB/2002/3890124",
        "year_10": "2002",
        "roll_12": "5901235",
        "reg_12": "WB/2004/5901235",
        "year_12": "2004",
        "uan": "100245678901",
        "member_id": "WBCAL00890120000090123",
        "establishment": "KOLKATA INFOTECH SOLUTIONS LLP",
        "establishment_id": "WBCAL0089012000",
        "doj": "01/04/2008",
        "doe": "30/09/2018",
    },
    {
        "id": "prof_h5",
        "full_name": "KAVITA ANAND JOSHI",
        "name_hindi": "कविता आनंद जोशी",
        "name_tamil": "கவிதா ஆனந்த் ஜோஷி",
        "father_name": "ANAND MORESHWAR JOSHI",
        "mother_name": "SADHANA ANAND JOSHI",
        "gender": "Female",
        "dob": "28/08/1995",
        "dob_iso": "1995-08-28",
        "address": "302, Mayur Colony, Kothrud, Pune, Maharashtra",
        "pincode": "411038",
        "aadhaar": "4567 8901 2345",
        "pan": "FZBKP1234T",
        "passport": "R8901234",
        "roll_10": "7345678",
        "reg_10": "MH/2011/7345678",
        "year_10": "2011",
        "roll_12": "9456789",
        "reg_12": "MH/2013/9456789",
        "year_12": "2013",
        "uan": "100356789012",
        "member_id": "MHPUN00123400000012345",
        "establishment": "PUNE AUTOMOTIVE COMPONENT WORKS",
        "establishment_id": "MHPUN0012340000",
        "doj": "10/08/2017",
        "doe": None,
    },
    {
        "id": "prof_h6",
        "full_name": "NAVEEN BALASUBRAMANIAN",
        "name_hindi": "नवीन बालसुब्रमण्यन",
        "name_tamil": "நவீன் பாலசுப்ரமணியன்",
        "father_name": "V. BALASUBRAMANIAN",
        "mother_name": "REVATHI BALASUBRAMANIAN",
        "gender": "Male",
        "dob": "15/01/1989",
        "dob_iso": "1989-01-15",
        "address": "45, 100 Feet Road, Indiranagar, Bengaluru, Karnataka",
        "pincode": "560038",
        "aadhaar": "3456 7890 1234",
        "pan": "GAHNB5678U",
        "passport": "S9012345",
        "roll_10": "6456789",
        "reg_10": "KA/2005/6456789",
        "year_10": "2005",
        "roll_12": "8567890",
        "reg_12": "KA/2007/8567890",
        "year_12": "2007",
        "uan": "100467890123",
        "member_id": "KABAN00345670000023456",
        "establishment": "BENGALURU CLOUD LABS PRIVATE LIMITED",
        "establishment_id": "KABAN0034567000",
        "doj": "01/07/2011",
        "doe": "28/02/2020",
    }
]

CONDITIONS = [
    {"code": "clean_scan", "name": "Clean High-Resolution Scan", "expected_review": False},
    {"code": "photo_shadow", "name": "Photographed Appearance with Shadow", "expected_review": False},
    {"code": "skewed_rot", "name": "Rotated & Skewed Alignment", "expected_review": False},
    {"code": "low_resolution", "name": "Low Resolution Downsampling", "expected_review": True},
    {"code": "blur_noise", "name": "Optical Blur & Sensor Noise", "expected_review": True},
    {"code": "compression", "name": "Heavy JPEG Compression Artifacts", "expected_review": False},
    {"code": "obscured_crease", "name": "Partially Obscured / Paper Crease", "expected_review": True},
    {"code": "bilingual_script", "name": "Bilingual Multi-Script Formatting", "expected_review": False},
]


def render_document_card(category: str, profile: dict, condition: dict) -> Tuple[Image.Image, dict, str]:
    width, height = 1200, 750
    if category == "pan":
        width, height = 1100, 700
    elif category == "passport":
        width, height = 1200, 850
    elif category in ("education_10th", "education_12th"):
        width, height = 1250, 850
    elif category == "epf":
        width, height = 1200, 800

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_type = "serif" if category in ("education_10th", "education_12th") else ("mono" if category == "epf" else "sans")
    is_bilingual = (condition["code"] == "bilingual_script")

    f_title = get_font(24, font_type=font_type)
    f_sub = get_font(14, font_type=font_type)
    f_label = get_font(13, font_type="sans")
    f_val = get_font(16, font_type=font_type)
    f_mono = get_font(16, font_type="mono")

    draw.rectangle([15, 15, width - 15, height - 15], outline=(180, 180, 180), width=3)
    draw.rectangle([25, 25, width - 25, height - 25], outline=(220, 220, 220), width=1)

    gt_fields: Dict[str, Any] = {}
    lines_text: List[str] = ["SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM"]

    if category == "aadhaar":
        draw.text((60, 45), "GOVERNMENT OF INDIA", fill=(20, 20, 20), font=f_title)
        draw.text((60, 80), "Unique Identification Authority of India (Sample)", fill=(80, 80, 80), font=f_sub)
        lines_text.extend(["GOVERNMENT OF INDIA", "Unique Identification Authority of India (Sample)"])

        y = 140
        draw.text((60, y), "Name:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["full_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Name: {profile['full_name']}")
        gt_fields["full_name"] = profile["full_name"]

        if is_bilingual:
            y += 28
            f_indic = get_font(15, script="hindi")
            draw.text((180, y), profile["name_hindi"], fill=(20, 20, 20), font=f_indic)
            lines_text.append(profile["name_hindi"])

        y += 40
        draw.text((60, y), "DOB:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["dob"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"DOB: {profile['dob']}")
        gt_fields["date_of_birth"] = profile["dob_iso"]

        y += 40
        draw.text((60, y), "Gender:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["gender"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Gender: {profile['gender']}")
        gt_fields["gender"] = profile["gender"]

        y += 40
        draw.text((60, y), "Address:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["address"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Address: {profile['address']}")
        gt_fields["address"] = profile["address"]
        gt_fields["pincode"] = profile["pincode"]

        y += 70
        f_num = get_font(28, font_type="mono")
        draw.text((60, y), "Aadhaar Number:", fill=(80, 80, 80), font=f_label)
        draw.text((220, y - 5), profile["aadhaar"], fill=(160, 20, 20), font=f_num)
        lines_text.append(f"Aadhaar Number: {profile['aadhaar']}")
        gt_fields["aadhaar_number"] = profile["aadhaar"]
        gt_fields["document_number"] = profile["aadhaar"]
        gt_fields["issuing_authority"] = "UIDAI"

    elif category == "pan":
        draw.text((50, 40), "INCOME TAX DEPARTMENT", fill=(20, 60, 120), font=f_title)
        draw.text((50, 75), "GOVERNMENT OF INDIA", fill=(80, 80, 80), font=f_sub)
        lines_text.extend(["INCOME TAX DEPARTMENT", "GOVERNMENT OF INDIA"])

        y = 130
        draw.text((50, y), "Name:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["full_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Name: {profile['full_name']}")
        gt_fields["full_name"] = profile["full_name"]

        y += 40
        draw.text((50, y), "Father's Name:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["father_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Father's Name: {profile['father_name']}")
        gt_fields["father_name"] = profile["father_name"]

        y += 40
        draw.text((50, y), "Date of Birth:", fill=(80, 80, 80), font=f_label)
        draw.text((180, y), profile["dob"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Date of Birth: {profile['dob']}")
        gt_fields["date_of_birth"] = profile["dob_iso"]

        y += 60
        f_pan = get_font(26, font_type="mono")
        draw.text((50, y), "Permanent Account Number:", fill=(80, 80, 80), font=f_label)
        draw.text((320, y - 5), profile["pan"], fill=(160, 20, 20), font=f_pan)
        lines_text.append(f"PAN: {profile['pan']}")
        gt_fields["pan_number"] = profile["pan"]
        gt_fields["document_number"] = profile["pan"]
        gt_fields["issuing_authority"] = "Income Tax Department"

    elif category == "passport":
        draw.text((60, 40), "PASSPORT — REPUBLIC OF INDIA", fill=(20, 40, 90), font=f_title)
        draw.text((60, 75), "Ministry of External Affairs (Specimen)", fill=(80, 80, 80), font=f_sub)
        lines_text.extend(["PASSPORT — REPUBLIC OF INDIA", "Ministry of External Affairs"])

        y = 125
        name_parts = profile["full_name"].split()
        surname = name_parts[-1]
        given_name = " ".join(name_parts[:-1])

        draw.text((60, y), "Type / Country Code:", fill=(80, 80, 80), font=f_label)
        draw.text((250, y), "P / IND", fill=(20, 20, 20), font=f_val)
        draw.text((500, y), "Passport No:", fill=(80, 80, 80), font=f_label)
        draw.text((640, y), profile["passport"], fill=(160, 20, 20), font=f_mono)
        lines_text.append(f"Passport No: {profile['passport']}")
        gt_fields["passport_number"] = profile["passport"]
        gt_fields["document_number"] = profile["passport"]
        gt_fields["issuing_authority"] = "Ministry of External Affairs"

        y += 35
        draw.text((60, y), "Surname:", fill=(80, 80, 80), font=f_label)
        draw.text((250, y), surname, fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Surname: {surname}")
        gt_fields["surname"] = surname

        y += 35
        draw.text((60, y), "Given Name(s):", fill=(80, 80, 80), font=f_label)
        draw.text((250, y), given_name, fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Given Name: {given_name}")
        gt_fields["full_name"] = profile["full_name"]

        y += 35
        draw.text((60, y), "Nationality:", fill=(80, 80, 80), font=f_label)
        draw.text((250, y), "INDIAN", fill=(20, 20, 20), font=f_val)
        draw.text((500, y), "Sex:", fill=(80, 80, 80), font=f_label)
        draw.text((640, y), "M" if profile["gender"] == "Male" else "F", fill=(20, 20, 20), font=f_val)
        gt_fields["gender"] = profile["gender"]

        y += 35
        draw.text((60, y), "Date of Birth:", fill=(80, 80, 80), font=f_label)
        draw.text((250, y), profile["dob"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"DOB: {profile['dob']}")
        gt_fields["date_of_birth"] = profile["dob_iso"]

        y += 35
        draw.text((60, y), "Date of Issue:", fill=(80, 80, 80), font=f_label)
        draw.text((250, y), "10/05/2018", fill=(20, 20, 20), font=f_val)
        draw.text((500, y), "Date of Expiry:", fill=(80, 80, 80), font=f_label)
        draw.text((640, y), "09/05/2028", fill=(20, 20, 20), font=f_val)
        gt_fields["date_of_issue"] = "2018-05-10"
        gt_fields["expiry_date"] = "2028-05-09"

        # MRZ Lines (ICAO Doc 9303 Type 3)
        y = height - 120
        draw.line([(40, y - 10), (width - 40, y - 10)], fill=(200, 200, 200), width=1)
        f_mrz = get_font(18, font_type="mono")

        # Format MRZ Line 1: P<IND[SURNAME]<<[GIVEN_NAME]...
        clean_s = surname.upper().replace(" ", "")
        clean_g = given_name.upper().replace(" ", "<")
        name_mrz = f"{clean_s}<<{clean_g}"
        mrz1 = f"P<IND{name_mrz}".ljust(44, "<")[:44]

        # Format MRZ Line 2: [PASSPORT_NO][CHK]IND[DOB][CHK][SEX][EXPIRY][CHK]...
        dob_digits = profile["dob_iso"].replace("-", "")[2:]  # YYMMDD
        exp_digits = "280509"
        sex_mrz = "M" if profile["gender"] == "Male" else "F"
        p_no = profile["passport"]
        mrz2 = f"{p_no}0IND{dob_digits}0{sex_mrz}{exp_digits}0<<<<<<<<<<<<<<<00"[:44]

        draw.text((50, y), mrz1, fill=(10, 10, 10), font=f_mrz)
        draw.text((50, y + 30), mrz2, fill=(10, 10, 10), font=f_mrz)
        lines_text.extend([mrz1, mrz2])

    elif category in ("education_10th", "education_12th"):
        tier = "CLASS X" if category == "education_10th" else "CLASS XII"
        tier_full = "SECONDARY SCHOOL" if category == "education_10th" else "SENIOR SCHOOL CERTIFICATE"
        year = profile["year_10"] if category == "education_10th" else profile["year_12"]
        roll = profile["roll_10"] if category == "education_10th" else profile["roll_12"]
        reg = profile["reg_10"] if category == "education_10th" else profile["reg_12"]

        draw.text((60, 40), "CENTRAL BOARD OF SECONDARY EDUCATION", fill=(120, 40, 30), font=f_title)
        draw.text((60, 75), f"{tier_full} EXAMINATION ({tier}) — {year}", fill=(80, 80, 80), font=f_sub)
        lines_text.extend(["CENTRAL BOARD OF SECONDARY EDUCATION", f"{tier_full} EXAMINATION ({tier})"])
        gt_fields["board"] = "CBSE"
        gt_fields["issuing_authority"] = "CBSE"
        gt_fields["passing_year"] = year

        y = 135
        draw.text((60, y), "Roll No:", fill=(80, 80, 80), font=f_label)
        draw.text((200, y), roll, fill=(20, 20, 20), font=f_mono)
        draw.text((450, y), "Registration No:", fill=(80, 80, 80), font=f_label)
        draw.text((620, y), reg, fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Roll No: {roll}")
        lines_text.append(f"Registration No: {reg}")
        gt_fields["roll_number"] = roll
        gt_fields["registration_number"] = reg
        gt_fields["document_number"] = roll

        y += 40
        draw.text((60, y), "Candidate Name:", fill=(80, 80, 80), font=f_label)
        draw.text((200, y), profile["full_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Candidate Name: {profile['full_name']}")
        gt_fields["full_name"] = profile["full_name"]

        y += 40
        draw.text((60, y), "Father's Name:", fill=(80, 80, 80), font=f_label)
        draw.text((200, y), profile["father_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Father's Name: {profile['father_name']}")
        gt_fields["father_name"] = profile["father_name"]
        gt_fields["parent_guardian_name"] = profile["father_name"]

        y += 40
        draw.text((60, y), "Mother's Name:", fill=(80, 80, 80), font=f_label)
        draw.text((200, y), profile["mother_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Mother's Name: {profile['mother_name']}")
        gt_fields["mother_name"] = profile["mother_name"]

        y += 40
        draw.text((60, y), "Date of Birth:", fill=(80, 80, 80), font=f_label)
        draw.text((200, y), profile["dob"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Date of Birth: {profile['dob']}")
        gt_fields["date_of_birth"] = profile["dob_iso"]

    elif category == "epf":
        draw.text((60, 40), "EMPLOYEES' PROVIDENT FUND ORGANISATION, INDIA", fill=(20, 100, 60), font=f_title)
        draw.text((60, 75), "MEMBER PASSBOOK & REGISTRATION PARTICULARS", fill=(80, 80, 80), font=f_sub)
        lines_text.extend(["EMPLOYEES' PROVIDENT FUND ORGANISATION, INDIA", "MEMBER PASSBOOK & REGISTRATION PARTICULARS"])
        gt_fields["issuing_authority"] = "EPFO"

        y = 135
        draw.text((60, y), "Universal Account Number (UAN):", fill=(80, 80, 80), font=f_label)
        draw.text((360, y - 2), profile["uan"], fill=(160, 20, 20), font=f_mono)
        lines_text.append(f"Universal Account Number (UAN): {profile['uan']}")
        gt_fields["uan"] = profile["uan"]
        gt_fields["document_number"] = profile["uan"]

        y += 40
        draw.text((60, y), "Member ID:", fill=(80, 80, 80), font=f_label)
        draw.text((360, y), profile["member_id"], fill=(20, 20, 20), font=f_mono)
        lines_text.append(f"Member ID: {profile['member_id']}")
        gt_fields["member_id"] = profile["member_id"]

        y += 40
        draw.text((60, y), "Member Name:", fill=(80, 80, 80), font=f_label)
        draw.text((360, y), profile["full_name"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Member Name: {profile['full_name']}")
        gt_fields["full_name"] = profile["full_name"]

        y += 40
        draw.text((60, y), "Establishment:", fill=(80, 80, 80), font=f_label)
        draw.text((360, y), profile["establishment"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Establishment: {profile['establishment']}")
        gt_fields["employer_name"] = profile["establishment"]
        gt_fields["establishment_id"] = profile["establishment_id"]

        y += 40
        draw.text((60, y), "Date of Joining:", fill=(80, 80, 80), font=f_label)
        draw.text((360, y), profile["doj"], fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Date of Joining: {profile['doj']}")
        gt_fields["date_of_joining"] = profile["doj"]

        y += 40
        doe_val = profile["doe"] if profile["doe"] else "N/A"
        draw.text((60, y), "Date of Exit:", fill=(80, 80, 80), font=f_label)
        draw.text((360, y), doe_val, fill=(20, 20, 20), font=f_val)
        lines_text.append(f"Date of Exit: {doe_val}")
        if profile["doe"]:
            gt_fields["date_of_exit"] = profile["doe"]

    # Apply physical variations according to condition
    cond_code = condition["code"]

    if cond_code == "clean_scan":
        pass  # Baseline clean scan

    elif cond_code == "photo_shadow":
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        y_grad = np.linspace(0.82, 1.05, h)[:, None, None]
        x_grad = np.linspace(0.85, 1.08, w)[None, :, None]
        arr = np.clip(arr * (y_grad * x_grad), 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    elif cond_code == "skewed_rot":
        img = img.rotate(5.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))

    elif cond_code == "low_resolution":
        w_orig, h_orig = img.size
        small = img.resize((480, int(480 * h_orig / w_orig)), Image.Resampling.BILINEAR)
        img = small.resize((w_orig, h_orig), Image.Resampling.NEAREST)

    elif cond_code == "blur_noise":
        img = img.filter(ImageFilter.GaussianBlur(radius=1.8))
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, 10, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    elif cond_code == "compression":
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=28)
        buf.seek(0)
        img = Image.open(buf)

    elif cond_code == "obscured_crease":
        d = ImageDraw.Draw(img)
        w, h = img.size
        d.line([(w // 4, 0), (w // 4 + 30, h)], fill=(120, 120, 120), width=4)
        d.line([(0, h // 2), (w, h // 2 + 20)], fill=(150, 150, 150), width=3)

    elif cond_code == "bilingual_script":
        pass

    full_text = "\n".join(lines_text)
    return img, gt_fields, full_text


def generate_all():
    print("Generating P3H.13 Independent Holdout Benchmark Data (48 samples)...")
    manifest = []
    
    categories = ["aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"]

    for cat_idx, cat in enumerate(categories):
        profile = HOLDOUT_PROFILES[cat_idx % len(HOLDOUT_PROFILES)]
        for cond_idx, cond in enumerate(CONDITIONS):
            sample_id = f"{cat}_{cond['code']}"
            ext = ".jpg" if cond["code"] == "compression" else ".png"
            img_rel_path = f"benchmarks/p3h13/images/{sample_id}{ext}"
            ann_rel_path = f"benchmarks/p3h13/annotations/{sample_id}.json"

            img, gt_fields, full_text = render_document_card(cat, profile, cond)

            img_full_path = BASE_DIR / img_rel_path
            ann_full_path = BASE_DIR / ann_rel_path

            if ext == ".jpg":
                img.convert("RGB").save(str(img_full_path), format="JPEG", quality=28)
            else:
                img.save(str(img_full_path), format="PNG")

            annotation_data = {
                "sample_id": sample_id,
                "category": cat,
                "condition": cond["code"],
                "condition_name": cond["name"],
                "expected_manual_review": cond["expected_review"],
                "profile_id": profile["id"],
                "image_filename": f"{sample_id}{ext}",
                "ground_truth_fields": gt_fields,
                "ground_truth_text": full_text,
            }

            with open(ann_full_path, "w", encoding="utf-8") as f:
                json.dump(annotation_data, f, indent=2, ensure_ascii=False)

            manifest_entry = {
                "sample_id": sample_id,
                "category": cat,
                "condition": cond["code"],
                "expected_review": cond["expected_review"],
                "profile_id": profile["id"],
                "image_path": img_rel_path,
                "annotation_path": ann_rel_path,
            }
            manifest.append(manifest_entry)
            print(f"  Generated {sample_id:<32} -> {img_rel_path}")

    manifest_path = BENCHMARK_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nP3H.13 Holdout Benchmark generation complete: {len(manifest)} samples written to {BENCHMARK_DIR}")


if __name__ == "__main__":
    generate_all()

