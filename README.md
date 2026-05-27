# Document Q&A Agent

A local document question-answering project built with FastAPI and Streamlit.

## Features

- Upload documents and index their content
- Search and answer questions over uploaded files
- Streamlit UI for document upload and query interactions
- FastAPI backend for document ingestion and query handling

## Project Structure

- `main.py` - FastAPI application entrypoint
- `api.py` - API routes for upload, document listing, markdown retrieval, and query
- `routes.py` - Route registration for FastAPI
- `config.py` - Environment and application settings
- `file_loader.py` - Document text extraction utilities
- `markdown_generator.py` - Markdown generation utilities
- `rag_service.py` - Local retrieval and query logic
- `streamlit.py` - Streamlit user interface
- `model.py` - Pydantic request/response models
- `.env` - Environment variable placeholders

## Quick Start

1. Install dependencies in the virtual environment.
2. Set environment variables in `.env`.
3. Run the backend:

```bash
python main.py
```

4. Run the Streamlit UI:

```bash
python -m streamlit run streamlit.py
```

## Notes

- Update `.env` with your API keys and endpoints before running.
- This project uses local document embeddings and retrieval.
