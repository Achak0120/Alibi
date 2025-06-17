import pytesseract as pyt
pyt.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
from PIL import Image
import os
import deepl

def ocr_image(file_path):
    # Read image and do OCR
    text = pyt.image_to_string(Image.open(file_path))
    return text

def translate_text(text, target_lang):
    auth_key = "62488e5e-8323-4490-966d-24b60a1d6cb2"
    translator = deepl.Translator(auth_key)
    result = translator.translate_text(text, target_lang=target_lang)
    return result.text

def process_document(file_path, target_lang):
    extracted_text = ocr_image(file_path)
    translated_text = translate_text(extracted_text, target_lang)
    return translated_text

if __name__=="__main__":
    file = "C:/Users/Aishik C/Desktop/Congressional Submission MAIN/CareBridge/backend/document_translator/medicalscreenshot.png"
    target_lang = "HI"
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file}")
    print(process_document(file, target_lang))