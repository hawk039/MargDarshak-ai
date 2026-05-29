# Marg Darshak AI Service

An AI knowledge processing platform designed to transform Indian wisdom literature into structured knowledge, philosophical insights, and high-quality training datasets for AI-powered guidance systems.

---

## Vision

Marg Darshak aims to build an AI companion that helps people navigate inner conflicts, uncertainty, fear, attachment, purpose, and difficult life decisions using timeless wisdom from texts such as:

* Bhagavad Gita
* Upanishads
* Yoga Sutras
* Vedas
* Vivekananda's teachings
* Other philosophical and spiritual literature

The goal is not to create a scripture search engine, but a wisdom-driven guidance system capable of delivering calm, practical, and context-aware responses.

---

## Current Scope

This repository contains the AI Knowledge Service responsible for:

* Document ingestion
* PDF text extraction
* Verse-level structuring
* Wisdom extraction
* Principle generation
* Dataset generation
* Dataset auditing
* Fine-tuning dataset export

This service is independent from the main application backend and serves as the foundation for future AI capabilities.

---

## Architecture

```text
Wisdom Literature
        ↓
PDF Ingestion
        ↓
Text Extraction
        ↓
Canonical Verse Generation
        ↓
Wisdom Entry Creation
        ↓
Principle Extraction
        ↓
Training Example Generation
        ↓
Dataset Auditing
        ↓
JSONL Export
        ↓
Fine-Tuning Pipeline
        ↓
Local LLM / RAG System
        ↓
Marg Darshak Application
```

## Key Features

### Document Processing

* PDF ingestion
* Metadata management
* Structured document storage
* Canonical verse extraction

### Knowledge Extraction

* Verse-level parsing
* Translation handling
* Commentary separation
* Principle extraction
* Philosophical tagging
* Emotional tagging

### Dataset Generation

* Training example creation
* Dataset quality validation
* Duplicate detection
* Response diversity checks
* Fine-tuning dataset export

### Quality Assurance

* OCR corruption detection
* Metadata leakage prevention
* Principle quality scoring
* Training example auditing
* Export gating

---

## Technology Stack

### Backend

* FastAPI
* Python 3.11+
* SQLAlchemy
* Alembic
* Pydantic v2

### Database

* SQLite (development)
* PostgreSQL (production-ready)

### AI Roadmap

* Qwen 2.5
* Local LLMs
* LoRA Fine-Tuning
* MLX-LM
* RAG
* Vector Search

---

## Project Structure

```text
app/
├── core/
├── models/
├── schemas/
├── routers/
├── services/
├── pipelines/
├── utils/

scripts/
├── ingestion
├── inspection
├── auditing
├── dataset generation
└── export

storage/
├── source_documents
├── exports
└── generated_data
```

---

## Development Status

Current Stage:

* Document ingestion ✓
* Canonical verse extraction ✓
* Wisdom entry generation ✓
* Principle extraction ✓
* Dataset auditing ✓
* JSONL export ✓

In Progress:

* Dataset quality refinement
* Training corpus expansion

Planned:

* Multi-book support
* Semantic retrieval
* RAG layer
* Local model serving
* Fine-tuning pipeline
* Production deployment

---

## Long-Term Goal

Build a trustworthy AI guidance system that combines modern AI engineering with the philosophical depth of Indian wisdom traditions, helping users gain clarity, perspective, and practical direction during life's internal struggles.

---

## Disclaimer

Marg Darshak is intended as a philosophical guidance system.

It is not a replacement for professional medical, psychological, legal, or financial advice.
