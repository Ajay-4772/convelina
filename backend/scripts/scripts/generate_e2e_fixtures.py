import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "e2e", "temp_fixtures"))
os.makedirs(FIXTURES_DIR, exist_ok=True)

# 1. valid_rejection.pdf
pdf_path_1 = os.path.join(FIXTURES_DIR, "valid_rejection.pdf")
c = canvas.Canvas(pdf_path_1, pagesize=letter)
c.drawString(50, 750, "GOVERNMENT OF INDIA - REGIONAL PASSPORT OFFICE")
c.drawString(50, 725, "REJECTION NOTICE / DEFICIENCY MEMO: REF #882910")
c.drawString(50, 700, "Reason: Discrepancy detected in applicant name between records.")
c.drawString(50, 675, "Name on Passport Application differs from submitted Aadhaar card.")
c.drawString(50, 650, "Date of Notice: 15-08-2024")
c.save()

# 2. valid_doc_2.pdf
pdf_path_2 = os.path.join(FIXTURES_DIR, "valid_doc_2.pdf")
c = canvas.Canvas(pdf_path_2, pagesize=letter)
c.drawString(50, 750, "EMPLOYEES PROVIDENT FUND ORGANISATION (EPFO)")
c.drawString(50, 725, "JOINT DECLARATION REJECTION MEMO #EPF-JD-2024")
c.drawString(50, 700, "Reason: Father name mismatch between UAN profile and Member Aadhaar.")
c.drawString(50, 675, "Date of Rejection: 22-09-2024")
c.save()

# 3. empty_document.pdf
empty_pdf_path = os.path.join(FIXTURES_DIR, "empty_document.pdf")
c = canvas.Canvas(empty_pdf_path, pagesize=letter)
c.save()

# 4. valid_document.png
png_path = os.path.join(FIXTURES_DIR, "valid_document.png")
img = Image.new("RGB", (400, 200), color=(255, 255, 255))
draw = ImageDraw.Draw(img)
draw.text((20, 20), "PASSPORT SEVA KENDRA - DEFICIENCY MEMO", fill=(0, 0, 0))
draw.text((20, 50), "Reason for rejection: Spelling discrepancy in applicant name", fill=(0, 0, 0))
draw.text((20, 80), "Date of notice: 10/11/2023", fill=(0, 0, 0))
img.save(png_path, format="PNG")

# 5. low_confidence.png (Tiny 30x30 grey noise block)
low_conf_path = os.path.join(FIXTURES_DIR, "low_confidence.png")
tiny_img = Image.new("RGB", (40, 30), color=(180, 180, 180))
tiny_img.save(low_conf_path, format="PNG")

# 6. invalid_extension.txt
txt_path = os.path.join(FIXTURES_DIR, "invalid_extension.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("This is a plain text file which should be rejected by the attachment upload validator.")

print(f"Generated 6 test fixtures in {FIXTURES_DIR}")

