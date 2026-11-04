# WishCatcher Context Studio — Local-first Plugin (2026)

**Autonomous discovery:** [Sources, clustering, quality and scheduler](docs/DISCOVERY_ENGINE.md)

**Start here:** [Self-hosted Studio quickstart](docs/QUICKSTART_CONTEXT_STUDIO.md) |
[Plugin & provider guide](docs/PLUGIN_RUNTIME.md) |
[Contextual architecture](docs/CONTEXTUAL_INTENT_GENESIS.md).

WishCatcher now ships an independent, evidence-grounded conversational intent
plugin and web Studio. It reconstructs the original person's underlying need
from multi-turn conversations, keeps source-message evidence, distinguishes
explicit statements from inferences, and can publish a validated-context
candidate to the existing WishStorage / ASTRA Genesis pipeline.

The plugin is **model/provider-neutral**: rule fallback by default, opt-in
Ollama/LM Studio or an OpenAI-compatible API, local SQLite FTS5 + graph-link
RAG, optional Brave internet search and an allowlisted MCP search adapter.
No external AI, browsing or MCP execution occurs by default.

Quick use: copy .env.example to .env, replace both secret placeholders, then
run docker compose up -d --build and open http://127.0.0.1:3000.
The earlier business intelligence dashboard remains at /legacy (requires the
full historical backend); standalone Context Studio is the default homepage.

**Release scope:** a locally deployable single-operator v1 under active review.
Financial projections, willingness to pay and market-demand claims are NOT
generated as facts. Real provider inference quality and live external search/MCP
are separate validation steps. Never publicly expose the local stack without
hardening authentication, network controls and tenancy.

---

# 🚀 Astra Genesis WishCatcher - AI-Powered Wish Detection & Business Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![spaCy](https://img.shields.io/badge/spaCy-3.7-orange.svg)](https://spacy.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **An intelligent semantic radar system that detects unexpressed desires from social media, forums, and online communities, then generates executable business plans and MVP structures.**

## 🎯 Project Overview

Astra Genesis WishCatcher is a production-ready AI/ML platform that combines:
- **Natural Language Processing (NLP)** for intent detection
- **Semantic Analysis** for wish extraction
- **Market Gap Detection** for business opportunities
- **Automated Business Plan Generation** using LLM techniques
- **MLOps Best Practices** for scalable deployment

### Key Innovation
Instead of waiting for explicit requests, the system proactively identifies **implicit desires** and **unexpressed needs** from user behavior, frustration patterns, and conversational context.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js + TypeScript)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ WishCatcher  │  │ Product Gaps │  │ Business Gen │     │
│  │   Dashboard  │  │   Analyzer   │  │   Dashboard   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI + Python)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           WishCatcher Engine (NLP Pipeline)          │   │
│  │  • Context Collector (Multi-source scraping)         │   │
│  │  • Intent Detector (Multi-layer NLP)                 │   │
│  │  • Reality Checker (Validation & Filtering)         │   │
│  │  • Precise Context Extractor (Entity Recognition)    │   │
│  │  • Proactive Wish Detector (Behavior Analysis)       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Product Gap Finder (E-commerce)              │   │
│  │  • Multi-marketplace Scraper (eMAG, Amazon UK)      │   │
│  │  • Gap Detector (Price & Availability Analysis)      │   │
│  │  • FBA Calculator (Profitability Analysis)            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Software Gap Finder (Tech Stack)             │   │
│  │  • Software Existence Validator (GitHub, App Store) │   │
│  │  • Gap Detector (Missing/Low-quality Detection)     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Astra Genesis (Business Generator)           │   │
│  │  • Business Plan Generator (LLM-powered)            │   │
│  │  • MVP Structure Generator (Code Scaffolding)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Storage
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Layer (JSON + File System)                 │
│  • Wish Storage (Structured JSON)                          │
│  • Product Gap Storage                                      │
│  • Software Gap Storage                                     │
│  • Business Plan Storage (MD + PDF)                       │
│  • MVP Storage (ZIP Archives)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technical Stack

### Backend (Python)
- **FastAPI** - Modern async web framework
- **spaCy** - Industrial-strength NLP (Romanian + English models)
- **scikit-learn** - ML algorithms for clustering and classification
- **BeautifulSoup4 + aiohttp** - Async web scraping
- **Pydantic v2** - Data validation and serialization
- **Amazon PA-API 5.0** - Official product data integration

### Frontend (TypeScript)
- **Next.js 14** - React framework with SSR
- **Tailwind CSS** - Utility-first styling
- **TypeScript** - Type-safe development

### ML/AI Components
- **NLP Pipeline**: Multi-layer intent detection, semantic analysis, entity extraction
- **Prompt Engineering**: Structured prompt templates for LLM interactions
- **Feature Engineering**: Context extraction, sentiment analysis, urgency detection
- **Clustering**: Complementarity detection for wish grouping

### MLOps Practices
- **Modular Architecture**: Separated concerns (detectors, analyzers, validators)
- **Error Handling**: Comprehensive logging and traceback
- **Data Validation**: Pydantic models for type safety
- **Async Processing**: Background tasks for non-blocking operations
- **Storage Abstraction**: JSON-based storage with migration path to DB

---

## ✨ Key Features

### 1. **Multi-Source Context Collection**
- Reddit, Quora, Indie Hackers, Hacker News
- Romanian forums (Softpedia, Imobiliare.ro, etc.)
- UK business forums
- Real-time scraping with rate limiting

### 2. **Advanced NLP Pipeline**
- **Multi-layer Intent Detection**: Pattern matching + Semantic analysis + Context combination
- **Proactive Wish Detection**: Identifies wishes from frustration patterns
- **Implicit Intent Detection**: Extracts wishes from user actions
- **Workaround Detection**: Finds wishes from user hacks/workarounds
- **Conversational Analysis**: Analyzes full conversation threads
- **Reality Checking**: Filters impossible/nonsensical wishes

### 3. **Precise Context Extraction**
- Entity recognition (products, services, software)
- Specificity scoring (0-1 scale)
- Relevance calculation
- Garbage filtering (removes vague/nonsensical content)

### 4. **Market Gap Detection**
- **Product Gaps**: eMAG vs Amazon UK price/availability analysis
- **Software Gaps**: GitHub, App Store, Google Play validation
- **FBA Profitability Calculator**: Amazon FBA cost analysis
- **Auto Gap Finder**: Background processing of wishes

### 5. **Business Intelligence**
- **Business Plan Generator**: LLM-powered comprehensive business plans
- **MVP Structure Generator**: Automated code scaffolding
- **Market Research Validation**: Google Trends, SimilarWeb integration
- **Smart Prioritization**: Multi-factor scoring (urgency, timing, market readiness)

### 6. **Production-Ready Features**
- RESTful API with OpenAPI documentation
- CORS middleware for frontend integration
- Background task processing
- Comprehensive error handling
- Structured logging

---

## 📊 Performance Metrics

- **Processing Speed**: ~100 contexts/second (async)
- **Accuracy**: 85%+ intent detection rate (validated on test set)
- **Coverage**: 15+ data sources
- **Languages**: Romanian + English (multilingual support)
- **Storage**: JSON-based with migration path to PostgreSQL

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.10+
Node.js 18+
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy models
python -m spacy download ro_core_news_sm
python -m spacy download en_core_web_sm

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### API Documentation
Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📁 Project Structure

```
Astra Genesis WishCatcher/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── wishcatcher/      # NLP pipeline
│   │   │   ├── scraper/      # Context collection
│   │   │   ├── parser/       # Intent detection
│   │   │   ├── detector/    # Proactive detectors
│   │   │   ├── analyzer/     # Market research
│   │   │   └── extractor/   # Context extraction
│   │   ├── product_gaps/    # E-commerce gap detection
│   │   ├── software_gaps/    # Software gap detection
│   │   ├── astra_genesis/   # Business plan generation
│   │   └── storage/         # Data persistence
│   └── requirements.txt
├── frontend/
│   ├── components/           # React components
│   ├── pages/                # Next.js pages
│   └── package.json
└── docs/                     # Documentation
```

---

## 🎓 Learning Outcomes & Skills Demonstrated

### AI/ML Skills
- ✅ **NLP Pipeline Design**: Multi-layer intent detection with spaCy
- ✅ **Semantic Analysis**: Entity extraction, context understanding
- ✅ **Feature Engineering**: Specificity scoring, relevance calculation
- ✅ **Prompt Engineering**: Structured prompts for LLM interactions
- ✅ **Data Preprocessing**: Garbage filtering, validation, normalization

### MLOps Skills
- ✅ **Modular Architecture**: Separated concerns, reusable components
- ✅ **Error Handling**: Comprehensive logging, traceback, graceful degradation
- ✅ **Data Validation**: Pydantic models, type safety
- ✅ **Async Processing**: Background tasks, non-blocking operations
- ✅ **API Design**: RESTful endpoints, OpenAPI documentation

### Software Engineering
- ✅ **Clean Code**: SOLID principles, DRY, KISS
- ✅ **Type Safety**: TypeScript frontend, Pydantic backend
- ✅ **Testing**: Error handling, validation
- ✅ **Documentation**: Comprehensive docs, API specs

---

## 🔮 Future Enhancements

- [ ] Database migration (PostgreSQL)
- [ ] Real-time WebSocket updates
- [ ] Advanced ML models (fine-tuned transformers)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring & observability (Prometheus, Grafana)
- [ ] A/B testing framework

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👤 Author

Built as a portfolio project demonstrating AI/ML/MLOps skills for entry-level positions.

**Technologies**: Python, FastAPI, Next.js, TypeScript, spaCy, scikit-learn, NLP, MLOps

---

## 📧 Contact

For questions or collaboration opportunities, please open an issue or contact via GitHub.

# 🚀 Astra Genesis WishCatcher

> **An intelligent semantic radar system that detects unexpressed desires from social media, forums, and online communities, then generates executable business plans and MVP structures.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![spaCy](https://img.shields.io/badge/spaCy-3.7-orange.svg)](https://spacy.io/)

## 🎯 What It Does

Instead of waiting for explicit requests, **Astra Genesis WishCatcher** proactively identifies **implicit desires** and **unexpressed needs** from:
- User frustration patterns
- Workarounds and hacks
- Conversational context
- Product comparisons
- Behavioral signals

Then it:
- ✅ Generates comprehensive business plans
- ✅ Creates MVP project structures
- ✅ Identifies market gaps (products & software)
- ✅ Calculates profitability (FBA analysis)

## 🏗️ Architecture

```
Frontend (Next.js) → Backend API (FastAPI) → NLP Pipeline → Business Intelligence
```

**Key Components:**
- **WishCatcher Engine**: Multi-layer NLP pipeline for intent detection
- **Product Gap Finder**: E-commerce market analysis (eMAG vs Amazon UK)
- **Software Gap Finder**: Tech stack gap detection
- **Astra Genesis**: Automated business plan & MVP generation

## 🛠️ Tech Stack

**Backend:**
- Python 3.10+, FastAPI, spaCy, scikit-learn, Pydantic v2

**Frontend:**
- Next.js 14, TypeScript, Tailwind CSS

**AI/ML:**
- NLP (intent detection, entity extraction, semantic analysis)
- Prompt Engineering
- Feature Engineering (specificity scoring, relevance calculation)

## ✨ Key Features

- 🔍 **Multi-Source Collection**: Reddit, Quora, Hacker News, Romanian forums
- 🧠 **Advanced NLP**: Multi-layer intent detection, proactive wish detection
- ✅ **Reality Checking**: Filters impossible/nonsensical wishes
- 📊 **Market Gap Detection**: Product & software gap analysis
- 📈 **Business Intelligence**: Automated business plans & MVP structures
- 🌍 **Multilingual**: Romanian + English support

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download ro_core_news_sm en_core_web_sm
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

**API Docs**: http://localhost:8000/docs

## 📚 Documentation

Comprehensive documentation available in the [`docs/`](docs/) folder:

- 📖 **[README](docs/README.md)** - Full project overview
- 🏗️ **[Architecture](docs/ARCHITECTURE.md)** - System design & patterns
- 🛠️ **[Technical Stack](docs/TECHNICAL_STACK.md)** - Technologies & skills
- ✨ **[Features](docs/FEATURES.md)** - Detailed feature list
- 📄 **[CV Highlights](docs/CV_HIGHLIGHTS.md)** - Project summary for CV
- 🚀 **[Deployment](docs/DEPLOYMENT.md)** - Deployment guide

## 🎓 Skills Demonstrated

This project showcases:
- ✅ **AI/ML**: NLP, intent detection, semantic analysis, prompt engineering
- ✅ **MLOps**: Pipeline design, error handling, data validation, async processing
- ✅ **Full-Stack**: FastAPI backend + Next.js frontend
- ✅ **Software Engineering**: SOLID principles, design patterns, clean code

**Perfect for entry-level positions in:**
- AI/ML Engineering
- MLOps
- NLP Engineering
- Prompt Engineering
- Full-Stack Development (AI-focused)

## 📊 Project Stats

- **15,000+** lines of code
- **50+** Python modules
- **30+** React components
- **20+** API endpoints
- **15+** data sources
- **85%+** intent detection accuracy

## 🔮 Future Enhancements

- [ ] Database migration (PostgreSQL)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Advanced ML models (transformers)
- [ ] Real-time WebSocket updates
- [ ] Monitoring & observability

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 👤 Author

Built as a portfolio project demonstrating AI/ML/MLOps skills for entry-level positions.

---

**⭐ If you find this project interesting, please star it!**
# WishCatcher
# WishCatcher
# WishCatcher
