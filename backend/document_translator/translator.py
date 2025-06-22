import pytesseract as pyt
pyt.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
from PIL import Image
import os
import requests
import socket

def ocr_image(file_path):
    text = pyt.image_to_string(Image.open(file_path))
    return text

def translate_text(text, target_lang):
    servers = [
        "https://translate.astian.org/translate",
        "https://libretranslate.de/translate",
        "https://translate.argosopentech.com/translate"
    ]
    for server in servers:
        try:
            response = requests.post(server, data={
                "q": text,
                "source": "en",
                "target": target_lang.lower(),
                "format": "text"
            }, timeout=10)
            if response.status_code == 200:
                return response.json()["translatedText"]
            print(f"[{server}] Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[{server}] Failed: {e}")
    raise Exception("All translation servers failed.")

def check_connection(host="1.1.1.1", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def process_document(file_path, target_lang):
    extracted_text = ocr_image(file_path)
    if not extracted_text.strip():
        raise ValueError("OCR returned empty text. Try using a clearer image.")
    return translate_text(extracted_text, target_lang)

if __name__=="__main__":
    file = "C:/Users/Aishik C/Desktop/Congressional Submission MAIN/CareBridge/backend/document_translator/medicalscreenshot.png"
    target_lang = "HI"
    
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file}")
    if not check_connection():
        print("No internet connection. Please connect and try again.")
        exit(1)

    print(process_document(file, target_lang))