"""
Script de verificare setup backend
"""
import sys
import os

def check_imports():
    """Verifică dacă toate importurile funcționează"""
    print("[*] Verificare importuri...")
    errors = []
    
    try:
        import fastapi
        print("[OK] FastAPI")
    except ImportError as e:
        errors.append(f"[ERROR] FastAPI: {e}")
    
    try:
        import uvicorn
        print("[OK] Uvicorn")
    except ImportError as e:
        errors.append(f"[ERROR] Uvicorn: {e}")
    
    try:
        import spacy
        print("[OK] spaCy")
    except ImportError as e:
        errors.append(f"[ERROR] spaCy: {e}")
    
    try:
        import sklearn
        print("[OK] scikit-learn")
    except ImportError as e:
        errors.append(f"[ERROR] scikit-learn: {e}")
    
    try:
        import requests
        print("[OK] requests")
    except ImportError as e:
        errors.append(f"[ERROR] requests: {e}")
    
    try:
        import aiohttp
        print("[OK] aiohttp")
    except ImportError as e:
        errors.append(f"[ERROR] aiohttp: {e}")
    
    try:
        import bs4
        print("[OK] beautifulsoup4 (bs4)")
    except ImportError as e:
        errors.append(f"[ERROR] beautifulsoup4: {e}")
    
    try:
        import praw
        print("[OK] praw")
    except ImportError as e:
        errors.append(f"[ERROR] praw: {e}")
    
    return errors

def check_spacy_models():
    """Verifică dacă modelele spaCy sunt instalate"""
    print("\n[*] Verificare modele spaCy...")
    errors = []
    
    try:
        import spacy
        try:
            nlp = spacy.load('en_core_web_sm')
            print("[OK] en_core_web_sm (English)")
        except OSError:
            errors.append("[ERROR] en_core_web_sm - Ruleaza: python -m spacy download en_core_web_sm")
        
        try:
            nlp = spacy.load('ro_core_news_sm')
            print("[OK] ro_core_news_sm (Romanian)")
        except OSError:
            errors.append("[ERROR] ro_core_news_sm - Ruleaza: python -m spacy download ro_core_news_sm")
    except ImportError:
        errors.append("[ERROR] spaCy nu este instalat")
    
    return errors

def check_app_imports():
    """Verifică dacă aplicația poate fi importată"""
    print("\n[*] Verificare import aplicatie...")
    errors = []
    
    # Adaugă directorul curent la path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        import app.main
        print("[OK] app.main")
    except Exception as e:
        errors.append(f"[ERROR] app.main: {e}")
    
    try:
        from app.api.routes import wishes, business_plans, mvp
        print("[OK] app.api.routes")
    except Exception as e:
        errors.append(f"[ERROR] app.api.routes: {e}")
    
    try:
        from app.api.models import HealthResponse
        print("[OK] app.api.models")
    except Exception as e:
        errors.append(f"[ERROR] app.api.models: {e}")
    
    return errors

def main():
    print("=" * 60)
    print("Verificare Setup Backend - WishCatcher + Astra Genesis")
    print("=" * 60)
    
    all_errors = []
    
    # Verifică importuri
    errors = check_imports()
    all_errors.extend(errors)
    
    # Verifică modele spaCy
    errors = check_spacy_models()
    all_errors.extend(errors)
    
    # Verifică import aplicație
    errors = check_app_imports()
    all_errors.extend(errors)
    
    print("\n" + "=" * 60)
    if all_errors:
        print("[ERROR] PROBLEME GASITE:")
        for error in all_errors:
            print(f"  {error}")
        print("\n[INFO] SOLUTII:")
        print("  1. Instaleaza dependente: pip install -r requirements.txt")
        print("  2. Descarca modele spaCy:")
        print("     python -m spacy download en_core_web_sm")
        print("     python -m spacy download ro_core_news_sm")
        print("  3. Verifica ca esti in directorul backend")
        return 1
    else:
        print("[OK] TOATE VERIFICARILE AU TRECUT!")
        print("\n[INFO] Poti porni backend-ul cu:")
        print("   uvicorn app.main:app --reload")
        return 0

if __name__ == "__main__":
    sys.exit(main())
