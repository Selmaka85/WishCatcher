"""
Test rapid pentru importuri și naming
"""

import sys

def test_imports():
    """Testează toate importurile critice"""
    errors = []
    
    try:
        from app.main import app
        print("✓ Main app import OK")
    except Exception as e:
        errors.append(f"Main app: {e}")
    
    try:
        from app.api.routes import wishes, business_plans, mvp
        print("✓ Routes imports OK")
    except Exception as e:
        errors.append(f"Routes: {e}")
    
    try:
        from app.api.models import (
            WishData, WishRequest, WishResponse,
            BusinessPlanRequest, BusinessPlanResponse,
            MVPRequest, MVPResponse,
            ComplementarityRequest, ComplementarityResponse
        )
        print("✓ Models imports OK")
    except Exception as e:
        errors.append(f"Models: {e}")
    
    try:
        from app.wishcatcher.parser.robust_intent_detector import RobustIntentDetector
        print("✓ RobustIntentDetector import OK")
    except Exception as e:
        errors.append(f"RobustIntentDetector: {e}")
    
    try:
        from app.wishcatcher.trigger_analyzer.trigger_analyzer import TriggerAnalyzer
        print("✓ TriggerAnalyzer import OK")
    except Exception as e:
        errors.append(f"TriggerAnalyzer: {e}")
    
    try:
        from app.wishcatcher.clusterer.complementarity_detector import ComplementarityDetector
        print("✓ ComplementarityDetector import OK")
    except Exception as e:
        errors.append(f"ComplementarityDetector: {e}")
    
    try:
        from app.wishcatcher.scorer.business_scorer import BusinessScorer
        print("✓ BusinessScorer import OK")
    except Exception as e:
        errors.append(f"BusinessScorer: {e}")
    
    try:
        from app.astra_genesis.business_plan.business_plan_generator import BusinessPlanGenerator
        print("✓ BusinessPlanGenerator import OK")
    except Exception as e:
        errors.append(f"BusinessPlanGenerator: {e}")
    
    try:
        from app.astra_genesis.mvp_generator.mvp_structure_generator import MVPStructureGenerator
        print("✓ MVPStructureGenerator import OK")
    except Exception as e:
        errors.append(f"MVPStructureGenerator: {e}")
    
    try:
        from app.wishcatcher.scraper.context_collector import ContextCollector
        print("✓ ContextCollector import OK")
    except Exception as e:
        errors.append(f"ContextCollector: {e}")
    
    if errors:
        print("\nERORI:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\nTOATE IMPORTURILE OK!")
        return True

def test_naming():
    """Testează naming conventions"""
    import inspect
    
    issues = []
    
    # Test classes (PascalCase)
    from app.wishcatcher.parser.robust_intent_detector import RobustIntentDetector
    from app.astra_genesis.business_plan.business_plan_generator import BusinessPlanGenerator
    
    classes = [
        RobustIntentDetector,
        BusinessPlanGenerator,
    ]
    
    for cls in classes:
        if not cls.__name__[0].isupper():
            issues.append(f"Class {cls.__name__} nu începe cu majusculă")
        if '_' in cls.__name__ and not cls.__name__.startswith('_'):
            # Allow _ for private classes
            pass
    
    # Test functions (snake_case)
    methods = inspect.getmembers(RobustIntentDetector, predicate=inspect.isfunction)
    for name, _ in methods:
        if not name.startswith('_') and not name.replace('_', '').islower():
            issues.append(f"Method {name} nu respectă snake_case")
    
    if issues:
        print("\nNAMING ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\nNAMING CONVENTIONS OK!")
        return True

if __name__ == "__main__":
    import sys
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 50)
    print("TEST IMPORTURI SI NAMING")
    print("=" * 50)
    
    imports_ok = test_imports()
    naming_ok = test_naming()
    
    print("\n" + "=" * 50)
    if imports_ok and naming_ok:
        print("TOATE TESTELE PASSED!")
        sys.exit(0)
    else:
        print("EXISTA PROBLEME!")
        sys.exit(1)
