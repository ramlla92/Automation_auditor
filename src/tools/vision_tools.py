# automation-auditor/src/tools/vision_tools.py
from typing import List

from pypdf import PdfReader

def extract_images_from_pdf(path: str) -> List[bytes]:
    """
    Extract raw image bytes from a PDF.
    """
    images = []
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            for image_file_object in page.images:
                images.append(image_file_object.data)
    except Exception as e:
        print(f"VisionTools extraction error: {e}")
    return images
