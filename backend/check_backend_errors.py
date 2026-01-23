"""
Script pentru verificare erori backend
"""

import sys
import os
import traceback
from pathlib import Path

# Adaugă backend la path
sys.path.insert(0, str(Path(__file__).parent))

errors = []
warnings = []

def check_imports():
    """Verifică toate importurile critice"""
    print("\n[*] Verificare importuri...")
    
    modules_to_check = [
        ("app.main", "app"),
        ("app.api.routes.wishes", "wishes router"),
        ("app.api.routes.software_gaps", "software_gaps router"),
        ("app.api.routes.product_gaps", "product_gaps router"),
        ("app.api.models", "models"),
        ("app.wishcatcher.parser.robust_intent_detector", "RobustIntentDetector"),
        ("app.wishcatcher.extractor.precise_context_extractor", "PreciseContextExtractor"),
        ("app.software_gaps.software_gap_finder", "SoftwareGapFinder"),
        ("app.software_gaps.validator.software_existence_validator", "SoftwareExistenceValidator"),
        ("app.software_gaps.detector.software_gap_detector", "SoftwareGapDetector"),
        ("app.software_gaps.storage.software_gap_storage", "SoftwareGapStorage"),
    ]
    
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"  [OK] {description}")
        except Exception as e:
            error_msg = f"  [ERROR] {description}: {e}"
            print(error_msg)
            errors.append(error_msg)
            traceback.print_exc()

def check_syntax():
    """Verifică sintaxa fișierelor Python"""
    print("\n[*] Verificare sintaxă...")
    
    import py_compile
    
    python_files = []
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"  [OK] {file_path}")
        except py_compile.PyCompileError as e:
            error_msg = f"  [ERROR] {file_path}: {e}"
            print(error_msg)
            errors.append(error_msg)

def check_duplicate_imports():
    """Verifică importuri duplicate"""
    print("\n[*] Verificare importuri duplicate...")
    
    main_file = Path("app/main.py")
    if main_file.exists():
        content = main_file.read_text(encoding='utf-8')
        imports = [line.strip() for line in content.split('\n') if line.strip().startswith('from app.api.routes import')]
        
        for import_line in imports:
            # Extrage modulele importate
            modules = import_line.split('import')[1].strip().split(',')
            modules = [m.strip() for m in modules]
            
            # Verifică duplicate
            seen = set()
            for module in modules:
                if module in seen:
                    error_msg = f"  ✗ Duplicate import in main.py: {module}"
                    print(error_msg)
                    errors.append(error_msg)
                seen.add(module)

def check_missing_fields():
    """Verifică câmpuri lipsă în storage"""
    print("\n[*] Verificare câmpuri storage...")
    
    wish_storage_file = Path("app/storage/wish_storage.py")
    if wish_storage_file.exists():
        content = wish_storage_file.read_text(encoding='utf-8')
        
        # Verifică dacă _wish_to_dict include toate câmpurile noi
        required_fields = [
            "priority_score",
            "urgency",
            "timing",
            "market_readiness",
            "market_validation"
        ]
        
        for field in required_fields:
            if f'"{field}"' not in content and f"'{field}'" not in content:
                warning_msg = f"  [WARNING] Field '{field}' might not be saved in _wish_to_dict"
                print(warning_msg)
                warnings.append(warning_msg)

def main():
    print("=" * 60)
    print("VERIFICARE BACKEND - Erori si Probleme")
    print("=" * 60)
    
    check_imports()
    check_duplicate_imports()
    check_missing_fields()
    
    # check_syntax() - skip pentru că necesită compilare
    
    print("\n" + "=" * 60)
    print("REZUMAT")
    print("=" * 60)
    
    if errors:
        print(f"\n[ERROR] ERORI GASITE: {len(errors)}")
        for error in errors:
            print(f"  {error}")
    else:
        print("\n[OK] NU SUNT ERORI CRITICE")
    
    if warnings:
        print(f"\n[WARNING] AVERTISMENTE: {len(warnings)}")
        for warning in warnings:
            print(f"  {warning}")
    
    print("\n" + "=" * 60)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
