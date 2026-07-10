# InsightDock  
![Python](https://img.shields.io/badge/Python-3.11-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-red) ![NLP](https://img.shields.io/badge/NLP-RAG-success) ![License](https://img.shields.io/badge/License-MIT-green)

An end-to-end Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents, build semantic vector indexes, and interact with them using natural language.

The application combines Natural Language Processing (NLP), semantic search, vector embeddings, and Retrieval-Augmented Generation (RAG) to extract information from PDF documents and answer questions with grounded responses.

### Live Demo

**Application:** https://insightdock.streamlit.app/

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

## Project Highlights

- Built an end-to-end NLP + RAG pipeline for PDF question answering.
- Uses Sentence Transformers to generate semantic embeddings.
- Stores vector representations using FAISS for efficient similarity search.
- Generates grounded answers with page-level source attribution.
- Includes automated executive summaries and document key insights.
- Interactive Streamlit interface with document statistics and cached processing.

---

## Tech Stack

* Python
* Streamlit
* Google Gemini 2.5 Flash
* Sentence Transformers
* Hugging Face Transformers
* FAISS
* PyMuPDF
* NumPy
* JSON

---

## System Architecture

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
<img width="1536" height="1024" alt="nlp" src="https://github.com/user-attachments/assets/af371f1e-021c-4bff-b9b4-c2e4ad5705b3" />
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
git clone https://github.com/Mansha-Khod/InsightDock.git
cd InsightDock
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

- OCR support for scanned PDFs
- Hybrid search (keyword + semantic retrieval)
- Multi-document knowledge base
- Citation highlighting inside documents
- Conversational memory
- Metadata filtering
- Local LLM support (Llama, Mistral)
- Docker deployment

---

## License

Distributed under the MIT License. See `LICENSE` for more details.

 **Note**

The live demo uses the Gemini API. On the free tier, executive summaries and key insights consume API quota and may become temporarily unavailable after the daily request limit is reached. In production, these features can be powered by local summarization models (such as BART or T5) or alternative LLM providers.

