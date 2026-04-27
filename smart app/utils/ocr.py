import pytesseract
from PIL import Image
import os

def extract_text_from_image(image_path):
    """
    Extracts text from an image using Tesseract OCR.
    """
    try:
        # Pointing to the custom installation path
        pytesseract.pytesseract.tesseract_cmd = r'C:\Users\SanjaY N\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        text = pytesseract.image_to_string(Image.open(image_path))
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def process_file(file_path):
    """
    Processes the uploaded file based on its extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        return extract_text_from_image(file_path)
    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "Unsupported file format"
