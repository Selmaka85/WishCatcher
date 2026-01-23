#!/bin/bash
# Script de pornire backend pentru Linux/Mac

echo "========================================"
echo "Starting WishCatcher Backend Server"
echo "========================================"
echo ""

# Verifică dacă ești în directorul corect
if [ ! -f "app/main.py" ]; then
    echo "ERROR: Nu esti in directorul backend!"
    echo "Navigheaza la: cd backend"
    exit 1
fi

# Pornește serverul
echo "Starting FastAPI server on http://localhost:8000"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
