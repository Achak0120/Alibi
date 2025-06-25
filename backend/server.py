from flask import Flask
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

alibi_entry = Blueprint('Alibi Entry Point', __name__,
                        template_folder='templates')

@alibi_entry.route('/', defaults={'page': 'index'})
@alibi_entry.route('/<page>')

def show(page):
    try:
        render_template(f'pages/{page}.html')
    except TemplateNotFound:
        abort(404)