# server.py
import os
import sys
from flask import Flask, request, send_file, Blueprint, render_template, abort, flash, redirect
from flask_cors import CORS
from jinja2 import TemplateNotFound

# Set working directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_TRANS_DIR = os.path.join(BASE_DIR, 'document_translator')
INPUT_DIR = os.path.join(DOC_TRANS_DIR, 'input')
OUTPUT_DIR = os.path.join(DOC_TRANS_DIR, 'output')

# Ensure paths are importable
sys.path.append(DOC_TRANS_DIR)

# Import translator logic and font map
from font_map import LANGUAGE_FONT_MAP
import main as translator_main

# NEW: import router
from translator_router import build_router

# Flask app setup
app = Flask(__name__)
CORS(app)

# Create input/output dirs
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Build router ONCE at startup, using the language codes you actually expose
PRODUCT_CODES = set(LANGUAGE_FONT_MAP.keys())  # or pull from your SUPPORTED_LANGUAGES if you prefer
ROUTER = build_router(PRODUCT_CODES)

# Blueprint
alibi_entry = Blueprint('Alibi Entry Point', __name__, template_folder='templates')

@alibi_entry.route('/', defaults={'page': 'index'})
@alibi_entry.route('/<page>')
def show(page):
    try:
        return render_template(f'pages/{page}.html')
    except TemplateNotFound:
        abort(404)

# Register blueprint
app.register_blueprint(alibi_entry)

# API endpoint for image upload + translation
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        flash('No image part')
        return redirect(request.url)

    file = request.files['image']
    if file.filename == '':
        flash("No selected image.")
        return redirect(request.url)

    input_path = os.path.join(INPUT_DIR, 'temp.jpg')
    file.save(input_path)

    requested_lang = request.form.get('targetLanguage', 'en')
    output_path = os.path.join(OUTPUT_DIR, 'translated.png')

    # NEW: pick a provider and normalized code
    try:
        service, norm_code = ROUTER.pick(requested_lang)
    except Exception as e:
        # Fail fast with a clear message the frontend can show
        return (str(e), 400)

    # OPTIONAL: if your pipeline can accept service + normalized code, pass them.
    # If it can't yet, at minimum pass norm_code instead of raw requested_lang.
    translator_main.translate_image_pipeline(
        image_path=input_path,
        output_path=output_path,
        target_lang=norm_code,        # << use normalized code
        font_map=LANGUAGE_FONT_MAP,
        service_hint=service          # << add this param in your pipeline (see note below)
    )

    return send_file(output_path, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
