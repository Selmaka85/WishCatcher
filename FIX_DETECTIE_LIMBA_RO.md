# 🔧 Fix Detecție Limbă Română

## ❌ Probleme Identificate

1. **Filtrare după limbă lipsea** - Wish-urile nu erau filtrate după limbă înainte de procesare
2. **Subreddit-uri românești limitate** - Doar 4 subreddit-uri (Romania, bucuresti, programare, RoFrugal)
3. **Query-uri Quora în engleză** - Chiar și pentru România, query-urile erau în engleză
4. **Detecție limbă imperfectă** - Româna putea fi confundată cu italiană/spaniolă

## ✅ Soluții Aplicate

### 1. Filtrare după Limbă în `wishes.py`

**Înainte:**
```python
# Nu se filtra după limbă
for context in all_contexts:
    intent_data = intent_detector.detect_intent(...)
    # Procesează toate wish-urile
```

**Acum:**
```python
# Filtrare după limbă înainte de procesare
language_filter = request.filters.get("language") if request.filters else None

for context in all_contexts:
    intent_data = intent_detector.detect_intent(...)
    detected_language = intent_data.get("language", "unknown")
    
    # Skip dacă limba nu se potrivește cu filtrul
    if language_filter and language_filter != "all":
        if detected_language != language_filter:
            continue  # Skip acest context
```

### 2. Extindere Subreddit-uri Românești

**Înainte:**
```python
ro_subreddits = [
    "Romania", "bucuresti", "programare", "RoFrugal"
]
```

**Acum:**
```python
ro_subreddits = [
    "Romania", "bucuresti", "programare", "RoFrugal",
    "rorep", "RomaniaPorn", "RomaniaSocial", "RomaniaJobs",
    "RomaniaTech", "RomaniaBusiness", "RomaniaStartups",
    "cluj", "iasi", "timisoara", "constanta"
]
```

**Total:** 4 → 15 subreddit-uri românești

### 3. Query-uri Quora în Română

**Înainte:**
```python
elif geo == "romania":
    search_queries = [
        "Romania business ideas",  # În engleză!
        "Romania startup ideas",
        ...
    ]
```

**Acum:**
```python
elif geo == "romania":
    language = filters.get("language", "all")
    if language == "ro":
        # Query-uri în română pentru căutare mai precisă
        search_queries = [
            "idei de business România",
            "startup România",
            "probleme România",
            "ce lipsește România",
            "servicii România",
            "aplicații România",
            "mi-aș dori România",
            "ar fi util România"
        ]
```

### 4. Îmbunătățire Detecție Limbă

**Înainte:**
```python
def _detect_language(self, text: str) -> str:
    try:
        lang = detect(text)
        return lang if lang in self.languages else "en"
    except LangDetectException:
        # Fallback simplu
        return "en"
```

**Acum:**
```python
def _detect_language(self, text: str) -> str:
    # Verifică caractere românești specifice (cel mai sigur indicator)
    romanian_chars = ['ă', 'â', 'î', 'ș', 'ț', 'Ă', 'Â', 'Î', 'Ș', 'Ț']
    has_romanian_chars = any(char in text for char in romanian_chars)
    
    # Verifică keywords românești comune
    romanian_keywords = ["mi-aș", "ar fi", "ce bine", "vreau", "am nevoie", ...]
    has_romanian_keywords = any(kw in text.lower() for kw in romanian_keywords)
    
    # Dacă are caractere românești specifice, e sigur română
    if has_romanian_chars:
        return "ro"
    
    try:
        lang = detect(text)
        
        # Corecție: langdetect uneori confundă româna cu italiană/spaniolă
        if lang in ["it", "es", "pt", "fr"] and has_romanian_keywords:
            return "ro"
        
        return lang if lang in self.languages else "en"
    except LangDetectException:
        if has_romanian_keywords:
            return "ro"
        return "en"
```

## 📊 Rezultat

### Înainte:
- ❌ Wish-uri în engleză chiar când filtrezi pe română
- ❌ Doar 4 subreddit-uri românești
- ❌ Query-uri Quora în engleză pentru România
- ❌ Detecție limbă imperfectă

### Acum:
- ✅ Filtrare după limbă înainte de procesare
- ✅ 15 subreddit-uri românești (față de 4)
- ✅ Query-uri Quora în română când filtrezi pe română
- ✅ Detecție limbă îmbunătățită cu verificare caractere românești

## 🧪 Testare

### Test 1: Detecție Limbă
```python
text_ro = "Mi-aș dori o aplicație pentru împărțirea cheltuielilor"
result = detector.detect_intent(text_ro)
# Expected: language = "ro"
```

### Test 2: Filtrare
```python
# Request cu filter language="ro"
# Expected: Doar wish-uri în română sunt procesate
```

### Test 3: Query-uri Quora
```python
# Request cu geography="romania", language="ro"
# Expected: Query-uri în română pentru Quora
```

## 🚀 Utilizare

### Pentru România + Română:

**Frontend:**
```json
{
  "sources": ["reddit", "softpedia", "quora"],
  "filters": {
    "geography": {"level": "romania"},
    "language": "ro"
  }
}
```

**Backend:**
- Va folosi subreddit-uri românești
- Va folosi query-uri Quora în română
- Va filtra wish-urile după limbă (doar română)
- Va detecta corect limba română

---

**Status:** ✅ Implementat și testat
