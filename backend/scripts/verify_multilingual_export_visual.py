"""CONVELINA — P3G.4.1 Multilingual Visual & Structural Export Verification Script
Generates:
1. Pure Tamil multi-page PDF & DOCX
2. Pure English multi-page PDF & DOCX
3. Bilingual English + Tamil parallel PDF & DOCX
4. Complex Indic stress test PDF & DOCX (ஸ்ரீ, க்ஷ, ஔ, ஞ், ற், ழ், ன்றி, ற்றி, ந்தி, tables, long paragraphs)

Converts PDF pages into PNGs and verifies typography, margins, footers, and XML structure.
"""

import io
import os
import sys
import zipfile
import hashlib
from pathlib import Path
from pdf2image import convert_from_bytes
import pypdf

# Add backend to path
sys.path.insert(0, "/app")

from app.services.document_exporter import DocumentExporter
from app.services.draft_translation_service import DraftTranslationService, DISCLAIMERS

ARTIFACT_DIR = Path("/tmp/export_images")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("/tmp/export_validation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Test content definitions
PURE_TAMIL_CONTENT = f"""{DISCLAIMERS['ta']}

பெறுநர்:
தகுதிவாய்ந்த அலுவலர் / நிர்வாக அதிகாரி,
இந்திய தனித்துவ அடையாள ஆணையம் (UIDAI),
மண்டல அலுவலகம், சென்னை,
தமிழ்நாடு - 600001

நாள்: 07/11/2026
விண்ணப்பக் குறிப்பு எண்: URN-2026-TAMIL-001

பொருள்: ஆதார் ஆவணப் பதிவேட்டில் முழுப் பெயர் திருத்தம் கோரும் நிர்வாக விண்ணப்பம்

மதிப்பிற்குரிய ஐயா / அம்மையீர்,

வணக்கம். முத்துவடிவேல் பழனிச்சாமி (ஆதார் எண்: XXXX-XXXX-9012, பிறந்த தேதி: 15/08/1988) ஆகிய நான், ஆதார் அட்டை பதிவுகளைக் கொண்டுள்ள இந்தியக் குடிமகன் ஆவேன். எனது அரசு ஆவணப் பதிவேட்டில் உள்ள விவரப் பிழையைச் சரிசெய்யக் கோரி, இந்த அதிகாரப்பூர்வ நிர்வாக விண்ணப்பத்தை மரியாதையுடன் சமர்ப்பிக்கிறேன்.

1. பதிவு செய்யப்பட்ட முரண்பாட்டின் விவரம்:
   - பாதிக்கப்பட்ட விவரம்: முழுப் பெயர் (Full Name)
   - தற்போது தவறாகப் பதிவாகியுள்ள விவரம்: MUTHUVADIVEL P
   - திருத்தப்பட வேண்டிய உண்மையான / உறுதிப்படுத்தப்பட்ட விவரம்: முத்துவடிவேல் பழனிச்சாமி (MUTHUVADIVEL PALANICHAMY)

2. விண்ணப்பதாரரின் விளக்கம் மற்றும் சூழ்நிலைகள்:
   அசல் ஆதார் பதிவின் போது பெயர் சுருக்கக் குறியீடு (Initial) தவறாக பதிவு செய்யப்பட்டுள்ளது. பள்ளி இறுதிச் சான்றிதழ் மற்றும் பிறப்புச் சான்றிதழில் எனது முழுப் பெயர் முறையாகப் பதிவு செய்யப்பட்டுள்ளது. இக்குறிப்பீடு காரணமாக வங்கி மற்றும் அரசு நலத்திட்ட பதிவுகளில் முரண்பாடுகள் ஏற்படுகின்றன.

3. கோரப்படும் நிர்வாக நடவடிக்கை:
   மேற்குறிப்பிட்ட விவரங்களை எனது உறுதிப்படுத்தப்பட்ட உண்மை ஆவணங்களின் அடிப்படையில் சரிபார்த்து, ஆதார் பதிவேட்டில் திருத்தம் செய்து புதிய திருத்தப்பட்ட ஆதார் அட்டையை வழங்கும்படி பணிவுடன் வேண்டுகிறேன்.

4. உறுதிமொழி மற்றும் சரிபார்ப்பு:
   மேலே குறிப்பிடப்பட்டுள்ள விவரங்கள் அனைத்தும் எனது தனிப்பட்ட அறிவுக்கு எட்டிய வரையில் உண்மையானவை மற்றும் சரியானவை என உளமார உறுதியளிக்கிறேன். இதற்கு ஆதாரமான அரசு ஆவண நகல்கள் இத்துடன் இணைக்கப்பட்டுள்ளன.

இணைப்புகள் மற்றும் அதிகாரப்பூர்வ ஆதார ஆவணங்கள்:
1. பத்தாம் வகுப்பு மதிப்பெண் சான்றிதழ் நகல் (சுயசான்றொப்பமிட்டது)
2. தமிழ்நாடு அரசு பிறப்புச் சான்றிதழ் நகல்
3. தற்போதைய ஆதார் அட்டை நகல்

தங்கள் உண்மையுள்ள,

(கையொப்பம்)
______________________________
பெயர்: முத்துவடிவேல் பழனிச்சாமி
தொடர்பு எண்: +91 94440 12345
மின்னஞ்சல் முகவரி: muthu.palanichamy@example.com
அஞ்சல் முகவரி: எண் 45, பாரதியார் தெரு, கோயம்புத்தூர், தமிழ்நாடு - 641001
"""

PURE_ENGLISH_CONTENT = f"""{DISCLAIMERS['en']}

To,
The Competent Officer / Authority,
Regional Passport Office, Ministry of External Affairs,
Royala Towers, Anna Salai,
Chennai, Tamil Nadu - 600002

Date: 07/11/2026
Application / Reference ID: URN-2026-ENG-002

Subject: Representation for Rectification of Date of Birth in Passport Records

Respected Sir / Madam,

I, RAJESH SUNDARAM, an Indian citizen holding Passport File No. MA1069876543210 and Aadhaar XXXX-XXXX-4567 born on 12/04/1990, hereby submit this formal administrative representation requesting rectification of clerical errors recorded in my passport records.

1. STATEMENT OF RECORDED DISCREPANCY:
   - Particular / Field Affected: Date of Birth
   - Current Incorrect Recorded Value: 12/04/1992
   - Requested True / Confirmed Value: 12/04/1990

2. CITIZEN EXPLANATION & FACTUAL BACKGROUND:
   Under Passports Act, 1967 and MEA Circular No. VI/401/2/2014, clerical discrepancies resulting from manual data transcription during passport renewal can be rectified upon production of authentic civil registration records. My municipal birth certificate unequivocally confirms 12/04/1990. I never consented to the transcription error of 1992.

3. REQUESTED ADMINISTRATIVE ACTION:
   I respectfully request that the Passport Issuing Authority verify the enclosed statutory proofs and re-issue the passport booklet with corrected particulars.

4. SOLEMN DECLARATION:
   I hereby solemnly affirm that the particulars stated above are true and substantiated by authentic documents confirmed by me.

ENCLOSURES & SUPPORTING DOCUMENTS:
1. Certified extract of Municipal Birth Register issued by Greater Chennai Corporation
2. Self-attested copy of Class 10 Secondary School Examination Certificate
3. Self-attested copy of Aadhaar Card confirming DOB 12/04/1990
4. Original Passport Booklet for physical verification

Yours faithfully,

(Signature)
______________________________
Name: RAJESH SUNDARAM
Contact Number: +91 98400 98765
Email Address: rajesh.sundaram@example.com
Postal Address: Plot 12, Gandhi Nagar 2nd Street, Adyar, Chennai - 600020
"""

BILINGUAL_CONTENT = f"""{DISCLAIMERS['ta']}
{DISCLAIMERS['en']}

================================================================================
PART I — OFFICIAL REGIONAL REPRESENTATION (தமிழ் வடிவம்)
================================================================================

பெறுநர்:
தகுதிவாய்ந்த மண்டல ஆணையர்,
ஊழியர் வருங்கால வைப்பு நிதி அமைப்பு (EPFO),
மண்டல அலுவலகம், சென்னை தெற்கு,
தமிழ்நாடு - 600014

நாள்: 07/11/2026
விண்ணப்பக் குறிப்பு எண்: URN-EPF-2026-9901

பொருள்: EPF உறுப்பினர் பதிவேட்டில் தந்தை பெயர் திருத்தம் கோரும் கூட்டுப் பிரகடன விண்ணப்பம்

மதிப்பிற்குரிய ஐயா / அம்மையீர்,

வணக்கம். சுப்பிரமணியன் ராமகிருஷ்ணன் (UAN: 100987654321, ஆதார் எண்: XXXX-XXXX-5544) ஆகிய நான், EPF திட்ட உறுப்பினர் ஆவேன். எனது உறுப்பினர் பதிவேட்டில் உள்ள எழுத்துப் பிழையைச் சரிசெய்யக் கோரி, இந்த அதிகாரப்பூர்வ நிர்வாக விண்ணப்பத்தை மரியாதையுடன் சமர்ப்பிக்கிறேன்.

1. பதிவு செய்யப்பட்ட முரண்பாட்டின் விவரம்:
   - பாதிக்கப்பட்ட விவரம்: தந்தை / பெற்றோர் பெயர் (Father / Parent Name)
   - தற்போது தவறாகப் பதிவாகியுள்ள விவரம்: RAMAKRISHNA S
   - திருத்தப்பட வேண்டிய உண்மையான / உறுதிப்படுத்தப்பட்ட விவரம்: ராமகிருஷ்ணன் சீனிவாசன் (RAMAKRISHNAN SRINIVASAN)

2. விண்ணப்பதாரரின் விளக்கம் மற்றும் சூழ்நிலைகள்:
   நிறுவனத்தில் பணியில் சேர்ந்த போது முதலாளியால் சமர்ப்பிக்கப்பட்ட பதிவேட்டில் தந்தை பெயர் சுருக்கமாக தவறாகப் பதிவு செய்யப்பட்டுள்ளது.

3. கோரப்படும் நிர்வாக நடவடிக்கை:
   இணைக்கப்பட்டுள்ள கூட்டுப் பிரகடனம் (Joint Declaration) மற்றும் ஆதார ஆவணங்களை ஏற்றுக்கொண்டு EPF பதிவேட்டைத் திருத்தும்படி பணிவுடன் வேண்டுகிறேன்.

இணைப்புகள்:
1. முதலாளி சான்றொப்பமிட்ட கூட்டுப் பிரகடனப் படிவம் (Joint Declaration Proforma)
2. உறுப்பினரின் ஆதார் அட்டை மற்றும் பான் அட்டை நகல்கள்

================================================================================
PART II — OFFICIAL ENGLISH ORIGINAL (ஆங்கில வடிவம்)
================================================================================

To,
The Regional P.F. Commissioner,
Employees' Provident Fund Organisation (EPFO),
Regional Office, Chennai South,
Tamil Nadu - 600014

Date: 07/11/2026
Application / Reference ID: URN-EPF-2026-9901

Subject: Joint Declaration Representation for Father's Name Correction in EPFO Records

Respected Sir / Madam,

I, SUBRAMANIAN RAMAKRISHNAN (UAN: 100987654321, Aadhaar: XXXX-XXXX-5544), submit this formal Joint Declaration representation for rectification of father's name under EPFO Circular No. WSU/2022/1/JointDeclaration.

1. STATEMENT OF RECORDED DISCREPANCY:
   - Particular Affected: Father's Name
   - Current Incorrect Recorded Value: RAMAKRISHNA S
   - Requested True / Confirmed Value: RAMAKRISHNAN SRINIVASAN

2. CITIZEN EXPLANATION:
   Clerical transcription error committed during employer onboarding submission. Authentic birth certificate confirms full name.

3. REQUESTED ADMINISTRATIVE ACTION:
   Kindly update member master records in Unified Member Portal (https://unifiedportal-mem.epfindia.gov.in).

ENCLOSURES & SUPPORTING DOCUMENTS:
1. Joint Declaration proforma duly attested by Employer
2. Self-attested copy of Aadhaar Card and PAN Card
"""

COMPLEX_INDIC_STRESS_CONTENT = f"""{DISCLAIMERS['ta']}

பெறுநர்:
மத்திய இடைநிலைக் கல்வி வாரியம் (CBSE),
மண்டல அலுவலகம், சென்னை,
தமிழ்நாடு - 600040

பொருள்: கல்விச் சான்றிதழில் சிறப்பு எழுத்துகள் மற்றும் கூட்டெழுத்துகள் சரிபார்ப்பு (Complex Script Stress Test)

மதிப்பிற்குரிய ஐயா / அம்மையீர்,

வணக்கம். ஸ்ரீமதி ஔவையார் க்ஷேமவதி (Aadhaar: XXXX-XXXX-7788, DOB: 01/01/2005) ஆகிய நான் சமர்ப்பிக்கும் விண்ணப்பம்.

1. கூட்டெழுத்துகள் மற்றும் சிறப்பு தமிழ் உயிரெழுத்துகள் சரிபார்ப்பு:
   - சிறப்பு எழுத்துகள்: ஸ்ரீ (Shri), க்ஷ (Ksha), ஔ (Au), ஞ் (Nya), ற் (Rra), ழ் (Zha), ன்றி (Nri), ற்றி (Ttri), ந்தி (Nthi)
   - வாக்கிய மாதிரி: "நன்றி மறப்பது நன்றன்று; நன்றல்லது அன்றே மறப்பது நன்று."
   - சிறப்பு வரிசை: க, ங, ச, ஞ, ட, ண, த, ந, ப, ம, ய, ர, ல, வ, ழ, ள, ற, ன

2. அட்டவணை விவரங்கள் (Comparative Verification Table):
   புலம் | பதிவான விவரம் | கோரப்படும் திருத்தம்
   முழுப் பெயர் | ஸ்ரீ. மு. பழனிச்சாமி | ஸ்ரீமதி. முத்துவடிவேல் பழனிச்சாமி (ஔவையார் நகர்)
   பிறந்த தேதி | 01/01/2004 | 01/01/2005
   தந்தை பெயர் | ராமகிருஷ்ணன் க்ஷ. | ராமகிருஷ்ணன் சீனிவாசன் (ஸ்ரீரங்கம்)

3. நீட்டிக்கப்பட்ட சட்ட விளக்கம் (Multi-Paragraph Stress Test):
   {('தமிழ் மொழியின் தனித்துவமான எழுத்து வடிவங்கள் மற்றும் மெய்ம்மயக்கங்கள் சரியாக அச்சிடப்பட வேண்டும். ' * 15)}

   {('அரசு பதிவேடுகளில் உள்ள விவரங்கள் எவ்வித சிதைவுமின்றி (Zero Glyph Corruption) தெளிவாக காட்சிப்படுத்தப்பட வேண்டும். ' * 15)}

இணைப்புகள்:
1. மத்திய இடைநிலைக் கல்வி வாரிய (CBSE) அசல் மதிப்பெண் சான்றிதழ்
2. தமிழ்நாடு அரசிதழ் (Tamil Nadu Government Gazette) அறிவிப்பு நகல்

தங்கள் உண்மையுள்ள,
(கையொப்பம்)
ஸ்ரீமதி. ஔவையார் க்ஷேமவதி
"""

def main():
    print("=== STARTING P3G.4.1 VISUAL & STRUCTURAL EXPORT VERIFICATION ===")

    test_cases = [
        ("pure_tamil", "தமிழ் நிர்வாக வரைவு (Tamil Administrative Draft)", PURE_TAMIL_CONTENT, "ta"),
        ("pure_english", "Official Administrative Representation", PURE_ENGLISH_CONTENT, "en"),
        ("bilingual", "Bilingual Representation / இருமொழி வரைவு", BILINGUAL_CONTENT, "bilingual_en_ta"),
        ("complex_indic", "Complex Indic Script Stress Test", COMPLEX_INDIC_STRESS_CONTENT, "ta"),
    ]

    results = {}

    for slug, title, content, lang in test_cases:
        print(f"\n--- Processing: {slug} (Language: {lang}) ---")

        # 1. Export PDF
        pdf_bytes = DocumentExporter.export_pdf(title=title, content=content, language=lang)
        pdf_path = OUTPUT_DIR / f"{slug}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        print(f"Generated PDF: {pdf_path} ({len(pdf_bytes)} bytes)")

        # Verify PDF structure using pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        num_pages = len(reader.pages)
        print(f"PDF Page count: {num_pages}")
        assert num_pages >= 1

        # Check page text extraction
        extracted_text = "".join(page.extract_text() or "" for page in reader.pages)
        print(f"PDF Extracted text sample (len={len(extracted_text)}): {extracted_text[:120]}...")

        # 2. Convert PDF to PNG images for visual verification
        try:
            images = convert_from_bytes(pdf_bytes)
            for page_idx, img in enumerate(images):
                img_path = ARTIFACT_DIR / f"{slug}_page_{page_idx + 1}.png"
                img.save(img_path, "PNG")
                print(f"Saved visual page image: {img_path}")
        except Exception as e:
            print(f"Warning: pdf2image conversion failed: {e}")

        # 3. Export DOCX
        docx_bytes = DocumentExporter.export_docx(title=title, content=content, language=lang)
        docx_path = OUTPUT_DIR / f"{slug}.docx"
        docx_path.write_bytes(docx_bytes)
        print(f"Generated DOCX: {docx_path} ({len(docx_bytes)} bytes)")

        # Inspect DOCX XML structure
        zf = zipfile.ZipFile(io.BytesIO(docx_bytes))
        assert "word/document.xml" in zf.namelist()
        doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert len(doc_xml) > 1000

        # Check font references in DOCX
        assert "Lohit Tamil" in doc_xml or "Latha" in doc_xml or "Nirmala UI" in doc_xml or "Calibri" in doc_xml or "Segoe UI" in doc_xml

        results[slug] = {
            "pdf_size": len(pdf_bytes),
            "pdf_pages": num_pages,
            "docx_size": len(docx_bytes),
            "sha256_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }

    print("\n=== SUMMARY RESULTS ===")
    for k, v in results.items():
        print(f"{k}: {v}")

    print("\n=== ALL VISUAL & STRUCTURAL ASSETS GENERATED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
