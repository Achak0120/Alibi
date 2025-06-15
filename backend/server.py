from flask import Flask
from document_translator.routes import translator_bp
from NLP_chatbot.routes import chatbot_bp

app = Flask(__name__)

# Register Blueprints (moduelar routing)
