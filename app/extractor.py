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
            "consumer_number": r"(?:Consumer No|ग्राहक क्रमांक)\s*[:\-]?\s*(\d{12})",
            "consumer_name": r"(?:SHRI|SMT|MR|MRS)\s+([A-Z\s]+?)(?=\s+NO|\s+NI|\s+SHIWAJI|\s+214|$)", # Heuristic for name
            "billing_month": r"(?:MONTH OF|महिना)\s*[:\-]?\s*([A-Za-z\-]+\d{2,4}|[^\s]+-\d{4})",
            "units_consumed": r"(?:एकूण वापर|Total Usage|Usage|Unit)\s*[:\-]?\s*(\d+)",
            "fixed_charges": r"(?:Fixed Charges|स्थिर आकार)\s*[:\-]?\s*(\d+\.?\d*)",
            "sanction_load": r"(?:मंजूर भार|Sanctioned Load|Connected Load)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:KW|HP)?",
            "connection_type": r"(?:Tariff|दर संकेत|Connection Type)\s*[:\-]?\s*([^\s,]+)",
            "bill_amount": r"(?:देय रक्कम रु|Bill Amount|Total Payable)\s*[:\-]?\s*(\d+\.?\d*)"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if match:
                data[key] = match.group(1).strip()

        # Fallback for name if first pattern fails
        if not data["consumer_name"]:
            # Often the name is on the 2nd or 3rd line of the bill
            lines = text.split('\n')
            for line in lines[:10]:
                if any(kw in line.upper() for kw in ["SHRI", "SMT", "MR", "MRS", "RANJANA", "MADHUSHAM"]):
                    data["consumer_name"] = line.strip()
                    break

        return data
