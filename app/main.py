import streamlit as st
import os
import sys
import pandas as pd
import tempfile
from PIL import Image

# Fix for Streamlit Cloud imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractor import BillExtractor
from excel_writer import ExcelWriter
from utils import logger, ensure_directories, get_timestamp

# Page configuration
st.set_page_config(
    page_title="Solar Load Calculator Automation",
    page_icon="☀️",
    layout="wide"
)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'output_file' not in st.session_state:
    st.session_state.output_file = None

def main():
    ensure_directories()
    
    st.title("☀️ Solar Load Calculator Automation")
    st.markdown("""
    Automatically extract data from electricity bills (PDF/Image) and generate solar load calculation Excel files.
    *Built for Energybae AI Internship Assignment.*
    """)
    
    # Move settings to expander for cleaner UI
    with st.expander("⚙️ Advanced Settings"):
        tesseract_path = st.text_input("Tesseract Path (Leave blank for default)", value="")
        template_path = st.text_input("Template Path", value="data/templates/template.xlsx")
        solar_watt = st.number_input("Solar Panel Watt (C7)", value=3000, step=100)
        
        if st.session_state.extracted_data and 'raw_text' in st.session_state:
            st.text_area("Raw Extracted Text (Debug)", value=st.session_state.raw_text, height=200)

    # File uploader
    uploaded_file = st.file_uploader("Upload Electricity Bill (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"])

    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
        st.write(file_details)
        
        # Preview image if it's an image
        if uploaded_file.type.startswith('image'):
            img = Image.open(uploaded_file)
            st.image(img, caption="Uploaded Bill Preview", width=400)
        
        if st.button("Extract Data"):
            with st.spinner("Processing bill..."):
                extractor = BillExtractor(tesseract_path if tesseract_path else None)
                
                # Save uploaded file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    if uploaded_file.type == "application/pdf":
                        text = extractor.extract_text_from_pdf(tmp_path)
                    else:
                        text = extractor.extract_text_from_image(Image.open(tmp_path))
                    
                    data = extractor.extract_bill_data(text)
                    st.session_state.extracted_data = data
                    st.session_state.raw_text = text # Store for debug
                    st.success("Data extraction complete!")
                except Exception as e:
                    st.error(f"Error during extraction: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

    # Display and Edit Extracted Data
    if st.session_state.extracted_data:
        st.subheader("Extracted Data Preview")
        st.info("You can verify and edit the data before generating the Excel file.")
        
        # Create form for editing
        with st.form("data_edit_form"):
            col1, col2 = st.columns(2)
            
            d = st.session_state.extracted_data
            
            updated_data = {}
            with col1:
                updated_data["consumer_name"] = st.text_input("Consumer Name", d.get("consumer_name", ""))
                updated_data["consumer_number"] = st.text_input("Consumer Number", d.get("consumer_number", ""))
                updated_data["billing_month"] = st.text_input("Billing Month", d.get("billing_month", ""))
                updated_data["connection_type"] = st.text_input("Connection Type", d.get("connection_type", ""))
            
            with col2:
                updated_data["units_consumed"] = st.text_input("Units Consumed", d.get("units_consumed", ""))
                updated_data["bill_amount"] = st.text_input("Bill Amount", d.get("bill_amount", ""))
                updated_data["fixed_charges"] = st.text_input("Fixed Charges", d.get("fixed_charges", ""))
                updated_data["sanction_load"] = st.text_input("Sanction Load", d.get("sanction_load", ""))
            
            is_second_meter = st.checkbox("Is this for Second Meter? (Columns H & I)")
            
            submit = st.form_submit_button("Generate Excel File")
            
            if submit:
                with st.spinner("Generating Excel..."):
                    try:
                        # Ensure template exists
                        if not os.path.exists(template_path):
                            # Try fallback to data/outputs if it was moved there
                            fallback_path = r"data/outputs/Reference Copy of Pranay HOME E-Bill Analysis.xlsx"
                            if os.path.exists(fallback_path):
                                template_path = fallback_path
                            else:
                                st.error(f"Template file found at {template_path}. Please check the path in sidebar.")
                                st.stop()

                        writer = ExcelWriter(template_path)
                        output_filename = f"Solar_Load_{get_timestamp()}.xlsx"
                        output_path = os.path.join("data/outputs", output_filename)
                        
                        success = writer.fill_template(updated_data, output_path, is_second_meter=is_second_meter)
                        
                        if success:
                            # Also update solar watt
                            import openpyxl
                            wb = openpyxl.load_workbook(output_path)
                            sheet = wb.active
                            sheet['C7'] = solar_watt
                            wb.save(output_path)
                            
                            st.session_state.output_file = output_path
                            st.success(f"Successfully generated: {output_filename}")
                        else:
                            st.error("Failed to generate Excel file.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Download Section
    if st.session_state.output_file and os.path.exists(st.session_state.output_file):
        st.subheader("Download Result")
        with open(st.session_state.output_file, "rb") as f:
            st.download_button(
                label="📥 Download Completed Excel",
                data=f,
                file_name=os.path.basename(st.session_state.output_file),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
