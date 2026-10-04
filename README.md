# DocuChat AI

**Chat with your documents using Retrieval-Augmented Generation (RAG).**

DocuChat AI is a Django-based AI application that allows users to upload documents and ask questions about their content. It uses **RAG, semantic embeddings, and FAISS vector search** to retrieve relevant information before generating an answer with an LLM.

##  Features

Chat with uploaded documents
Retrieval-Augmented Generation (RAG)
Semantic search with Sentence Transformers
FAISS vector similarity search
Persistent chat sessions
Video transcription using Whisper
Supports PDF, TXT, DOCX, PPTX, XLSX, CSV and video files
Django authentication
Context-grounded answers to reduce hallucinations

## Tech Stack

**Backend:** Django, Python  
**RAG:** LangChain, Sentence Transformers, FAISS  
**LLM:** OpenAI-compatible API  
**Documents:** PyPDF, python-pptx, docx2txt, OpenPyXL  
**Video:** FFmpeg, faster-whisper  
**Database:** SQLite

## How It Works

Document / Video
       ↓
Text Extraction
       ↓
Chunking
       ↓
Embeddings
       ↓
FAISS Vector Store
       ↓
User Question
       ↓
Semantic Search
       ↓
Relevant Context
       ↓
LLM
       ↓
Grounded Answer

Installation & Setup
1. Clone the repository
git clone https://github.com/<your-username>/DocuChat-AI.git
cd DocuChat-AI
2. Create a virtual environment

Windows:

python -m venv .venv
.venv\Scripts\activate

Linux / macOS:

python3 -m venv .venv
source .venv/bin/activate
3. Install Python dependencies
pip install -r requirements.txt
4. Configure environment variables

Create a .env file in the project root and add:

LLM_GATEWAY_KEY=your_api_key
LLM_GATEWAY_URL=your_llm_endpoint
LLM_MODEL=your_model

Never commit your .env file or API keys to GitHub.

5. Install FFmpeg

FFmpeg is required for video processing.

Windows:

Install FFmpeg and make sure it is available in your system PATH.

Verify:

ffmpeg -version

Ubuntu / Debian:

sudo apt update
sudo apt install ffmpeg

macOS:

brew install ffmpeg
6. Initialize the database
python manage.py migrate
7. Create an admin user
python manage.py createsuperuser

Follow the prompts to create your username and password.

8. Start the development server
python manage.py runserver

Open the application at:

http://127.0.0.1:8000/
