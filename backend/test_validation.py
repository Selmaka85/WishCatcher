"""
Test validare WishRequest
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.models import WishRequest
from pydantic import ValidationError

# Test cu date similare cu ce trimite frontend-ul
test_cases = [
    {
        "name": "Request normal",
        "data": {
            "sources": ["reddit"],
            "filters": {"geography": {"level": "global"}},
            "limit": 50
        }
    },
    {
        "name": "Request fara filters",
        "data": {
            "sources": ["reddit"],
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
]

print("=" * 60)
print("Test Validare WishRequest")
print("=" * 60)

for test in test_cases:
    print(f"\n[*] Test: {test['name']}")
    print(f"    Data: {json.dumps(test['data'])}")
    
    try:
        req = WishRequest(**test['data'])
        print(f"    [OK] Validat cu succes")
        print(f"    Sources: {req.sources}")
        print(f"    Filters: {req.filters}")
        print(f"    Limit: {req.limit}")
    except ValidationError as e:
        print(f"    [ERROR] Validare esuata:")
        print(f"    {e.json()}")
