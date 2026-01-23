# Surse și Configurație Scraping - WishCatcher

## 📍 Surse Implementate (Funcționale)

### 1. **Reddit** ✅ COMPLET IMPLEMENTAT

#### UK Subreddits:
- `r/unitedkingdom` - Discuții generale UK
- `r/london` - Discuții despre Londra
- `r/AskUK` - Întrebări despre UK
- `r/CasualUK` - Discuții casual UK
- `r/UKPersonalFinance` - Finanțe personale UK
- `r/UKFrugal` - Economii și frugalitate UK

#### România Subreddits:
- `r/Romania` - Discuții generale România
- `r/bucuresti` - Discuții despre București
- `r/programare` - Programare și tech România
- `r/RoFrugal` - Economii și frugalitate România

#### Configurație:
- **Metodă**: Reddit JSON API (fără autentificare necesară)
- **Rate Limiting**: 60 requests/minut
- **Perioadă**: Ultima lună (`t=month`)
- **Limită**: Max 25 posturi per subreddit
- **Context**: Post + toate comentariile (inclusiv replies)

#### Ce colectează:
- Post title + text
- Autor post
- Timestamp
- Upvotes
- **Toate comentariile** (inclusiv replies nested)
- Engagement score (calculat)
- Discussion depth

---

## ✅ Surse Implementate (Funcționale)

### 2. **Quora** ✅ IMPLEMENTAT
- Status: ✅ Funcțional
- Metodă: Scraping HTML cu BeautifulSoup
- Search queries: "business ideas", "startup ideas", "problems need solutions"
- Filtrare geografică: UK/Romania queries
- Colectează: Întrebări + top 10 răspunsuri

### 3. **Gumtree** ✅ IMPLEMENTAT
- Status: ✅ Funcțional (UK only)
- Metodă: Scraping HTML
- Search queries: "wanted", "looking for", "need"
- Filtrare: Doar UK (Gumtree e UK marketplace)
- Colectează: Listings cu descrieri

### 4. **Mumsnet** ✅ IMPLEMENTAT
- Status: ✅ Funcțional (UK only)
- Metodă: Scraping HTML
- Boards: Talk, Am I Being Unreasonable
- Filtrare: Doar UK
- Colectează: Discuții + top 20 posturi

### 5. **MoneySavingExpert** ✅ IMPLEMENTAT
- Status: ✅ Funcțional (UK only)
- Metodă: Scraping HTML
- Categories: Deals Discussion, Debt Free Wannabe
- Filtrare: Doar UK
- Colectează: Topics + top 20 posturi

### 6. **Indie Hackers** ✅ IMPLEMENTAT
- Status: ✅ Funcțional
- Metodă: Scraping HTML
- Pages: Posts, Posts page 2
- Colectează: Posts + top 10 comentarii

### 7. **Hacker News** ✅ IMPLEMENTAT
- Status: ✅ Funcțional
- Metodă: Hacker News Firebase API (nu scraping!)
- Endpoint: `https://hacker-news.firebaseio.com/v0/`
- Colectează: Top stories + top 10 comentarii
- Avantaj: API oficial, nu scraping

### 8. **Product Hunt** ✅ IMPLEMENTAT
- Status: ✅ Funcțional
- Metodă: Scraping HTML
- Page: Posts
- Colectează: Products + top 10 comentarii

### 9. **YouTube** ⚠️ PARȚIAL IMPLEMENTAT
- Status: ⚠️ Basic scraping (comentarii necesită API)
- Metodă: Scraping HTML (limitat)
- Note: Comentarii sunt încărcate dinamic (JavaScript)
- Recomandare: Folosește YouTube Data API v3 pentru comentarii
- Colectează: Video title + description (comentarii TODO cu API)

---

## 🌍 Filtrare Geografică

### Cum funcționează:
1. **Global** (default): Caută în toate subreddit-urile (UK + RO)
2. **UK**: Caută doar în subreddit-urile UK
3. **România**: Caută doar în subreddit-urile RO

### Configurație:
```python
filters = {
    "geography": {
        "level": "uk" | "romania" | "global"
    }
}
```

---

## 📊 Statistici Colectare

### Per Request:
- **Max subreddits**: 5 (limitat pentru performanță)
- **Max posturi/subreddit**: 25
- **Total max**: ~125 posturi per request
- **Context complet**: Post + toate comentariile

### Rate Limiting:
- **60 requests/minut** (respectă Reddit rate limits)
- **1 secundă delay** între subreddit-uri

---

## 🔧 Cum se Configurează

### În Frontend:
```typescript
// Selectează surse
sources: ["reddit"]

// Setează filtre
filters: {
  geography: { level: "uk" },  // sau "romania" sau "global"
  language: "en",              // sau "ro" sau "all"
  domain: "software"           // sau "finance", "health", etc.
}
```

### În API:
```python
POST /api/wishes/collect
{
  "sources": ["reddit"],
  "filters": {
    "geography": {"level": "uk"}
  },
  "limit": 100
}
```

---

## 📝 Rezumat

### ✅ Funcționează Acum:
- ✅ **Reddit** - 10 subreddits (6 UK + 4 RO)
- ✅ **Quora** - Search queries cu răspunsuri
- ✅ **Gumtree** - UK marketplace listings
- ✅ **Mumsnet** - UK parenting forum
- ✅ **MoneySavingExpert** - UK finance forum
- ✅ **Indie Hackers** - Startup discussions
- ✅ **Hacker News** - Tech news (API oficial)
- ✅ **Product Hunt** - Product launches
- ⚠️ **YouTube** - Basic (comentarii necesită API)
- ✅ Context complet (post + comentarii)
- ✅ Rate limiting inteligent
- ✅ Filtrare geografică

---

## 💡 Recomandări

### Pentru Mai Multe Surse:
1. **Reddit** e suficient pentru început (mare volum, API ușor)
2. **Quora** ar fi următorul (mare volum, dar necesită scraping)
3. **Gumtree** pentru UK (local, specific)
4. **Mumsnet** pentru UK (niche, valoare mare)

### Prioritizare:
1. ✅ Reddit (DONE)
2. ⏳ Quora (HIGH priority)
3. ⏳ Gumtree (MEDIUM priority)
4. ⏳ Mumsnet (MEDIUM priority)
5. ⏳ Rest (LOW priority)

---

## 🎯 Concluzie

**Acum funcționează:**
- ✅ Reddit cu 10 subreddits (UK + RO)
- ✅ Context complet (post + comentarii)
- ✅ Filtrare geografică

**Pentru mai multe surse**, trebuie implementat scraping HTML pentru:
- Quora
- Gumtree
- Mumsnet
- etc.
