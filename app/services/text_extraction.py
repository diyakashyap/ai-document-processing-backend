from io import BytesIO

import pytesseract
from PIL import Image
from pypdf import PdfReader

from app.services.file_validation import get_extension


def extract_text(file_name: str, content: bytes) -> str:
    extension = get_extension(file_name)
    if extension == "txt":
        return content.decode("utf-8", errors="ignore")
    if extension == "pdf":
        return extract_pdf_text(content)
    if extension in {"png", "jpg", "jpeg"}:
        return extract_image_text(content)
    return ""


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(page.strip() for page in pages if page.strip())


def extract_image_text(content: bytes) -> str:
    image = Image.open(BytesIO(content))
    return pytesseract.image_to_string(image).strip()
