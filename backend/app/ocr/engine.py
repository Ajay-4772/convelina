import io
import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pypdf

logger = logging.getLogger("convelina.ocr")

class BaseOCREngine(ABC):
    """
    Abstract interface for OCR engines allowing future pluggable engines (e.g. TrOCR, PaddleOCR, AWS Textract).
    """
    @abstractmethod
    def extract_text(self, file_path: str, is_pdf: bool = False) -> str:
        pass

class TesseractOCREngine(BaseOCREngine):
    """
    Production-oriented Tesseract OCR engine with image preprocessing and PDF rasterization.
    """
    def __init__(self, languages: str = "eng+hin"):
        self.languages = languages
        self._verify_tesseract_available()

    def _verify_tesseract_available(self):
        try:
            ver = pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully. Version: %s", ver)
        except Exception as e:
            logger.warning("Tesseract binary not found or not in PATH: %s. Fallback modes enabled.", str(e))

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesses image for optimal OCR extraction:
        - Upscales small scans/images to optimal OCR resolution.
        - Converts to grayscale, enhances contrast, and applies light sharpening.
        """
        try:
            # 1. Upscale if image is smaller than optimal OCR resolution (~1500px)
            if image.width < 1200 or image.height < 800:
                scale = min(3.0, max(1.5, 1600.0 / max(image.width, 1)))
                new_dim = (int(image.width * scale), int(image.height * scale))
                image = image.resize(new_dim, Image.Resampling.LANCZOS)

            # 2. Convert to Grayscale
            gray = image.convert("L")
            # 3. Enhance Contrast
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.8)
            # 4. Apply subtle sharpening filter
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            return sharpened
        except Exception as e:
            logger.warning("Image preprocessing failed, using original: %s", str(e))
            return image


    def _extract_from_image(self, image: Image.Image) -> str:
        processed = self.preprocess_image(image)
        try:
            text = pytesseract.image_to_string(processed, lang=self.languages)
        except pytesseract.TesseractError:
            # Fall back to English if Hindi language pack is missing in current environment
            text = pytesseract.image_to_string(processed, lang="eng")
        return text

    def extract_text(self, file_path: str, is_pdf: bool = False) -> str:
        """
        Extracts all textual content from the document.
        For PDFs, first attempts fast digital text extraction via pypdf;
        if insufficient, rasterizes pages using pdf2image and runs OCR.
        """
        if not is_pdf:
            with Image.open(file_path) as img:
                return self._extract_from_image(img)

        # PDF processing
        extracted_text_chunks: List[str] = []
        try:
            # Step 1: Direct text extraction from digital PDF
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    extracted_text_chunks.append(t.strip())
            
            combined_digital_text = "\n".join(extracted_text_chunks).strip()
            # If digital extraction yielded substantial text (>50 chars), return it
            if len(combined_digital_text) > 50:
                logger.info("Extracted direct text from digital PDF (%d chars)", len(combined_digital_text))
                return combined_digital_text
        except Exception as e:
            logger.warning("Direct PDF text extraction failed or incomplete: %s", str(e))

        # Step 2: Rasterize PDF pages to images and run Tesseract
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, first_page=1, last_page=3) # Process up to 3 pages for identity docs
            ocr_chunks = []
            for idx, img in enumerate(images):
                page_text = self._extract_from_image(img)
                if page_text.strip():
                    ocr_chunks.append(page_text.strip())
            return "\n\n--- Page Break ---\n\n".join(ocr_chunks)
        except Exception as e:
            logger.error("PDF rasterization OCR failed: %s", str(e))
            # If direct text extraction had anything, return it
            if extracted_text_chunks:
                return "\n".join(extracted_text_chunks)
            raise RuntimeError(f"OCR extraction failed for PDF: {str(e)}")

# Singleton default instance
default_ocr_engine = TesseractOCREngine()
