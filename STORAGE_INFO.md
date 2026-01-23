# 📁 Stocare Wish-uri - Informații

## 📍 Unde Se Salvează Wish-urile

Wish-urile colectate se salvează automat în:

### 📂 Structură Foldere

```
backend/
└── data/
    └── wishes/
        ├── wishes.json              # Fișier principal cu toate wish-urile
        └── individual/              # Wish-uri individuale (backup)
            ├── wish_0_1234567890.json
            ├── wish_1_1234567891.json
            └── ...
```

## 💾 Format Fișiere

### `wishes.json` - Fișier Principal

Conține toate wish-urile într-un singur fișier JSON:

```json
[
  {
    "id": "wish_0_1234567890",
    "intent": "platformă pentru împărțirea cheltuielilor",
    "domain": "software",
    "score": 0.91,
    "business_score": 0.85,
    "technologies": ["react", "node.js"],
    "feasibility": "high",
    "trigger_analysis": {...},
    "source": "reddit",
    "timestamp": "2026-01-XX...",
    "frequency": 1,
    "market_analysis": {...},
    "monetization": {...}
  },
  ...
]
```

### `individual/*.json` - Wish-uri Individuale

Fiecare wish este salvat și individual pentru:
- Backup
- Acces rapid
- Export selectiv

## 🔧 Funcționalități

### 1. Salvare Automată

Wish-urile se salvează automat după colectare în:
- `backend/data/wishes/wishes.json` - fișier principal
- `backend/data/wishes/individual/` - wish-uri individuale

### 2. Export

Poți exporta toate wish-urile:

**API Endpoint:**
```bash
POST http://localhost:8000/api/storage/export
```

**Sau cu path custom:**
```bash
POST http://localhost:8000/api/storage/export?output_file=data/my_export.json
```

### 3. Statistici

Obține statistici despre wish-uri:

**API Endpoint:**
```bash
GET http://localhost:8000/api/storage/stats
```

**Răspuns:**
```json
{
  "total": 150,
  "by_source": {
    "reddit": 80,
    "quora": 50,
    "gumtree": 20
  },
  "by_domain": {
    "software": 100,
    "finance": 30,
    "health": 20
  },
  "avg_business_score": 0.75
}
```

### 4. Listare Wish-uri

Listează wish-uri cu filtre și paginare:

**API Endpoint:**
```bash
GET http://localhost:8000/api/wishes/?limit=50&offset=0&source=reddit&domain=software
```

## 📊 Accesare Date

### Din Terminal

**Vizualizează wish-uri:**
```bash
# Windows PowerShell
Get-Content backend\data\wishes\wishes.json | ConvertFrom-Json | Format-Table

# Linux/Mac
cat backend/data/wishes/wishes.json | jq .
```

**Numără wish-uri:**
```bash
# Windows PowerShell
(Get-Content backend\data\wishes\wishes.json | ConvertFrom-Json).Count

# Linux/Mac
cat backend/data/wishes/wishes.json | jq '. | length'
```

### Din Python

```python
import json
from pathlib import Path

# Încarcă wish-uri
wishes_file = Path("backend/data/wishes/wishes.json")
with open(wishes_file, 'r', encoding='utf-8') as f:
    wishes = json.load(f)

print(f"Total wish-uri: {len(wishes)}")
```

## 🔍 Verificare

### Verifică dacă există wish-uri salvate:

```bash
# Windows
dir backend\data\wishes\wishes.json

# Linux/Mac
ls -lh backend/data/wishes/wishes.json
```

### Verifică numărul de wish-uri:

```bash
# Windows PowerShell
$wishes = Get-Content backend\data\wishes\wishes.json | ConvertFrom-Json
Write-Host "Total wish-uri: $($wishes.Count)"
```

## 📝 Note

1. **Folder-ul `data/` este creat automat** la prima salvare
2. **Wish-urile se adaugă** (nu se înlocuiesc) - duplicatele sunt evitate
3. **Format JSON** - ușor de citit și procesat
4. **Backup automat** - fiecare wish este salvat și individual

## 🚀 Export Rapid

Pentru export rapid, folosește:

```bash
# Python script
cd backend
python -c "from app.storage.wish_storage import WishStorage; s = WishStorage(); print(f'Exportat: {s.export_to_json(\"data/wishes_export.json\")}')"
```

---

**Wish-urile se salvează automat după fiecare colectare!** ✅
