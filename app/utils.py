import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger("SolarLoadCalculator")

def ensure_directories():
    """Ensure necessary directories exist."""
    dirs = ["data/sample_bills", "data/outputs", "data/templates"]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            logger.info(f"Created directory: {d}")

def get_timestamp():
    """Generate a timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def validate_file_extension(filename, allowed_extensions):
    """Validate file extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions
