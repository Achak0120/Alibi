# 🌍 Alibi - A Web App to Help Immigrants Understand Documents

**Alibi** is a full-stack web application that helps immigrants - documented or undocumented - understand important legal and medical documents in their native languages.

The app runs fully offline on the backend, without any cloud APIs, user accounts, or internet-based AI services for **FREE**. Users interact through a web browser, and all document processing and AI chatbot functionality is powered by local, open-source software.

## ⚙ What Alibi Does:
### 📸 Image Translator (Image → Translated Image)
Users can upload pictures of physical documents - such as medical records, legal notices, or government forms. Alibi will:
* Extract all visible English text from the image
* Translate it to the user's chosen language
* Rebuild the image with translated text in place of the original text
* Return the new translated image to the browser for viewing/download

### 🈯 Multilingual Document Assistant (Chatbot)
Users can ask questions in **any language** - and the chatbot will:
* Automatically detect and translate the message into English
* Generate a clear, simple response using a **locally hosted LLM**
* Translate the answer back into the user's original language
* Deliver the translated answer directly in the web interface

> 🚨 Alibi does **not** offer legal advice. It provides general information and help only. No user data or documents are stored on the server.

## 🖥️ Web Architecture
Frontend (HTML/CSS/JScript)
↓ ↑
REST API (Flask / FastAPI backend)
↓ ↑
OCR | Translation | LLM (Google Generative AI) | Image Editor

All processing happens in your own backend - **no external APIs for document translation, no cloud calls, no user accounts**.

## 💻 Tech Stack
| Part                       | Technology Used                          |
|----------------------------|------------------------------------------|
| 🌐 Frontend                | React, Vite, HTML/CSS/JavaScript         |
| ⚙️ Backend (Document Translator) | Python + Flask                     |
| ⚙️ Backend (Chatbot)       | Python + FastAPI + Uvicorn               |
| 🔍 OCR                     | Google Cloud Vision API                  |
| 🌍 Translation             | DeepL API, Google Translate API          |
| 🖼️ Image Processing        | Pillow (PIL)                             |
| 📦 Package Management      | pip (Python), npm (JavaScript)           |

## 📦 Getting Started (For Developers)

### 📋 Hardware Requirements
* Python 3.9+
* npm & pip
* Basic command line usage
* 4-8 GB RAM recommended
* Internet access (for API calls)

---
### Setup Instructions (Make sure all terminal windows are opened in your code editor with the same root directory)

1. **Clone the Repo**
```bash
git clone https://github.com/Achak0120/Alibi.git
```

2. **Install requirements.txt**
```bash
cd Alibi
pip install -r backend/NLP_chatbot/requirements.txt
pip install -r requirements.txt
```

3. **Run the Document Translator Backend** (Open a new terminal window --> Terminal 1)
```bash
cd backend/document_translator
python server.py
```

4. ** Run the Chatbot Backend** (Open a new terminal window --> Terminal 2, but keep all previous terminal windows open)
```bash
cd backend/NLP_chatbot
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

5. **Run the Frontend** (Open a new terminal window --> Terminal 3, but keep all previous terminal windows open)
```bash
cd frontend
npm install  (only do once, either globally or in your virtual environment)
npm run dev
```

6. **Navigate to Project Frontend via URL in your search engine**
> The most common port to enter the project is (*http://localhost:5173/*)
> To make sure you are in the correct port url, check the terminal output in terminal 3 after you complete **Step 5** and travel to that URL
