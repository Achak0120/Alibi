from flask import Flask
from flask import request, send_file
from flask import Blueprint, render_template, abort
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
    request.files['image']
    request.form['targetLanguage']
    