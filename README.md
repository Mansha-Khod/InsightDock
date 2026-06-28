# Intelligent Document Assistant

An end-to-end Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents, build semantic vector indexes, and interact with them using natural language.

The application extracts document text, generates embeddings, builds a FAISS vector database, and uses Google's Gemini model to provide grounded answers with source attribution. It also generates executive summaries and key insights for the entire document.

---

## Features

* Upload any PDF document
* Automatic text extraction using PyMuPDF
* Intelligent document chunking
* Sentence Transformer embeddings
* FAISS vector search
* Retrieval-Augmented Question Answering (RAG)
* Executive Summary generation
* Key Insights extraction
* Source attribution with page references
* Interactive Streamlit interface
* Cached document processing
* Document statistics dashboard

---

## Tech Stack

* Python
* Streamlit
* Google Gemini 2.5 Flash
* Sentence Transformers
* FAISS
* PyMuPDF
* NumPy
* JSON

---

## Project Pipeline

```
PDF Upload
      │
      ▼
Text Extraction
      │
      ▼
Sentence Chunking
      │
      ▼
Embedding Generation
      │
      ▼
FAISS Vector Index
      │
      ▼
Semantic Search
      │
      ▼
Gemini RAG Response
```

---

## Repository Structure

```
data/
    reports/
    processed/
    embeddings/

models/

src/
    pdf_loader.py
    chunker.py
    embeddings.py
    vector_store.py
    rag.py
    executive_summary.py
    key_points.py

config/
app.py
requirements.txt
```

---

## Installation

Clone the repository

```bash
git clone <repository-url>
cd intelligent-document-assistant
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```text
GEMINI_API_KEY=YOUR_API_KEY
```

Run the application

```bash
streamlit run app.py
```

---

## Example Workflow

1. Upload a PDF document.
2. The application extracts text.
3. Text is divided into semantic chunks.
4. Embeddings are generated.
5. A FAISS vector index is created.
6. Ask natural language questions about the document.
7. Generate an executive summary.
8. Extract key insights.

---

## Future Improvements

* OCR support for scanned PDFs
* Multi-document search
* Citation highlighting
* Conversation memory
* Metadata filtering
* Docker deployment

---

## License

This project is intended for educational and portfolio purposes.
