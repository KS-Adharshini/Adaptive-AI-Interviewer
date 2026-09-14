import io
import re
from typing import Optional
from pypdf import PdfReader
from ..utils.helpers import setup_logger

logger = setup_logger("ResumeParser")

def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """
    Extract readable text from an uploaded PDF resume.
    Accepts bytes or file-like object.
    """
    if pdf_file is None:
        return None
    
    try:
        if isinstance(pdf_file, bytes):
            reader = PdfReader(io.BytesIO(pdf_file))
        else:
            reader = PdfReader(pdf_file)
            
        full_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)
                
        raw_text = "\n".join(full_text)
        # Clean up excess whitespace and non-standard characters
        cleaned = re.sub(r"[ \t]+", " ", raw_text)
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned).strip()
        
        # Limit to reasonable token count (~3000 chars) for prompt context
        truncated = cleaned[:3500]
        logger.info(f"Successfully extracted {len(truncated)} characters from resume.")
        return truncated
    except Exception as e:
        logger.warning(f"Error parsing PDF resume: {e}")
        return None
