"""
Test script pentru verificare server
"""
import sys
import os

# Adaugă directorul backend la path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testează toate importurile"""
    print("[*] Testare importuri...")
    
    try:
        from app.main import app
        print("[OK] app.main importat")
        
        from app.api.routes import wishes, business_plans, mvp
        print("[OK] app.api.routes importat")
        
        from app.api.models import HealthResponse
        print("[OK] app.api.models importat")
        
        from app.wishcatcher.scraper.context_collector import ContextCollector
        print("[OK] ContextCollector importat")
        
        from app.wishcatcher.parser.robust_intent_detector import RobustIntentDetector
        print("[OK] RobustIntentDetector importat")
        
        from app.wishcatcher.trigger_analyzer.trigger_analyzer import TriggerAnalyzer
        print("[OK] TriggerAnalyzer importat")
        
        from app.wishcatcher.clusterer.complementarity_detector import ComplementarityDetector
        print("[OK] ComplementarityDetector importat")
        
        from app.wishcatcher.scorer.business_scorer import BusinessScorer
        print("[OK] BusinessScorer importat")
        
        from app.astra_genesis.business_plan.business_plan_generator import BusinessPlanGenerator
        print("[OK] BusinessPlanGenerator importat")
        
        from app.astra_genesis.mvp_generator.mvp_structure_generator import MVPStructureGenerator
        print("[OK] MVPStructureGenerator importat")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Eroare import: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Testează crearea aplicației"""
    print("\n[*] Testare creare aplicatie...")
    
    try:
        from app.main import app
        print(f"[OK] Aplicatie creata cu {len(app.routes)} rute")
        print(f"[OK] Titlu: {app.title}")
        return True
    except Exception as e:
        print(f"[ERROR] Eroare creare aplicatie: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Test Server - WishCatcher + Astra Genesis")
    print("=" * 60)
    
    success = True
    
    # Test importuri
    if not test_imports():
        success = False
    
    # Test creare aplicatie
    if not test_app_creation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] TOATE TESTELE AU TRECUT!")
        print("\n[INFO] Poti porni serverul cu:")
        print("  uvicorn app.main:app --reload")
        return 0
    else:
        print("[ERROR] TESTELE AU ESUAT!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
