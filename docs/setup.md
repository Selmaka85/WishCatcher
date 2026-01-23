# Setup Guide - WishCatcher + Astra Genesis

## 📋 Cerințe

- Python 3.9+
- Node.js 18+ (pentru frontend)
- pip
- npm sau yarn

## 🚀 Instalare Backend

### 1. Clone repository (sau creează folder)

```bash
mkdir wishcatcher
cd wishcatcher
```

### 2. Creează virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalează dependențe

```bash
pip install -r requirements.txt
```

### 4. Download spaCy models

```bash
# Romanian model
python -m spacy download ro_core_news_sm

# English model
python -m spacy download en_core_web_sm
```

### 5. Configurează environment variables

Creează `.env` în root:

```env
# Reddit API (opțional - pentru rate limits mai mari)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=WishCatcher/1.0

# Database (opțional - SQLite by default)
DATABASE_URL=sqlite:///./wishcatcher.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### 6. Rulează backend

```bash
cd backend
uvicorn app.main:app --reload
```

Backend-ul va rula pe `http://localhost:8000`

## 🎨 Instalare Frontend

### 1. Navighează la frontend

```bash
cd frontend
```

### 2. Instalează dependențe

```bash
npm install
# sau
yarn install
```

### 3. Configurează environment

Creează `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Rulează frontend

```bash
npm run dev
# sau
yarn dev
```

Frontend-ul va rula pe `http://localhost:3000`

## ✅ Verificare

### Test Backend

```bash
curl http://localhost:8000/health
```

Ar trebui să returneze:
```json
{"status": "healthy"}
```

### Test Frontend

Deschide `http://localhost:3000` în browser.

## 🔧 Troubleshooting

### Problema: spaCy models nu se descarcă

**Soluție:**
```bash
python -m spacy download ro_core_news_sm --user
python -m spacy download en_core_web_sm --user
```

### Problema: Port deja folosit

**Soluție:**
Schimbă portul în `.env` sau în command:
```bash
uvicorn app.main:app --port 8001
```

### Problema: Module not found

**Soluție:**
Asigură-te că ești în virtual environment și că ai instalat toate dependențele:
```bash
pip install -r requirements.txt
```

## 📚 Next Steps

După setup, vezi:
- [Usage Guide](usage.md)
- [Examples](examples.md)
