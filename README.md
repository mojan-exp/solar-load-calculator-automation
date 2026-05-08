# Solar Load Calculator — Electricity Bill to Excel Automation

## Overview
Solar Load Calculator is an AI-powered automation system designed for **Energybae** to streamline the solar system sizing process. It automatically extracts key data from electricity bills (PDF/Images) and populates a specialized Excel template, saving time and reducing manual errors.

## Features
- **Hybrid OCR Pipeline**: Combines direct PDF text extraction with Tesseract OCR for scanned images/PDFs.
- **Automated Data Extraction**: Extracts Consumer Name, Number, Billing Month, Units, Sanction Load, Tariff, and Bill Amount using robust Regex patterns.
- **Excel Automation**: Populates an existing Excel template while preserving formulas and formatting.
- **Streamlit UI**: Simple, user-friendly interface for uploading bills, verifying extracted data, and downloading results.
- **Error Handling**: Gracefully handles corrupted files, OCR failures, and missing fields.

## Tech Stack
- **Language**: Python 3.11+
- **Frontend**: Streamlit
- **OCR**: Pytesseract, OpenCV
- **PDF Processing**: pdfplumber, PyMuPDF (fitz)
- **Excel Automation**: openpyxl
- **Data Handling**: pandas, numpy

## Folder Structure
```text
solar_load_calculator/
│
├── app/
│   ├── main.py          # Streamlit UI & Application Logic
│   ├── extractor.py     # OCR & Data Extraction Logic
│   ├── excel_writer.py  # Excel Template Automation
│   ├── utils.py         # Logging & Path Helpers
│
├── data/
│   ├── sample_bills/    # Place sample bills here (PDF/JPG/PNG)
│   ├── outputs/         # Generated Excel files with timestamps
│   ├── templates/       # Excel template storage
│
├── .env                 # Configuration variables
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd solar_load_calculator
   ```

2. **Install Tesseract OCR**:
   - **Windows**: Download and install from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
   - **Linux**: `sudo apt install tesseract-ocr`
   - **Mac**: `brew install tesseract`

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment**:
   - Create a `.env` file or use the provided one.
   - If Tesseract is not in your system PATH, specify it in the sidebar of the app or in `.env`.

## How to Use

1. **Run the Application**:
   ```bash
   streamlit run app/main.py
   ```
2. **Upload a Bill**: Drag and drop a PDF or Image (JPG/PNG) of an electricity bill.
3. **Extract Data**: Click the "Extract Data" button.
4. **Verify & Edit**: Check the extracted fields. If OCR missed anything, you can manually correct it in the form.
5. **Generate Excel**: Click "Generate Excel File".
6. **Download**: Click the download button to get your filled Excel report.

## Future Improvements
- **LLM Integration**: Use LLMs (like GPT-4o or Gemini Flash) for even more accurate extraction from complex layouts.
- **Batch Processing**: Allow uploading multiple bills at once.
- **Database Integration**: Store extracted data for historical analysis.
- **Mobile Support**: Optimized UI for tablet/mobile bill scanning.

## License
Built for Energybae Internship Assignment.
