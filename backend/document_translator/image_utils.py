from PIL import Image, ImageDraw, ImageFont
import cv2
import pytesseract
import requests
import os
from document_translator import translator
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Extracts readable english text from an image
# Outputs plain english text
def image_to_string(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

def overlay_translated_text_on_image(original_image_path: str, lang: str, output_path: str):
    image = Image.open(original_image_path)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    lines = defaultdict(list)
    for i in range(len(data["text"])):
        word = data["text"][i]
        if word.strip() == "" or int(data["conf"][i]) < 0:
            continue
        key = (data["block_num"][i], data["line_num"][i])
        word_info = {
            "text": word,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i]
        }
        lines[key].append(word_info)
    
    # Translate and draw each line
    for line_words in lines.values():
        # Join english words in the line
        english_line = " ".join([w["text"] for w in line_words])
        translated_line = translator.translate(english_line, lang)
        
        # Position to draw: left/top of first word
        x = line_words[0]["left"]
        y = line_words[0]["top"]
        
        # Add translated lines
        draw.text((x, y), translated_line, fill="black", font=font)
    image.save(output_path)