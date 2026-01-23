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
