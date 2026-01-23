"""
Test pentru validarea WishRequest
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.models import WishRequest
from pydantic import ValidationError

def test_requests():
    """Testează diferite scenarii de request"""
    
    test_cases = [
        {
            "name": "Request complet valid",
            "data": {
                "sources": ["reddit"],
                "filters": {"geography": {"level": "global"}},
                "limit": 50
            }
        },
        {
            "name": "Request fără filters",
            "data": {
                "sources": ["reddit"],
                "limit": 50
            }
        },
        {
            "name": "Request cu sources gol",
            "data": {
                "sources": [],
                "limit": 50
            }
        },
        {
            "name": "Request cu filters null",
            "data": {
                "sources": ["reddit"],
                "filters": None,
                "limit": 50
            }
        },
        {
            "name": "Request cu filters empty dict",
            "data": {
                "sources": ["reddit"],
                "filters": {},
                "limit": 50
            }
        },
    ]
    
    print("=" * 60)
    print("Test Validare WishRequest")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\n[*] Test: {test['name']}")
        print(f"    Data: {json.dumps(test['data'], indent=2)}")
        
        try:
            req = WishRequest(**test['data'])
            print(f"    [OK] Validat cu succes")
            print(f"    Sources: {req.sources}")
            print(f"    Filters: {req.filters}")
            print(f"    Limit: {req.limit}")
        except ValidationError as e:
            print(f"    [ERROR] Validare esuata:")
            for error in e.errors():
                print(f"      - {error['loc']}: {error['msg']}")
        except Exception as e:
            print(f"    [ERROR] Eroare: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_requests()
