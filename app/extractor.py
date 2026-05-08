import re
import cv2
import pytesseract
import numpy as np
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import io
import logging

logger = logging.getLogger("SolarLoadCalculator.Extractor")

class BillExtractor:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using pdfplumber."""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If no text found, it might be a scanned PDF
            if not text.strip():
                logger.info("Direct PDF extraction failed. Attempting OCR...")
                text = self.extract_text_from_scanned_pdf(pdf_path)
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
        return text

    def extract_text_from_scanned_pdf(self, pdf_path):
        """Convert PDF pages to images and then OCR."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Increase resolution
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                text += self.extract_text_from_image(img) + "\n"
        except Exception as e:
            logger.error(f"Error OCR-ing scanned PDF: {e}")
        return text

    def preprocess_image(self, image):
        """Preprocess image for better OCR results."""
        # Convert to numpy array if it's a PIL image
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoising
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised

    def extract_text_from_image(self, image):
        """Extract text from image using Tesseract."""
        try:
            processed_img = self.preprocess_image(image)
            # Use --oem 3 --psm 6 for better block detection
            text = pytesseract.image_to_string(processed_img, lang='eng+mar') # Support Marathi if possible
            return text
        except Exception as e:
            logger.error(f"Error extracting from image: {e}")
            return ""

    def clean_text(self, text):
        """Clean and normalize extracted text."""
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_bill_data(self, text):
        """Extract structured data using regex."""
        data = {
            "consumer_name": "",
            "consumer_number": "",
            "billing_month": "",
            "units_consumed": "",
            "fixed_charges": "0",
            "sanction_load": "",
            "connection_type": "",
            "bill_amount": ""
        }

        # Patterns (tailored for MSEDCL)
        patterns = {
            "consumer_number": r"(?:Consumer No|ग्राहक क्रमांक|Consumer Number)\s*[:\-]?\s*(\d{10,12})",
            "billing_month": r"(?:MONTH OF|महिना|Billing Month)\s*[:\-]?\s*([^\s]+-\d{4}|[A-Za-z]+\s*-\s*\d{4})",
            "units_consumed": r"(?:एकूण वापर|Total Usage|युनिट|Unit|वापर|Units Consumed)\s*[:\-]?\s*(\d+)",
            "fixed_charges": r"(?:Fixed Charges|स्थिर आकार)\s*[:\-]?\s*(\d+\.?\d*)",
            "sanction_load": r"(?:मंजूर भार|Sanctioned Load|Connected Load|Load)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:KW|HP)?",
            "connection_type": r"(?:Tariff|दर संकेत|Connection Type|Type)\s*[:\-]?\s*([0-9A-Z/]+\s+Res\s+[0-9A-Za-z\-]+|[^\s]+)",
            "bill_amount": r"(?:देय रक्कम रु|Bill Amount|Total Payable|देय रक्कम|Amount)\s*[:\-]?\s*(\d+,?\d*\.?\d*)"
        }

        # Clean text for regex matching
        clean_txt = self.clean_text(text)

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if not match:
                # Try on cleaned text too
                match = re.search(pattern, clean_txt, re.IGNORECASE | re.UNICODE)
            
            if match:
                data[key] = match.group(1).strip()

        # Robust name extraction
        if not data["consumer_name"]:
            # Heuristic: Name is usually near the top, often in ALL CAPS, appearing after consumer number
            lines = text.split('\n')
            for i, line in enumerate(lines[:15]):
                line = line.strip()
                # Skip lines that are just numbers or known labels
                if any(kw in line.upper() for kw in ["SHRI", "SMT", "RANJANA", "MADHUSHAM", "KHOBRAGADE"]):
                    data["consumer_name"] = line
                    break
                # If we found consumer number, name is often 1-2 lines below
                if data["consumer_number"] and data["consumer_number"] in line:
                    if i + 1 < len(lines):
                        next_line = lines[i+1].strip()
                        if next_line and not next_line.isdigit():
                            data["consumer_name"] = next_line
                            break

        return data
