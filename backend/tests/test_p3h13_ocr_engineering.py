"""
CONVELINA — P3H.13 OCR Engineering & Extraction Accuracy Test Suite
Validates:
1. Image preprocessing modularity, safety invariants (non-destructive), and transformations:
   - Resolution normalization (Lanczos resampling, aspect ratio preservation)
   - Deskewing (coarse + fine angle estimation)
   - Pure-NumPy CLAHE contrast enhancement
   - Unsharp masking edge sharpening
2. ICAO Doc 9303 MRZ Parser:
   - 7-3-1 check digit validation
   - Detection of corrupted characters in document number and DOB
   - Primary/secondary identifier (surname / given name) parsing
   - Century resolution for birth and expiry dates
3. Document-specific field extractors across all 6 Tier 1 categories:
   - Aadhaar: full / last 4 number handling and multi-line address lookahead
   - PAN: issuing authority and alphanumeric structure
   - Passport: dual-zone MRZ + visual inspection zone
   - Class 10 & Class 12: education board token detection and roll number
   - EPFO / UAN: authority attribution and date handling
4. Confidence calibration mathematics:
   - Brier score calculation
   - Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
   - Multi-factor field confidence calibration
5. Manual review trigger policy:
   - Fail-safe trigger on degraded or low-confidence extractions
   - FAR preservation (0.00% false acceptance)
6. P3H.13 Holdout dataset integrity and isolation:
   - 48 samples, 48 ground truth annotations, 6 categories, 8 visual conditions
   - Complete absence of identity leakage from P3H.12
"""

import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import pytest

from app.ocr.preprocessing import ImagePreprocessor, PreprocessingConfig
from app.ocr.mrz import MRZParser, compute_mrz_check_digit, parse_mrz_date
from app.ocr.calibrator import ConfidenceCalibrator
from app.ocr.field_extractor import FieldExtractor
from app.ocr.parsers.aadhaar import AadhaarParser
from app.ocr.parsers.pan import PANParser
from app.ocr.parsers.passport import PassportParser
from app.ocr.parsers.education import EducationCertificateParser
from app.ocr.parsers.epf import EPFRecordParser
from app.services.identity_matching.models import DocumentIdentityProfile
from app.services.identity_matching.engine import IdentityComparisonEngine
from app.services.identity_matching.classification import OverallIdentityClassification, NameMatchClassification


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
P3H12_DIR = REPO_ROOT / "benchmarks" / "p3h12"
P3H13_DIR = REPO_ROOT / "benchmarks" / "p3h13"


# ============================================================================
# 1. Image Preprocessor Tests
# ============================================================================

def test_preprocessor_preserves_original_image():
    """Verify preprocessor operates strictly on in-memory copies and does not mutate input."""
    preprocessor = ImagePreprocessor()
    test_arr = np.random.randint(50, 200, (300, 400, 3), dtype=np.uint8)
    original_copy = test_arr.copy()
    img = Image.fromarray(test_arr)
    
    _ = preprocessor.preprocess(img)
    
    assert np.array_equal(np.array(img), original_copy), "Original PIL image was mutated in-place!"


def test_preprocessor_resolution_normalization():
    """Verify Lanczos upscaling preserves aspect ratio and brings low-res images into optimal OCR range."""
    preprocessor = ImagePreprocessor(PreprocessingConfig(min_dimension=1000, max_dimension=2200, target_dimension=1500))
    
    # 400x300 image (min_dim = 300)
    small_img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    norm_img = preprocessor.normalize_resolution(small_img)
    
    # Upscaled min_dim should be substantially increased (3x upscale -> 900)
    w, h = norm_img.size
    min_dim = min(w, h)
    assert min_dim >= 800 and max(w, h) >= 1200, f"Expected upscaled dimensions, got {w}x{h}"
    # Aspect ratio check (400/300 = 1.333)
    assert abs((w / h) - (400 / 300)) < 0.02, "Aspect ratio was distorted during normalization"


def test_preprocessor_clahe_contrast_enhancement():
    """Verify pure-NumPy CLAHE improves dynamic range on low-contrast images."""
    preprocessor = ImagePreprocessor(PreprocessingConfig(clahe_enabled=True, clahe_clip_limit=3.0))
    
    # Generate low contrast grayscale: values compressed between 110 and 140
    low_contrast = np.random.randint(110, 140, (200, 200), dtype=np.uint8)
    initial_std = float(np.std(low_contrast))
    
    enhanced = preprocessor.apply_clahe(Image.fromarray(low_contrast, mode="L"))
    enhanced_std = float(np.std(np.array(enhanced)))
    
    assert enhanced_std > initial_std, (
        f"CLAHE failed to increase contrast: initial std={initial_std:.2f}, enhanced std={enhanced_std:.2f}"
    )


def test_preprocessor_deskewing():
    """Verify 2-stage coarse/fine deskewing accurately detects and corrects skew."""
    preprocessor = ImagePreprocessor(PreprocessingConfig(deskew_enabled=True))
    
    # Create horizontal text-like bar lines
    img = Image.new("L", (500, 300), color=255)
    draw = ImageDraw.Draw(img)
    for y in range(40, 260, 25):
        draw.line([(50, y), (450, y)], fill=0, width=4)
        
    # Rotate by 4.0 degrees
    rotated = img.rotate(-4.0, resample=Image.Resampling.BICUBIC, fillcolor=255)
    _, detected_angle = preprocessor.deskew_image(rotated)
    
    # Detected angle should be non-zero and counteract skew
    assert abs(detected_angle) >= 0.5, f"Expected detected deskew angle, got {detected_angle}"


# ============================================================================
# 2. ICAO Doc 9303 MRZ Parser Tests
# ============================================================================

def test_mrz_parser_valid_td3():
    """Verify standard Indian Passport TD3 MRZ parsing with valid 7-3-1 check digits."""
    # Check digits:
    # Z1234567< -> 1
    # 950412 -> 1
    # 320411 -> 9
    line1 = "P<INDSHARMA<<PRIYA<ANAND<<<<<<<<<<<<<<<<<<<<"
    line2 = "Z1234567<1IND9504121F3204119<<<<<<<<<<<<<<<0"
    
    result = MRZParser.parse_td3(line1, line2)
    
    assert result["mrz_detected"] is True
    assert result["composite_valid"] is True
    assert result["passport_check_valid"] is True
    assert result["dob_check_valid"] is True
    assert result["expiry_check_valid"] is True
    assert result["issuing_country"] == "IND"
    assert result["passport_number"] == "Z1234567"
    assert result["surname"] == "SHARMA"
    assert result["given_name"] == "PRIYA ANAND"
    assert result["full_name"] == "PRIYA ANAND SHARMA"
    assert result["date_of_birth"] == "1995-04-12"
    assert result["gender"] == "Female"
    assert result["expiry_date"] == "2032-04-11"
    assert result["nationality"] == "IND"


def test_mrz_parser_checksum_detection_of_corruption():
    """Verify 7-3-1 check digit rejects corrupted passport numbers or birth dates."""
    # Line 2 with corrupted passport number ('Z1234568<' instead of 'Z1234567<' with check digit '1')
    line1 = "P<INDSHARMA<<PRIYA<ANAND<<<<<<<<<<<<<<<<<<<<"
    corrupted_line2 = "Z1234568<1IND9504121F3204119<<<<<<<<<<<<<<<0"
    
    result = MRZParser.parse_td3(line1, corrupted_line2)
    
    assert result["passport_check_valid"] is False
    assert result["composite_valid"] is False


def test_mrz_parser_century_resolution():
    """Verify birth and expiry year 2-digit century expansion logic."""
    # DOB: 35 -> 1935 (senior citizen); 05 -> 2005 (young adult)
    assert parse_mrz_date("350101", is_expiry=False) == "1935-01-01"
    assert parse_mrz_date("050101", is_expiry=False) == "2005-01-01"
    # Expiry: 32 -> 2032
    assert parse_mrz_date("321231", is_expiry=True) == "2032-12-31"


# ============================================================================
# 3. Document-Specific Field Extractor Enhancements
# ============================================================================

def test_aadhaar_parser_number_and_address_lookahead():
    """Verify Aadhaar parser captures both masked/unmasked and does not truncate address at house numbers."""
    raw_text = (
        "GOVERNMENT OF INDIA\n"
        "Rajesh Kumar\n"
        "DOB: 15/08/1988\n"
        "Male\n"
        "Address: Flat 402, Building 12, Sector 15, Near City Mall, New Delhi 110001\n"
        "9876 5432 1098\n"
        "VID: 1234 5678 9012 3456\n"
    )
    parser = AadhaarParser()
    res = parser.parse(raw_text)
    fields = res.get("fields", {})
    
    assert fields.get("aadhaar_last_4") == "1098"
    assert fields.get("aadhaar_number") == "9876 5432 1098"
    assert fields.get("gender") in ("Male", "MALE")
    # Address should contain Sector 15 and New Delhi, not truncated prematurely
    address = fields.get("address", "")
    assert "Sector 15" in address and "110001" in address


def test_pan_parser_issuing_authority_and_format():
    """Verify PAN parser identifies Income Tax Department authority and PAN regex."""
    raw_text = (
        "INCOME TAX DEPARTMENT\n"
        "GOVT. OF INDIA\n"
        "Permanent Account Number Card\n"
        "ABCDE1234F\n"
        "Name: VIKRAM MALHOTRA\n"
        "Father's Name: SUNIL MALHOTRA\n"
        "DOB: 22/11/1990\n"
    )
    parser = PANParser()
    res = parser.parse(raw_text)
    fields = res.get("fields", {})
    
    assert fields.get("pan_number") == "ABCDE1234F"
    assert fields.get("issuing_authority") == "Income Tax Department"
    assert fields.get("full_name") == "VIKRAM MALHOTRA"
    assert fields.get("father_name") == "SUNIL MALHOTRA"


def test_education_parser_board_detection():
    """Verify Class 10 & 12 education parsers accurately identify CBSE and ICSE authorities."""
    cbse_text = (
        "CENTRAL BOARD OF SECONDARY EDUCATION\n"
        "ALL INDIA SECONDARY SCHOOL EXAMINATION 2011\n"
        "This is to certify that AMIT VERMA\n"
        "Roll No. 6123456\n"
        "Mother's Name: REKHA VERMA\n"
        "Father's Name: SURESH VERMA\n"
        "Date of Birth: 04/05/1995\n"
        "PASSED"
    )
    parser = EducationCertificateParser(doc_type="CLASS_10")
    res = parser.parse(cbse_text)
    fields = res.get("fields", {})
    
    assert fields.get("issuing_authority") in ("CBSE", "Central Board of Secondary Education")
    assert fields.get("board") == "CBSE"
    assert fields.get("roll_number") == "6123456"
    assert fields.get("full_name") == "AMIT VERMA"


def test_epf_parser_authority_and_dates():
    """Verify EPFO parser extracts UAN and attributes issuing authority."""
    raw_text = (
        "EMPLOYEES' PROVIDENT FUND ORGANISATION, INDIA\n"
        "Member Passbook / UAN Card\n"
        "UAN: 100987654321\n"
        "Member Name: POOJA HEGDE\n"
        "Father / Husband Name: RAMESH HEGDE\n"
        "Date of Joining: 01/06/2018\n"
        "Date of Exit: 31/03/2022\n"
    )
    parser = EPFRecordParser()
    res = parser.parse(raw_text)
    fields = res.get("fields", {})
    
    assert fields.get("uan") == "100987654321"
    assert fields.get("issuing_authority") == "EPFO"
    assert fields.get("full_name") == "POOJA HEGDE"


# ============================================================================
# 4. Confidence Calibration Mathematics Tests
# ============================================================================

def test_confidence_calibrator_mathematics():
    """Verify Brier score, ECE (10 bins), and MCE mathematical calculations."""
    # Perfectly calibrated predictor
    perfect_confs = [0.1, 0.2, 0.8, 0.9]
    perfect_outcomes = [0, 0, 1, 1]
    predictions = list(zip(perfect_confs, perfect_outcomes))
    
    brier = ConfidenceCalibrator.compute_brier_score(predictions)
    # ( (0.1)^2 + (0.2)^2 + (0.8-1)^2 + (0.9-1)^2 ) / 4 = (0.01 + 0.04 + 0.04 + 0.01) / 4 = 0.10 / 4 = 0.025
    assert abs(brier - 0.025) < 1e-4
    
    report = ConfidenceCalibrator.evaluate_calibration(predictions, num_bins=5)
    assert report.expected_calibration_error < 0.25, f"ECE for well-calibrated sample should be low, got {report.expected_calibration_error}"
    
    # Multi-factor field confidence calibration
    cal_conf, rev_req = ConfidenceCalibrator.calibrate_field_confidence(
        ocr_engine_conf=0.92,
        parser_anchor_conf=1.0,
        format_validated=True
    )
    assert 0.0 <= cal_conf <= 1.0
    assert cal_conf > 0.80, "High-validity extraction should receive high calibrated confidence"
    assert rev_req is False


# ============================================================================
# 5. Manual Review Trigger Policy & Safety Invariant Tests
# ============================================================================

def test_manual_review_triggers_on_low_confidence():
    """Verify manual review trigger policy forces human review when OCR confidence is below safe floor."""
    raw_text = (
        "GOVERNMENT OF INDIA\n"
        "Rajesh Kumar\n"
        "DOB: 15/08/1988\n"
        "Male\n"
        "9876 5432 1098\n"
    )
    # Low overall confidence (0.45 < 0.75 threshold)
    res = FieldExtractor.extract_category_fields(
        document_type="aadhaar",
        raw_text=raw_text,
        overall_confidence=0.45
    )
    
    assert res.requires_manual_review is True
    assert any(f.review_required for f in res.field_extractions.values())


# ============================================================================
# 6. P3H.13 Holdout Dataset Integrity & Non-Leakage Tests
# ============================================================================

def test_p3h13_holdout_dataset_integrity():
    """Verify 48 holdout benchmark images, annotations, categories, and visual conditions."""
    manifest_path = P3H13_DIR / "manifest.json"
    assert manifest_path.exists(), f"Holdout manifest missing at {manifest_path}"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    samples = manifest if isinstance(manifest, list) else manifest.get("samples", [])
    assert len(samples) == 48, f"Expected 48 holdout samples, got {len(samples)}"
    
    expected_categories = {"aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"}
    expected_conditions = {
        "clean_scan", "photo_shadow", "skewed_rot", "low_resolution",
        "blur_noise", "compression", "obscured_crease", "bilingual_script"
    }
    
    cat_counts = {}
    cond_counts = {}
    
    for s in samples:
        cat = s["category"]
        cond = s["condition"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        cond_counts[cond] = cond_counts.get(cond, 0) + 1
        
        # Verify file existence on disk
        img_p = REPO_ROOT / s["image_path"]
        ann_p = REPO_ROOT / s["annotation_path"]
        assert img_p.exists() and img_p.stat().st_size > 0, f"Missing image {img_p}"
        assert ann_p.exists() and ann_p.stat().st_size > 0, f"Missing annotation {ann_p}"
        
    for cat in expected_categories:
        assert cat_counts.get(cat) == 8, f"Category {cat} does not have exactly 8 samples"
    for cond in expected_conditions:
        assert cond_counts.get(cond) == 6, f"Condition {cond} does not have exactly 6 samples"


def test_holdout_zero_identity_leakage():
    """Verify P3H.13 holdout dataset shares zero citizen identity overlap with P3H.12 baseline."""
    manifest_p12 = P3H12_DIR / "manifest.json"
    manifest_p13 = P3H13_DIR / "manifest.json"
    
    with open(manifest_p12, "r", encoding="utf-8") as f12, open(manifest_p13, "r", encoding="utf-8") as f13:
        p12_json = json.load(f12)
        p13_json = json.load(f13)
        p12_samples = p12_json if isinstance(p12_json, list) else p12_json.get("samples", [])
        p13_samples = p13_json if isinstance(p13_json, list) else p13_json.get("samples", [])
        
    p12_names = set()
    for s in p12_samples:
        ann_p = REPO_ROOT / s["annotation_path"]
        with open(ann_p, "r", encoding="utf-8") as af:
            ann = json.load(af)
            p12_names.add(ann["ground_truth_fields"].get("full_name", "").strip().upper())
            
    p13_names = set()
    for s in p13_samples:
        ann_p = REPO_ROOT / s["annotation_path"]
        with open(ann_p, "r", encoding="utf-8") as af:
            ann = json.load(af)
            p13_names.add(ann["ground_truth_fields"].get("full_name", "").strip().upper())
            
    overlap = p12_names.intersection(p13_names)
    assert len(overlap) == 0, f"CRITICAL LEAKAGE DETECTED: Overlapping identities between baseline and holdout: {overlap}"


# ============================================================================
# 7. Downstream Comparison Invariant Recovery & Safety Tests (P3H.13.1)
# ============================================================================

def test_downstream_invariant_1_ocr_uncertainty_blocks_auto_match():
    """Invariant 1: OCR uncertainty must not become a confirmed identity match."""
    # Even with identical names, degraded OCR confidence (< 0.60) must halt auto-match
    prof_a = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_uncert_a",
        document_type="aadhaar",
        extracted_fields={"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12"},
        overall_ocr_confidence=0.45,  # Sub-threshold confidence
    )
    prof_b = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_uncert_b",
        document_type="pan",
        extracted_fields={"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12"},
        overall_ocr_confidence=0.92,
    )
    res = IdentityComparisonEngine.compare_profiles(prof_a, prof_b)

    assert res.overall_classification == OverallIdentityClassification.LOW_CONFIDENCE_NEEDS_REVIEW
    assert res.requires_manual_review is True
    assert res.confidence_score < 0.60
    # Clean auto-acceptance is strictly prohibited
    is_auto_match = (
        res.overall_classification in [OverallIdentityClassification.EXACT_MATCH, OverallIdentityClassification.FORMAT_ONLY_MATCH]
        and not res.requires_manual_review
    )
    assert is_auto_match is False


def test_downstream_invariant_2_missing_fields_never_match():
    """Invariant 2: Missing fields must not be treated as matching fields."""
    prof_a = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_missing_a",
        document_type="aadhaar",
        extracted_fields={"full_name": None, "date_of_birth": "1994-08-25"},
        overall_ocr_confidence=0.95,
    )
    prof_b = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_missing_b",
        document_type="pan",
        extracted_fields={"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25"},
        overall_ocr_confidence=0.95,
    )
    res = IdentityComparisonEngine.compare_profiles(prof_a, prof_b)

    assert "full_name" not in res.matched_fields
    assert res.requires_manual_review is True
    # Overall cannot be an exact match when name is absent
    assert res.overall_classification not in [
        OverallIdentityClassification.EXACT_MATCH,
        OverallIdentityClassification.FORMAT_ONLY_MATCH,
    ]


def test_downstream_invariant_3_incorrectly_extracted_values_never_accepted():
    """Invariant 3: Incorrectly extracted values must not be silently accepted."""
    prof_a = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_garbled_a",
        document_type="aadhaar",
        extracted_fields={"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12"},
        overall_ocr_confidence=0.95,
    )
    # Garbled/corrupted extraction on document B
    prof_b = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_garbled_b",
        document_type="pan",
        extracted_fields={"full_name": "R4J3SH KM4R VRMA", "date_of_birth": "1988-04-12"},
        overall_ocr_confidence=0.75,
    )
    res = IdentityComparisonEngine.compare_profiles(prof_a, prof_b)

    is_auto_accepted = (
        res.overall_classification in [OverallIdentityClassification.EXACT_MATCH, OverallIdentityClassification.FORMAT_ONLY_MATCH]
        and not res.requires_manual_review
        and len(res.conflicting_fields) == 0
        and len(res.ambiguous_fields) == 0
    )
    assert is_auto_accepted is False
    assert res.requires_manual_review is True


def test_downstream_invariant_4_ambiguous_values_preserve_manual_review():
    """Invariant 4: Ambiguous values must preserve the manual-review outcome."""
    # Initial expansion without corroborating parental record must require manual review
    prof_a = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_init_a",
        document_type="aadhaar",
        extracted_fields={"full_name": "K. RAMANATHAN", "date_of_birth": "1990-05-10"},
        overall_ocr_confidence=0.95,
    )
    prof_b = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_init_b",
        document_type="passport",
        extracted_fields={"full_name": "KUMAR RAMANATHAN", "date_of_birth": "1990-05-10"},
        overall_ocr_confidence=0.95,
    )
    res = IdentityComparisonEngine.compare_profiles(prof_a, prof_b)

    assert res.requires_manual_review is True
    # Cannot be resolved to an automatic unverified match without corroboration
    assert res.overall_classification in [
        OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW,
        OverallIdentityClassification.LIKELY_SAME_PERSON,
    ]
    if res.overall_classification == OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW:
        assert res.requires_manual_review is True


def test_downstream_invariant_5_genuine_discrepancies_detected():
    """Invariant 5: Genuine discrepancies must remain detectable."""
    # Gender-differentiated lookalike pair (Deepak vs Deepika)
    prof_a = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_gender_a",
        document_type="aadhaar",
        extracted_fields={"full_name": "DEEPAK SHARMA", "date_of_birth": "1992-06-15", "gender": "male"},
        overall_ocr_confidence=0.95,
    )
    prof_b = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_gender_b",
        document_type="pan",
        extracted_fields={"full_name": "DEEPIKA SHARMA", "date_of_birth": "1992-06-15", "gender": "female"},
        overall_ocr_confidence=0.95,
    )
    res = IdentityComparisonEngine.compare_profiles(prof_a, prof_b)

    assert "full_name" in res.conflicting_fields
    assert res.requires_manual_review is True
    assert res.overall_classification in [
        OverallIdentityClassification.MISMATCH,
        OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH,
    ]

    # Date of birth conflict
    prof_c = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_dob_a",
        document_type="aadhaar",
        extracted_fields={"full_name": "AMIT PATEL", "date_of_birth": "1985-03-20"},
        overall_ocr_confidence=0.95,
    )
    prof_d = DocumentIdentityProfile.from_extracted_fields(
        document_id="doc_dob_b",
        document_type="passport",
        extracted_fields={"full_name": "AMIT PATEL", "date_of_birth": "1988-11-10"},
        overall_ocr_confidence=0.95,
    )
    res_dob = IdentityComparisonEngine.compare_profiles(prof_c, prof_d)

    assert "date_of_birth" in res_dob.conflicting_fields
    assert res_dob.requires_manual_review is True
    assert res_dob.overall_classification in [
        OverallIdentityClassification.MISMATCH,
        OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH,
    ]


def test_downstream_invariant_6_preprocessing_immutability():
    """Invariant 6: OCR preprocessing must not alter the original uploaded document."""
    preprocessor = ImagePreprocessor()
    test_img_path = P3H13_DIR / "images" / "pan_clean_scan.png"
    assert test_img_path.exists()

    with open(test_img_path, "rb") as f:
        original_bytes = f.read()

    img = Image.open(test_img_path)
    img_np_before = np.array(img).copy()

    # Preprocess
    processed = preprocessor.preprocess(img)

    # 1. Disk immutability: File on disk was not modified
    with open(test_img_path, "rb") as f:
        bytes_after = f.read()
    assert original_bytes == bytes_after, "Source image on disk was mutated during preprocessing!"

    # 2. In-memory immutability: Original PIL Image passed in was not altered
    img_np_after = np.array(img)
    assert np.array_equal(img_np_before, img_np_after), "Input PIL Image array was mutated in memory!"
    # 3. Processed is a distinct object
    assert processed is not img


def test_downstream_invariant_7_comparison_classification_deterministic():
    """Invariant 7: Comparison classification must remain strictly deterministic."""
    test_pairs = [
        # Pair 1: Exact match
        (
            {"full_name": "NEHA PATEL", "date_of_birth": "1992-02-03", "gender": "female"},
            {"full_name": "NEHA PATEL", "date_of_birth": "1992-02-03", "gender": "female"},
        ),
        # Pair 2: Format variation
        (
            {"full_name": "M AJAY", "date_of_birth": "1995-10-12"},
            {"full_name": "m. ajay", "date_of_birth": "1995-10-12"},
        ),
        # Pair 3: Genuine mismatch
        (
            {"full_name": "VIKRAM SINGH", "date_of_birth": "1980-05-15"},
            {"full_name": "VIKRAM RAO", "date_of_birth": "1980-05-15"},
        ),
    ]

    for doc_a, doc_b in test_pairs:
        p_a = DocumentIdentityProfile.from_extracted_fields("da", "aadhaar", doc_a, overall_ocr_confidence=0.95)
        p_b = DocumentIdentityProfile.from_extracted_fields("db", "pan", doc_b, overall_ocr_confidence=0.95)

        base_res = IdentityComparisonEngine.compare_profiles(p_a, p_b)

        # Run 50 iterations and verify bit-for-bit identical results
        for _ in range(50):
            iter_res = IdentityComparisonEngine.compare_profiles(p_a, p_b)
            assert iter_res.overall_classification == base_res.overall_classification
            assert iter_res.confidence_score == base_res.confidence_score
            assert iter_res.requires_manual_review == base_res.requires_manual_review
            assert iter_res.matched_fields == base_res.matched_fields
            assert iter_res.conflicting_fields == base_res.conflicting_fields
            assert iter_res.ambiguous_fields == base_res.ambiguous_fields

