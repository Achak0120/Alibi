# 🌍 LegalBridge – A Web App to Help Immigrants Understand Documents

**LegalBridge** is a full-stack web application that helps immigrants — documented or undocumented — understand important legal and medical documents in their native languages.

The app runs fully offline on the backend, without any cloud APIs, user accounts, or internet-based AI services. Users interact through a web browser, and all document processing and AI chatbot functionality is powered by local, open-source Python modules.

---

## 🧠 What LegalBridge Does

### 📸 Image Translator (Image → Translated Image)
Users can upload pictures of physical documents — such as medical records, legal notices, or government forms. LegalBridge will:
- Extract all visible English text from the image
- Translate it to the user’s chosen language
- Rebuild the image with translated text in place of the original text
- Return the new translated image to the browser for viewing/download

### 💬 Multilingual Legal Assistant (Chatbot)
Users can ask questions in **any language** — and the chatbot will:
- Automatically detect and translate the message into English
- Generate a clear, simple response using a **locally hosted LLM**
- Translate the answer back into the user’s original language
- Deliver the translated answer directly in the web interface

> 🔐 LegalBridge does **not** offer legal advice. It provides general information and help only. No user data or documents are stored on the server.

---

## 🌐 Web Architecture
Frontend (HTML/CSS/JScript)
↓ ↑
REST API (Flask / FastAPI backend)
↓ ↑
OCR | Translation | LLM (llama-cpp) | Image Editor


All processing happens in your own backend — **no external APIs, no cloud calls, no user accounts**.

---

## 🧰 Tech Stack

| Part                  | Technology                |
|-----------------------|---------------------------|
| Frontend              | HTML/CSS/JS / React       |
| API Server            | Python + Flask or FastAPI |
| OCR                   | `pytesseract`             |
| Translation (offline) | `argos-translate`         |
| Language Detection    | `langdetect`              |
| Local LLM             | `llama-cpp-python`        |
| Image Editor          | `Pillow`, `OpenCV`        |

---

## 🚀 Getting Started (For Developers)

### ✅ Requirements

- Python 3.9+
- Node.js (for frontend, optional depending on stack)
- Basic command line usage
- 4–8 GB RAM (for local LLM model)
- Internet access (for initial setup only)

---

### 📦 Backend Setup

1. **Clone the Repo**

```bash
git clone https://github.com/yourusername/legalbridge.git
cd legalbridge/backend



