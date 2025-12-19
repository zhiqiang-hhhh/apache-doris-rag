# Doris RAG

A RAG system based on Apache Doris hybrid search capabilities. For more information about hybrid search, please refer to the [Doris Official Documentation](https://doris.incubator.apache.org/zh-CN/docs/4.x/ai/ai-overview).

## Components

- `conf.ini`: Project configuration file, including Doris connection, model configuration, document path, and language settings.
- `index_md_to_doris.py`: Offline index build script. It chunks `doris-website` documents, generates embeddings, and writes them to the Doris vector table.
- `rag_service.py`: FastAPI backend service, providing `/api/chat` (RAG interface) and `/` (Web frontend).
- `rag_cli.py`: Command-line RAG client for quick testing in the terminal.

## Installation

It is recommended to install in a `conda` environment:

```bash
pip install "doris-vector-search>=0.0.5" langchain langchain-community openai fastapi uvicorn pydantic pandas
```


## Configuration

Before running, please modify the `conf.ini` configuration file according to your environment. All runtime and indexing parameters are consolidated in this file (no env vars required):

- **[doris]**: Configure Doris FE connection information (host, port, user, password, db, table).
- **[embedding]**: Configure embedding for both retrieval and indexing.
	- `type`: `openai` or `openrouter` (for indexing). `ollama` is supported for retrieval in `rag_lib.py`, but indexing requires `openai`/`openrouter`.
	- `model`: embedding model name.
	- `base_url`, `api_key`: endpoint and credential.
	- `embed_dim` (optional): embedding dimension (defaults to 1536 if omitted).
- **[llm]**: Configure LLM model (supports openai protocol).
- **[docs]**: Document ingestion settings.
	- `doc_root`: directory path to scan `.md`/`.mdx`.
	- `chunk_size`: chunk size for markdown splitting (default 500).
	- `chunk_overlap`: chunk overlap for splitting (default 100).
- **[app]**: Set application language (`zh` or `en`).

## Build Vector Index

Ensure Doris FE/BE is started and `conf.ini` is configured correctly, then execute one of the following:

```bash
# Recommended: CocoIndex CLI
cocoindex update index_md_to_doris
```

This builds the vector index by:

1. Scan all markdown/mdx files in the directory specified by `doc_root` in `conf.ini`.
2. Clean and chunk the text.
3. Generate embeddings using the specified embedding model.
4. Write to the Doris database.

## Start RAG Web Service

Start the FastAPI service:

```bash
uvicorn rag_service:app --host 0.0.0.0 --port 8000
```

Open your browser and visit <http://localhost:8000> to use the chat interface.

## Command Line Test (Optional)

```bash
python rag_cli.py
```

Enter your question and press Enter to see the answer generated based on Doris document retrieval + LLM.

## Roadmap

- [x] **Basic RAG Pipeline**: Markdown ingestion, Vector Storage (Doris), Retrieval, and LLM generation.
- [ ] **Parameter Tuning**: Experiment with different embedding models and chunking strategies.
- [ ] **Document Enhancement**: Clean, filter, and synthesize high-quality data.
- [ ]  **Query Pre-processing**: Implement intent detection and CoT (Chain-of-Thought) enhancement, evolving into an Agentic RAG.
- [ ] **Cross-Document Retrieval**: Utilize Knowledge Graphs.
- [ ] **More Data Sources**: Support image, code, etc.
- [ ] **Advanced Retrieval**: Hybrid search (Keyword + Vector) optimization.
- [ ] **Evaluation**: Identify and optimize documents with poor retrieval quality. 
- [ ] **UI Enhancements**: Better chat interface with history management.
