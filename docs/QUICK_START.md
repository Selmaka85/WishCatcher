# ⚡ Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- pip (Python package manager)
- npm (Node package manager)

## Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd "Astra Genesis WishCatcher"
```

## Step 2: Backend Setup

### Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Download spaCy Models

```bash
python -m spacy download ro_core_news_sm
python -m spacy download en_core_web_sm
```

### Run Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Step 3: Frontend Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Frontend

```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## Step 4: Verify Installation

1. **Backend Health Check:**
   - Visit: http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

2. **Frontend:**
   - Visit: http://localhost:3000
   - Should see the dashboard

3. **API Test:**
   - Visit: http://localhost:8000/docs
   - Try the `/api/wishes/collect` endpoint

## Common Issues

### Issue: spaCy models not found

**Solution:**
```bash
python -m spacy download ro_core_news_sm
python -m spacy download en_core_web_sm
```

### Issue: Port already in use

**Solution:**
Change port in command:
```bash
uvicorn app.main:app --reload --port 8001
```

### Issue: Import errors

**Solution:**
Ensure you're in the correct directory:
```bash
cd backend
python -m app.main
```

### Issue: CORS errors

**Solution:**
Check that frontend URL matches `ALLOWED_ORIGINS` in backend:
- Default: `http://localhost:3000`

## Next Steps

1. **Read Documentation:**
   - [Full README](README.md)
   - [Architecture](ARCHITECTURE.md)
   - [Features](FEATURES.md)

2. **Try Features:**
   - Collect wishes from Reddit/Quora
   - Generate business plans
   - Find product gaps
   - Generate MVP structures

3. **Explore Code:**
   - Backend: `backend/app/`
   - Frontend: `frontend/components/`
   - Documentation: `docs/`

## Development Tips

### Backend Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Development

```bash
# Development mode (with hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Testing API

Use the interactive Swagger UI:
1. Visit: http://localhost:8000/docs
2. Click on an endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

## Environment Variables (Optional)

Create `.env` file in `backend/`:

```env
# Amazon PA-API (optional)
AMAZON_ACCESS_KEY=your_key
AMAZON_SECRET_KEY=your_secret
AMAZON_PARTNER_TAG=your_tag

# CORS (optional)
ALLOWED_ORIGINS=http://localhost:3000
```

## Need Help?

- Check [Documentation](README.md)
- Review [Architecture](ARCHITECTURE.md)
- See [Troubleshooting](DEPLOYMENT.md#troubleshooting)

---

**Happy Coding! 🚀**
