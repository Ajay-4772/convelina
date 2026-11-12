import io
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import pytesseract
import pypdf

from app.config import settings
from app.ocr.preprocessing import default_image_preprocessor, ImagePreprocessor, PreprocessingConfig

logger = logging.getLogger("convelina.ocr")

class BaseOCREngine(ABC):
    """
    Abstract interface for OCR engines allowing future pluggable engines (e.g. TrOCR, PaddleOCR, AWS Textract).
    """
    @abstractmethod
    def extract_text(self, file_path: str, is_pdf: bool = False) -> str:
        pass

    def extract_text_and_confidence(self, file_path: str, is_pdf: bool = False) -> Tuple[str, float]:
        text = self.extract_text(file_path, is_pdf=is_pdf)
        return text, 0.85

class TesseractOCREngine(BaseOCREngine):
    """
    Production-oriented Tesseract OCR engine with image preprocessing, projection deskewing,
    PDF rasterization, and multilingual Tamil/Hindi/English support.
    """
    def __init__(self, languages: str = "eng+hin+tam"):
        self.languages = languages
        self._verify_tesseract_available()

    def _verify_tesseract_available(self):
        try:
            ver = pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully. Version: %s", ver)
        except Exception as e:
            logger.warning("Tesseract binary not found or not in PATH: %s. Fallback modes enabled.", str(e))

    def deskew_image(self, image: Image.Image) -> Image.Image:
        """
        Detects orientation skew using horizontal projection profile variance
        and rotates the image to align text lines horizontally.
        """
        try:
            thumb = image.convert("L")
            thumb.thumbnail((500, 500), Image.Resampling.BILINEAR)
            arr = np.array(thumb)
            thresh = np.mean(arr)
            binary = (arr < thresh).astype(np.float32)

            best_score = -1.0
            best_angle = 0.0
            # Sweep -15 to +15 degrees in 0.5 degree steps
            for angle in np.arange(-15.0, 15.5, 0.5):
                rot = Image.fromarray(binary).rotate(float(angle), resample=Image.Resampling.NEAREST, fillcolor=0)
                proj = np.sum(np.array(rot), axis=1)
                score = np.sum(np.diff(proj)**2)
                if score > best_score:
                    best_score = score
                    best_angle = float(angle)

            if abs(best_angle) >= 0.5:
                logger.info("Deskewing image by correction angle: %.1f deg", best_angle)
                return image.rotate(best_angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))
            return image
        except Exception as e:
            logger.warning("Deskewing failed, proceeding with original orientation: %s", str(e))
            return image

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesses image for optimal OCR extraction using modular ImagePreprocessor:
        - Multi-scale resolution normalization (Lanczos)
        - Coarse/fine projection profile deskewing
        - Pure-NumPy CLAHE contrast equalization
        - Unsharp mask edge sharpening & median despeckling
        """
        try:
            return default_image_preprocessor.preprocess(image)
        except Exception as e:
            logger.warning("Modular image preprocessing failed, using original: %s", str(e))
            return image

    def _extract_from_image(self, image: Image.Image) -> str:
        processed = self.preprocess_image(image)
        for lang_spec in [self.languages, "eng+tam", "eng+hin", "eng"]:
            try:
                text = pytesseract.image_to_string(processed, lang=lang_spec, config="--psm 4")
                if text and text.strip():
                    return text
            except pytesseract.TesseractError:
                continue
        return pytesseract.image_to_string(processed, lang="eng")

    def compute_image_quality_metrics(self, image: Image.Image) -> Dict[str, float]:
        """
        Computes objective image quality metrics to calibrate OCR confidence:
        - Laplacian variance (sharpness / blur detection)
        - Intensity standard deviation (contrast assessment)
        - Resolution adequacy
        """
        return default_image_preprocessor.compute_quality_metrics(image)

    def _extract_from_image_with_confidence(self, image: Image.Image) -> Tuple[str, float]:
        # Compute image quality metrics on raw input image before enhancement
        quality_metrics = self.compute_image_quality_metrics(image)
        quality_penalty = quality_metrics["total_quality_penalty"]

        processed = self.preprocess_image(image)
        data = None
        for lang_spec in [self.languages, "eng+tam", "eng+hin", "eng"]:
            try:
                data = pytesseract.image_to_data(
                    processed,
                    lang=lang_spec,
                    config="--psm 4",
                    output_type=pytesseract.Output.DICT
                )
                break
            except Exception:
                continue

        if not data:
            try:
                data = pytesseract.image_to_data(processed, lang="eng", output_type=pytesseract.Output.DICT)
            except Exception as e:
                logger.warning("pytesseract image_to_data failed: %s, falling back to basic extraction", str(e))
                text = self._extract_from_image(image)
                return text, 0.70

        lines = []
        current_line = []
        last_line_key = None
        confidences = []

        num_items = len(data.get("text", []))
        for i in range(num_items):
            w = str(data["text"][i]).strip()
            c = float(data["conf"][i]) if data.get("conf") else -1.0
            line_key = (data.get("block_num", [0])[i], data.get("par_num", [0])[i], data.get("line_num", [0])[i])

            if line_key != last_line_key and last_line_key is not None:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
            last_line_key = line_key

            if w:
                current_line.append(w)
                if c >= 0:
                    confidences.append(c)

        if current_line:
            lines.append(" ".join(current_line))

        text = "\n".join(lines).strip()
        if not text:
            text = self._extract_from_image(image)

        avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.75
        calibrated_conf = max(0.30, avg_conf - quality_penalty)
        return text, round(calibrated_conf, 4)

    def extract_text_and_confidence(self, file_path: str, is_pdf: bool = False) -> Tuple[str, float]:
        """
        Extracts textual content and computes an overall OCR confidence score (0.0 to 1.0).
        """
        if not is_pdf:
            with Image.open(file_path) as img:
                return self._extract_from_image_with_confidence(img)

        # PDF processing
        extracted_text_chunks: List[str] = []
        try:
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages[: settings.MAX_UPLOAD_PDF_PAGES]:
                t = page.extract_text()
                if t and t.strip():
                    extracted_text_chunks.append(t.strip())

            combined_digital_text = "\n".join(extracted_text_chunks).strip()
            if len(combined_digital_text) > 50:
                logger.info("Extracted direct text from digital PDF (%d chars)", len(combined_digital_text))
                # Dynamic calibrated confidence for digital PDFs based on density and character validity
                printable_chars = sum(1 for c in combined_digital_text if c.isprintable())
                total_chars = max(len(combined_digital_text), 1)
                clean_ratio = printable_chars / total_chars
                has_structure = any(kw in combined_digital_text.lower() for kw in ["name", "date", "number", "certificate", "record", "passbook", "authority", "government"])
                struct_bonus = 0.05 if has_structure else 0.0
                digital_conf = round(min(0.93, max(0.75, 0.84 + 0.05 * clean_ratio + struct_bonus)), 3)
                return combined_digital_text, digital_conf
        except Exception as e:
            logger.warning("Direct PDF text extraction failed: %s", str(e))

        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, first_page=1, last_page=3)
            ocr_chunks = []
            page_confs = []
            for img in images:
                page_text, conf = self._extract_from_image_with_confidence(img)
                if page_text.strip():
                    ocr_chunks.append(page_text.strip())
                    page_confs.append(conf)
            avg_conf = (sum(page_confs) / len(page_confs)) if page_confs else 0.70
            return "\n\n--- Page Break ---\n\n".join(ocr_chunks), round(avg_conf, 4)
        except Exception as e:
            logger.error("PDF rasterization OCR failed: %s", str(e))
            if extracted_text_chunks:
                return "\n".join(extracted_text_chunks), 0.75
            raise RuntimeError(f"OCR extraction failed for PDF: {str(e)}")

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
            for page in reader.pages[: settings.MAX_UPLOAD_PDF_PAGES]:
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
