from flask import Flask
from flask import request, send_file
from flask import Blueprint, render_template, abort, flash, redirect, url_for
from jinja2 import TemplateNotFound
from document_translator import image_utils
from document_translator import translator
import os

alibi_entry = Blueprint('Alibi Entry Point', __name__,
                        template_folder='templates')

@alibi_entry.route('/', defaults={'page': 'index'})
@alibi_entry.route('/<page>')

def show(page):
    try:
        render_template(f'pages/{page}.html')
    except TemplateNotFound:
        abort(404)


app = Flask(__name__)
app.register_blueprint(alibi_entry)
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image part')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash("No selected image, please select an image or provide a name for existing image")
            return redirect(request.url)
    save_path = os.path.join('uploads', 'temp.jpg')
    file.save(save_path)
    
    extracted_text = image_utils.image_to_string(save_path)
    lang = request.form['targetLanguage']
    image_utils.overlay_translated_text_on_image(
        original_image_path=save_path,
        lang=lang,
        output_path="uploads/translated.png"
    )
    return send_file("uploads/translated.png", mimetype="image/png")