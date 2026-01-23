# Usage Guide - WishCatcher + Astra Genesis

## 🚀 Quick Start

### 1. Colectează Wish-uri

```bash
POST /api/wishes/collect
{
  "sources": ["reddit", "quora"],
  "filters": {
    "geography": {
      "level": "uk"
    },
    "language": "en"
  },
  "limit": 100
}
```

### 2. Generează Business Plan

```bash
POST /api/business-plans/generate
{
  "wish_id": "wish_123",
  "include_mvp": true
}
```

### 3. Generează MVP Structure

```bash
POST /api/mvp/generate
{
  "wish_id": "wish_123",
  "business_plan_id": "bp_wish_123"
}
```

## 📚 Exemple Complete

Vezi [Examples](examples.md) pentru exemple detaliate.

## 🔧 API Endpoints

### WishCatcher

- `POST /api/wishes/collect` - Colectează wish-uri
- `POST /api/wishes/combine` - Combină wish-uri complementare
- `GET /api/wishes/{wish_id}` - Obține wish specific
- `GET /api/wishes/` - Listează wish-uri

### Business Plans

- `POST /api/business-plans/generate` - Generează business plan
- `GET /api/business-plans/{business_plan_id}` - Obține business plan

### MVP

- `POST /api/mvp/generate` - Generează MVP structure
- `GET /api/mvp/{mvp_id}` - Obține MVP structure

## 📖 Documentație Completă

- [Setup Guide](setup.md)
- [Examples](examples.md)
