from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from googletrans import Translator as GoogleTranslator
from spellchecker import SpellChecker
from font_map import LANGUAGE_FONT_MAP
from google.cloud import vision
import numpy as np
import wordninja
import deepl
import easyocr
import cv2
import sys
import os

# Font configs
FONT_DIR = os.path.join(os.path.dirname(__file__), "Noto")

def is_junk(text):
    return sum(1 for c in text if not c.isalnum() and c not in '.,:;!?') > len(text) * 0.4

def get_font_by_lang(lang_code: str, size: int = 20):
    font_name = LANGUAGE_FONT_MAP.get(lang_code, 'NotoSans-Regular.ttf')
    font_path = os.path.join(FONT_DIR, font_name)
    if os.path.isfile(font_path):
        return ImageFont.truetype(font_path, size)
    else:
        print(f"[WARN] Font not found for {lang_code}, using default.")
        return ImageFont.load_default()

# Preprocess inserted image for better translation
def preprocess_image_for_ocr(image_path):
    image = Image.open(image_path).convert("RGB")

    # Convert to grayscale
    gray_image = ImageOps.grayscale(image)

    # Enhance contrast
    contrast_enhancer = ImageEnhance.Contrast(gray_image)
    contrast_image = contrast_enhancer.enhance(2.5)  # Increase contrast

    # Binarize
    threshold = 180
    binarized_image = contrast_image.point(lambda x: 0 if x < threshold else 255).convert("L")

    return binarized_image

# OCR Processing with Google Vision API
def perform_ocr_with_google_vision(image_path):
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, "rb") as image_file:
        content = image_file.read()
        
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    annotations = response.text_annotations
    
    extracted_text_boxes = []
    
    if annotations:
        for annotation in annotations[1:]:
            vertices = [(v.x, v.y) for v in annotation.bounding_poly.vertices]
            text = annotation.description
            extracted_text_boxes.append((vertices, text))
    
    return extracted_text_boxes
            
def get_font(image, text, width, height, lang_code):
    font_size = None
    font = None
    box = None
    x = 0
    y = 0
    draw = ImageDraw.Draw(image)

    for size in range(1, 500):
        new_font = get_font_by_lang(lang_code, size)
        new_box = draw.textbbox((0, 0), text, font=new_font)
        new_w = new_box[2] - new_box[0]
        new_h = new_box[3] - new_box[1]

        if new_w > width or new_h > height:
            break

        font_size = size
        font = new_font
        box = new_box
        w = new_w
        h = new_h
        x = (width - w) // 2 - box[0]
        y = (height - h) // 2 - box[1]

    return font, x, y

def add_discoloration(color, strength):
    r, g, b = color[:3]
    r = max(0, min(255, r + strength))
    g = max(0, min(255, g + strength))
    b = max(0, min(255, b + strength))
    if r == 255 and g == 255 and b == 255:
        r, g, b = 245, 245, 245
    return (r, g, b)

def get_background_color(image, x_min, y_min, x_max, y_max):
    image = image.convert('RGBA')
    margin = 10
    edge_region = image.crop((
        max(x_min - margin, 0),
        max(y_min - margin, 0),
        min(x_max + margin, image.width),
        min(y_max + margin, image.height),
    ))
    pixels = list(edge_region.getdata())
    opaque_pixels = [pixel[:3] for pixel in pixels if pixel[3] > 0]

    if not opaque_pixels:
        background_color = (255, 255, 255)
    else:
        from collections import Counter
        most_common = Counter(opaque_pixels).most_common(1)[0][0]
        background_color = most_common

    return add_discoloration(background_color, 40)

def get_text_fill_color(background_color):
    luminance = (
        0.299 * background_color[0]
        + 0.587 * background_color[1]
        + 0.114 * background_color[2]
    ) / 255
    return "black" if luminance > 0.5 else "white"

def replace_text_with_translation(image_path, translated_texts, text_boxes, lang_code):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    for text_box, translated in zip(text_boxes, translated_texts):
        if translated is None:
            continue

        x_min, y_min = text_box[0][0][0], text_box[0][0][1]
        x_max, y_max = text_box[0][0][0], text_box[0][0][1]

        for x, y in text_box[0]:
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)

        background_color = get_background_color(image, x_min, y_min, x_max, y_max)
        draw.rectangle(((x_min, y_min), (x_max, y_max)), fill=background_color)

        font, x_offset, y_offset = get_font(image, translated, x_max - x_min, y_max - y_min, lang_code)

        draw.text(
            (x_min + x_offset, y_min + y_offset),
            translated,
            fill=get_text_fill_color(background_color),
            font=font,
        )

    return image

def translate_image_pipeline(image_path, output_path, target_lang, font_map):
    # OCR
    extracted_text_boxes = perform_ocr_with_google_vision(image_path)

    # Get font fallback
    selected_lang_code = target_lang.lower()
    if selected_lang_code not in font_map:
        selected_lang_code = "en"

    # DeepL setup
    deepl_translator = deepl.Translator(os.environ["DEEPL_API_KEY"])
    deepl_supported = {lang.code.lower(): lang.name for lang in deepl_translator.get_target_languages()}

    # Google fallback setup
    google_translator = GoogleTranslator()
    translated_texts = []
    cache = {}

    spell = SpellChecker()
    for _, text in extracted_text_boxes:
        if not text:
            translated_texts.append(None)
            continue
        if is_junk(text):
            print(f"[SKIP] Skipped junk: {text}")
            translated_texts.append(None)
            continue
        
        # Spell-correct
        words = text.split()
        corrected_words = [spell.correction(w) or w for w in words]
        corrected_text = " ".join(corrected_words)

        # Wordninja split long garbled words
        split_words = []
        for word in corrected_text.split():
            if len(word) > 10:
                split_words.extend(wordninja.split(word))
            else:
                split_words.append(word)
        final_text = " ".join(split_words)

        # Cache
        if final_text in cache:
            translated_texts.append(cache[final_text])
            continue

        # Translate
        try:
            if target_lang.lower() in deepl_supported:
                result = deepl_translator.translate_text(
                    final_text,
                    source_lang="EN",
                    target_lang=target_lang.upper()
                )
                translated = result.text
                print(f"[DeepL] {final_text} → {translated}")
            else:
                result = google_translator.translate(final_text, src="en", dest=target_lang)
                translated = result.text
                print(f"[Google] {final_text} → {translated}")

            cache[final_text] = translated
            translated_texts.append(translated)

        except Exception as e:
            print(f"[ERROR] Failed to translate '{final_text}': {e}")
            translated_texts.append(None)

    # Replace and draw text
    image = replace_text_with_translation(
        image_path, translated_texts, extracted_text_boxes, selected_lang_code
    )

    image.save(output_path)
    
# Script Setup

if __name__ == "__main__":
    input_folder = "input"
    output_folder = "output"
    target_lang = sys.argv[1] if len(sys.argv) > 1 else "en"

    files = os.listdir(input_folder)
    image_files = [file for file in files if file.endswith((".jpg", ".jpeg", ".png"))]

    for filename in image_files:
        print(f'[INFO] Processing {filename}...')
        image_path = os.path.join(input_folder, filename)
        output_path = os.path.join(
            output_folder,
            f"{os.path.splitext(filename)[0]}-translated{os.path.splitext(filename)[1]}"
        )
        translate_image_pipeline(image_path, output_path, target_lang, LANGUAGE_FONT_MAP)
        print(f'[INFO] Saved as {output_path}...')