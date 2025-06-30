from PIL import Image, ImageDraw, ImageFont
import cv2
import pytesseract
import requests
import os

pytesseract.pytesseract.tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Extracts readable english text from an image
# Outputs plain english text
def image_to_string(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

def overlay_translated_text_on_image(original_image_path: str, translated_text: str, output_path: str):
    image = Image.open(original_image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    for i in range(len(data["text"])):
        