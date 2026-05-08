import openpyxl
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger("SolarLoadCalculator.ExcelWriter")

class ExcelWriter:
    def __init__(self, template_path):
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")

    def get_month_row(self, month_str):
        """Map month string to Excel row (9 to 20)."""
        month_map = {
            "JAN": 9, "FEB": 10, "MAR": 11, "APR": 12, "MAY": 13, "JUN": 14,
            "JUL": 15, "AUG": 16, "SEP": 17, "OCT": 18, "NOV": 19, "DEC": 20,
            "जानेवारी": 9, "फेब्रुवारी": 10, "मार्च": 11, "एप्रिल": 12, "मे": 13, "जून": 14,
            "जुलै": 15, "ऑगस्ट": 16, "सप्टेंबर": 17, "ऑक्टोबर": 18, "नोव्हेंबर": 19, "डिसेंबर": 20
        }
        
        # Clean the month string
        month_str = month_str.upper()
        for key, row in month_map.items():
            if key.upper() in month_str:
                return row
        return 9  # Default to January if unknown

    def _to_float(self, val):
        """Safely convert value to float."""
        try:
            # Remove any non-numeric characters except decimal point
            if isinstance(val, str):
                val = re.sub(r'[^\d.]', '', val)
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def fill_template(self, data, output_path, is_second_meter=False):
        """Fill extracted data into the Excel template."""
        try:
            wb = openpyxl.load_workbook(self.template_path, data_only=False) # Keep formulas
            sheet = wb.active
            
            # Basic info mapping
            if is_second_meter:
                sheet['H1'] = data.get("consumer_name", "")
                sheet['H2'] = str(data.get("consumer_number", "")) # Keep as string
                sheet['H2'].number_format = '@' # Force text format
                sheet['H3'] = self._to_float(data.get("fixed_charges", 0))
                sheet['H4'] = self._to_float(data.get("sanction_load", 0))
                sheet['H5'] = data.get("connection_type", "")
            else:
                sheet['D1'] = data.get("consumer_name", "")
                sheet['D2'] = str(data.get("consumer_number", "")) # Keep as string
                sheet['D2'].number_format = '@' # Force text format
                sheet['D3'] = self._to_float(data.get("fixed_charges", 0))
                sheet['D4'] = self._to_float(data.get("sanction_load", 0))
                sheet['D5'] = data.get("connection_type", "")
            
            # Monthly data mapping
            month_row = self.get_month_row(data.get("billing_month", ""))
            if is_second_meter:
                sheet[f'H{month_row}'] = self._to_float(data.get("units_consumed", 0))
                sheet[f'I{month_row}'] = self._to_float(data.get("bill_amount", 0))
            else:
                sheet[f'D{month_row}'] = self._to_float(data.get("units_consumed", 0))
                sheet[f'E{month_row}'] = self._to_float(data.get("bill_amount", 0))
            
            wb.save(output_path)
            logger.info(f"Excel file saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error filling Excel template: {e}")
            return False
