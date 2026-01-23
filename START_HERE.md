# 🚀 START HERE - WishCatcher + Astra Genesis

## ⚠️ PROBLEMA PRINCIPALĂ

Eroarea `ERR_CONNECTION_REFUSED` pe portul 8000 înseamnă că **backend-ul nu rulează**.

Frontend-ul (portul 3000) încearcă să se conecteze la backend (portul 8000), dar backend-ul nu este pornit.

## ✅ SOLUȚIE - Pornește Backend-ul

### Opțiunea 1: Folosind script-ul automat (Windows)

```bash
cd backend
start_backend.bat
```

### Opțiunea 2: Manual (Windows/Linux/Mac)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

Ar trebui să vezi:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Opțiunea 3: Folosind Python direct

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## ✅ Pornește Frontend-ul (Terminal 2)

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Ar trebui să vezi:
```
- ready started server on 0.0.0.0:3000
- Local:        http://localhost:3000
```

## 🔍 Verificare Setup

### Verifică Backend Setup

```bash
cd backend
python check_setup.py
```

Ar trebui să vezi: `[OK] TOATE VERIFICARILE AU TRECUT!`

### Verifică că Backend Rulează

Deschide în browser: `http://localhost:8000/health`

Ar trebui să vezi: `{"status":"healthy"}`

### Verifică că Frontend Rulează

Deschide în browser: `http://localhost:3000`

Ar trebui să vezi dashboard-ul WishCatcher.

## 📋 Checklist Complet

- [ ] Backend dependencies instalate: `pip install -r requirements.txt`
- [ ] spaCy models instalate: `python -m spacy download en_core_web_sm` și `python -m spacy download ro_core_news_sm`
- [ ] Frontend dependencies instalate: `cd frontend && npm install`
- [ ] Backend rulează pe portul 8000
- [ ] Frontend rulează pe portul 3000
- [ ] Backend health check funcționează: `http://localhost:8000/health`

## 🐛 Troubleshooting

### Backend nu pornește

1. **Verifică că ești în directorul corect:**
   ```bash
   cd backend
   ```

2. **Verifică setup-ul:**
   ```bash
   python check_setup.py
   ```

3. **Verifică că portul 8000 nu este deja folosit:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

4. **Dacă portul este ocupat, schimbă portul:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
   Apoi actualizează `frontend/lib/api.ts` cu noul port.

### Frontend nu se conectează la Backend

1. **Verifică că backend-ul rulează:**
   - Deschide `http://localhost:8000/health` în browser

2. **Verifică configurația frontend:**
   - Fișierul `frontend/.env.local` trebuie să conțină:
     ```
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```

3. **Verifică CORS:**
   - În `backend/app/main.py`, asigură-te că:
     ```python
     allow_origins=["http://localhost:3000"]
     ```

### Module not found errors

1. **Reinstalează dependențele:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

2. **Verifică virtual environment (backend):**
   ```bash
   # Creează virtual environment
   python -m venv venv
   
   # Activează (Windows)
   venv\Scripts\activate
   
   # Activează (Linux/Mac)
   source venv/bin/activate
   
   # Instalează dependențe
   pip install -r requirements.txt
   ```

## 📞 Ordinea Corectă de Pornire

1. **Pornește Backend PRIMUL** (Terminal 1)
2. **Așteaptă să vezi mesajul "Application startup complete"**
3. **Pornește Frontend** (Terminal 2)
4. **Deschide browser la** `http://localhost:3000`

## 🎯 Test Rapid

După ce ambele servicii rulează:

1. Deschide `http://localhost:3000`
2. Selectează o sursă (ex: Reddit)
3. Apasă "Colectează Wish-uri"
4. Ar trebui să vezi rezultate (sau mesaje de eroare dacă nu există date)

---

**IMPORTANT:** Backend-ul TREBUIE să ruleze înainte de frontend pentru ca aplicația să funcționeze!
