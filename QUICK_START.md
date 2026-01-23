# Quick Start Guide - WishCatcher + Astra Genesis

## 🚀 Start Rapid

### 1. Backend Setup (Terminal 1)

```bash
# Navighează la backend
cd backend

# Creează virtual environment
python -m venv venv

# Activează virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalează dependențe
pip install -r requirements.txt

# Download spaCy models
python -m spacy download ro_core_news_sm
python -m spacy download en_core_web_sm

# Rulează backend
uvicorn app.main:app --reload
```

Backend-ul va rula pe `http://localhost:8000`

### 2. Frontend Setup (Terminal 2)

```bash
# Navighează la frontend
cd frontend

# Instalează dependențe
npm install

# Creează .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Rulează frontend
npm run dev
```

Frontend-ul va rula pe `http://localhost:3000`

## 🎯 Utilizare

### 1. Deschide Browser
- Accesează `http://localhost:3000`

### 2. Colectează Wish-uri
- Selectează surse (Reddit, Quora, etc.)
- Setează filtre (geografie, limbă, domeniu)
- Apasă "Colectează Wish-uri"

### 3. Generează Business Plan
- Click pe un wish
- Apasă "Generează Business Plan"
- Vezi business plan complet

### 4. Generează MVP
- După business plan
- Apasă "Generează MVP"
- Download MVP structure

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Colectează Wish-uri
```bash
curl -X POST http://localhost:8000/api/wishes/collect \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["reddit"],
    "filters": {"geography": {"level": "uk"}},
    "limit": 50
  }'
```

### Generează Business Plan
```bash
curl -X POST http://localhost:8000/api/business-plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "wish_id": "wish_123",
    "include_mvp": true
  }'
```

## 🔧 Troubleshooting

### Backend nu pornește
- Verifică că Python 3.9+ e instalat
- Verifică că virtual environment e activat
- Verifică că toate dependențele sunt instalate

### Frontend nu pornește
- Verifică că Node.js 18+ e instalat
- Verifică că `npm install` a rulat cu succes
- Verifică că `.env.local` există

### spaCy models nu se descarcă
```bash
python -m spacy download ro_core_news_sm --user
python -m spacy download en_core_web_sm --user
```

### Import errors
- Verifică că ești în virtual environment
- Verifică că ai rulat `pip install -r requirements.txt`

## 📚 Documentație Completă

- [Setup Guide](docs/setup.md)
- [Usage Guide](docs/usage.md)
- [Examples](docs/examples.md)

## 🎉 Gata!

Aplicația e gata de utilizare! 🚀
