from PIL import Image, ImageDraw, ImageFont
import pytesseract
import os
from document_translator import translator
from collections import defaultdict

# Set Tesseract path (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Extracts readable English text from an image
def image_to_string(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    print("[OCR OUTPUT]", text)
    return text

# Overlays translated text on image and saves it
def overlay_translated_text_on_image(original_image_path: str, lang: str, output_path: str):
    image = Image.open(original_image_path)
    draw = ImageDraw.Draw(image)

    # Use a readable TTF font
    font_path = "C:/Windows/Fonts/arial.ttf"
    font = ImageFont.truetype(font_path, size=20)

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    lines = defaultdict(list)
    for i in range(len(data["text"])):
        word = data["text"][i]
        conf = int(data["conf"][i])

        if word.strip() == "" or conf < 0:
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
        english_line = " ".join([w["text"] for w in line_words])
        if not english_line.strip():
            continue

        print("[TRANSLATE INPUT]", english_line)
        translated_line = translator.translate(english_line, lang)
        print("[TRANSLATE OUTPUT]", translated_line)

        # Position to draw: left/top of first word
        x = line_words[0]["left"]
        y = line_words[0]["top"]

        # Erase original text area with white box
        text_width = sum(w["width"] for w in line_words)
        text_height = max(w["height"] for w in line_words)
        draw.rectangle([x, y, x + text_width, y + text_height], fill="white")

        # Draw translated text
        draw.text((x, y), translated_line, fill="black", font=font)

    image.save(output_path)