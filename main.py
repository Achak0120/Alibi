from flask import Flask
from .backend import server
app = Flask(__name__)

app.register_blueprint(server.alibi_entry)