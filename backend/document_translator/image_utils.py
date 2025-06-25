from PIL import Image, ImageDraw, ImageFont
import cv2
import pytesseract
import requests
import os

pytesseract.pytesseract.tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def image_to_string(image_path):
    return pytesseract.image_to_string(Image.open(image_path))