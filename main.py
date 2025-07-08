from flask import Flask
from .backend.document_translator import server
app = Flask(__name__)

app.register_blueprint(server.alibi_entry)