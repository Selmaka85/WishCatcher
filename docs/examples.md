# Examples - WishCatcher + Astra Genesis

## 📝 Exemplu Complet: Flux de la Wish la Business Plan

### 1. Colectează Wish-uri din Reddit

```python
import requests

response = requests.post("http://localhost:8000/api/wishes/collect", json={
    "sources": ["reddit"],
    "filters": {
        "geography": {
            "level": "uk",
            "country": "united_kingdom"
        }
    },
    "limit": 50
})

wishes = response.json()["wishes"]
print(f"Colectate {len(wishes)} wish-uri")
```

### 2. Selectează Wish cu Scor Mare

```python
# Sortează după business_score
top_wish = max(wishes, key=lambda w: w["business_score"])
print(f"Top wish: {top_wish['intent']}")
print(f"Business score: {top_wish['business_score']}")
```

### 3. Generează Business Plan

```python
response = requests.post(
    "http://localhost:8000/api/business-plans/generate",
    json={
        "wish_id": top_wish["id"],
        "include_mvp": True
    }
)

business_plan = response.json()
print(f"Business plan generat: {business_plan['id']}")
```

### 4. Generează MVP Structure

```python
response = requests.post(
    "http://localhost:8000/api/mvp/generate",
    json={
        "wish_id": top_wish["id"],
        "business_plan_id": business_plan["id"]
    }
)

mvp = response.json()
print(f"MVP generat: {mvp['id']}")
```

## 🎯 Exemplu: Combinare Wish-uri Complementare

```python
# Combină 3 wish-uri complementare
response = requests.post(
    "http://localhost:8000/api/wishes/combine",
    json={
        "wish_ids": ["wish_1", "wish_2", "wish_3"],
        "min_similarity": 0.7,
        "max_wishes": 5
    }
)

combined = response.json()
print(f"Wish combinat: {combined['combined_intent']}")
```

## 📊 Exemplu: Analiză Trigger

```python
# Wish cu trigger analysis
wish = {
    "intent": "app pentru cheltuieli comune",
    "trigger_analysis": {
        "trigger": {
            "text": "Am avut o dispută cu colegul despre factura",
            "confidence": 0.85
        },
        "frustration": {
            "expressions": ["E frustrant să calculez manual"],
            "intensity": 0.6
        },
        "pain_points": [
            {"type": "time", "severity": "medium"},
            {"type": "risk", "severity": "high"}
        ]
    }
}
```

## 💼 Exemplu: Business Plan Output

```json
{
  "executive_summary": {
    "idea": "platformă pentru împărțirea cheltuielilor",
    "value_proposition": "Elimină dispute despre facturi",
    "market_opportunity": "Market medium în regional"
  },
  "market_analysis": {
    "target_market": {
      "size": "medium",
      "demographic": "adults_25-40"
    }
  },
  "business_model": {
    "revenue_streams": [{
      "type": "subscription",
      "pricing": "€5-10/mo"
    }]
  }
}
```
