# Hands-on RAG for Production

Code examples and Jupyter notebooks for the book **"Hands-on RAG for Production"**.

This repository contains practical examples demonstrating Retrieval-Augmented Generation (RAG) techniques, from basic implementations to advanced topics like Agentic RAG, RAG with knowledge graphs and multimodal RAG.

You can run these examples locally or using Google CoLab.

## Prerequisites

- Python 3.10+
- API keys (depending on which chapters you run):
  - OpenAI API key (`OPENAI_API_KEY`)
  - Anthropic API key (`ANTHROPIC_API_KEY`)
  - Vectara API key (for Chapter 5)
- Docker (for Chapter 4 caching examples)
- Neo4j (for Chapter 9 knowledge graphs)

## Quick Start (Local)

1. Clone the repository:
```bash
git clone https://github.com/ofermend/hands-on-rag.git
cd hands-on-rag
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies for the chapter you want to run:
```bash
cd chapter1
pip install -r requirements.txt
```

4. Set up your API keys:
```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

5. Run the Jupyter notebooks:
```bash
jupyter notebook
```

or 

```bash
jupyter lab
```

## Chapter Overview

### Chapter 1: Introduction to RAG
A simple end-to-end RAG example using LangChain, demonstrating the core RAG workflow: load, split, embed, store, and query.

**Notebooks:**
- `sample-rag.ipynb` - Basic RAG pipeline with Alice in Wonderland

---

### Chapter 2: The Base RAG Stack
Deep dive into the foundational components of RAG systems: document parsing, text chunking, embedding models, vector databases, and generative LLMs.

**Notebooks:**
- `parse-pdf.ipynb` - PDF text extraction with PyMuPDF
- `parse-docx.ipynb` - DOCX parsing with python-docx
- `parse-in-llm.ipynb` - Using LLMs for document parsing
- `embedding.ipynb` - Sentence embeddings and similarity
- `pgvector-simple.ipynb` - PostgreSQL vector search basics
- `sqlite-vec.ipynb` - SQLite vector extension
- `generative-llms.ipynb` - Using Claude for RAG generation

---

### Chapter 3: Scaling RAG
Techniques for improving RAG quality at scale: parsing document at scale, using rerankers, guardrails, and hallucination handling.

**Notebooks:**
- `split-pdf.ipynb` - PDF splitting strategies for large documents
- `parse-tables.ipynb` - Table extraction from documents
- `reranking.ipynb` - Reranking retrieved results
- `guardrails.ipynb` - Input/output guardrails
- `hallucinations.ipynb` - Detecting and handling hallucinations

---

### Chapter 4: Performance & Security
Optimizing RAG systems for production with caching strategies and data redaction techniques.

**Notebooks:**
- `caching.ipynb` - Exact-match and semantic caching with Redis
- `redaction.ipynb` - Sensitive data redaction

---

### Chapter 5: Managed RAG Services
Using managed RAG platforms like Vectara for simplified RAG deployment.

**Notebooks:**
- `vectara-ingest.ipynb` - Ingesting documents into Vectara
- `vectara-list-docs.ipynb` - Listing and managing documents
- `vectara-query.ipynb` - Querying Vectara

---

### Chapter 6: Evaluation & Metrics
Evaluating RAG system quality using LLM-as-a-judge and specialized metrics.

**Notebooks:**
- `llm-as-a-judge.ipynb` - Using LLMs to evaluate RAG outputs
- `metrics.ipynb` - RAG evaluation metrics
- `umbrela.ipynb` - Umbrella evaluation concepts

---

### Chapter 7: Agents & Multi-Agent Systems
Building intelligent agents that use RAG for tool-augmented reasoning.

**Notebooks:**
- `tool-calling.ipynb` - Basic LLM tool/function calling
- `react-agent-langchain.ipynb` - ReAct pattern with LangChain
- `function-agent-llamaindex.ipynb` - Function-calling agents with LlamaIndex
- `vectara-agent.ipynb` - RAG agents with Vectara
- `crewai-multi-agent.ipynb` - Multi-agent systems with CrewAI

---

### Chapter 8: Multimodal RAG
Extending RAG to handle images, audio, and tables alongside text.

**Notebooks:**
- `image-rag-langchain.ipynb` - Image-based RAG with LangChain and Docling
- `image-retrieval-siglip.ipynb` - Image retrieval with SigLIP
- `audio-transcribe.ipynb` - Audio transcription and indexing
- `simple-table-chunking.ipynb` - Table extraction and chunking

---

### Chapter 9: Knowledge Graph RAG
Combining knowledge graphs with RAG for enhanced reasoning and retrieval.

**Notebooks:**
- `create-graph.ipynb` - Building knowledge graphs from movie data
- `graph-query.ipynb` - Querying knowledge graphs
- `graphrag-create.ipynb` - Using Microsoft's GraphRAG
- `graphrag-query.ipynb` - Querying with GraphRAG

**Requirements:** Neo4j database running locally or in Docker.

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this code for both personal and commercial purposes.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

If you encounter issues, please open a GitHub issue with:
- The chapter and notebook you're running
- The error message
- Your Python version and OS
