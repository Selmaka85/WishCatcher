# Analiză Consum Resurse - WishCatcher + Astra Genesis

## 💻 Consum Resurse

### Backend (FastAPI)

#### CPU:
- **Idle**: ~0-2% CPU (doar server-ul rulează)
- **Scraping activ**: 10-30% CPU (depinde de numărul de surse)
- **NLP Processing**: 20-40% CPU (spaCy models)
- **Peak**: 50-70% CPU (scraping + NLP simultan)

#### RAM:
- **Base**: ~200-300 MB (FastAPI + dependențe)
- **spaCy models**: ~150-200 MB (ro_core_news_sm + en_core_web_sm)
- **Scraping activ**: +100-300 MB (cache HTML, responses)
- **Total normal**: ~500-800 MB
- **Peak**: ~1-1.5 GB (scraping multiple surse simultan)

#### Disk:
- **Dependențe Python**: ~500 MB
- **spaCy models**: ~50 MB
- **Cache/Logs**: ~100-500 MB (crește cu timpul)
- **Total**: ~1-2 GB

### Frontend (Next.js)

#### CPU:
- **Idle**: ~0-1% CPU
- **Active browsing**: 2-5% CPU
- **Peak**: 5-10% CPU (rendering complex UI)

#### RAM:
- **Base**: ~100-200 MB (Next.js dev server)
- **Browser**: ~200-400 MB (React app)
- **Total**: ~300-600 MB

#### Disk:
- **node_modules**: ~300-500 MB
- **Build**: ~50-100 MB
- **Total**: ~400-600 MB

---

## 📊 Consum Total

### Scenariu Normal (Backend + Frontend):
- **CPU**: 5-15% (idle) → 30-50% (activ)
- **RAM**: 800 MB - 1.5 GB
- **Disk**: 1.5 - 2.5 GB

### Scenariu Peak (Scraping + NLP simultan):
- **CPU**: 50-70%
- **RAM**: 1.5 - 2 GB
- **Disk**: 2 - 3 GB

---

## ⚠️ Omoară Calculatorul?

### Răspuns: **NU** (pentru calculatoare moderne)

#### Calculatoare Compatibile:
- ✅ **8GB+ RAM**: Perfect
- ✅ **4GB RAM**: OK (dar poate fi lent când scraping)
- ⚠️ **2GB RAM**: Poate fi problematic (swap usage)
- ✅ **CPU modern** (i3/i5/i7 sau AMD equivalent): Perfect
- ⚠️ **CPU vechi** (< 2GHz): Poate fi lent

#### Optimizări Implementate:
- ✅ **Rate limiting**: Previne overload
- ✅ **Async/await**: Eficient I/O
- ✅ **Error handling**: Previne crashes
- ✅ **Memory cleanup**: Garbage collection

#### Ce Poate Încărca:
- ⚠️ **Scraping multiple surse simultan**: +RAM
- ⚠️ **NLP processing bulk**: +CPU
- ⚠️ **Cache mare**: +Disk

---

## 🎯 Recomandări Optimizare

### Pentru Calculatoare Slabe:
1. **Limitează sursele**: Selectează 1-2 surse, nu toate
2. **Reduce limit**: 50 wish-uri în loc de 1000
3. **Scraping incremental**: Colectează în batch-uri mici
4. **Close browser tabs**: Reduce RAM usage

### Pentru Calculatoare Puternice:
- ✅ Poți rula toate sursele simultan
- ✅ Poți procesa 1000+ wish-uri
- ✅ No problem!

---

## 💡 Optimizări Viitoare (Opționale)

1. **Database caching**: Reduce re-scraping
2. **Background jobs**: Scraping în background
3. **Lazy loading**: Load models doar când necesar
4. **Compression**: Compress responses
5. **CDN**: Pentru frontend static

---

## 📝 Concluzie

**Nu o să omoare calculatorul** dacă:
- Ai minim 4GB RAM
- CPU modern (2015+)
- Nu rulezi alte aplicații grele simultan

**Poate fi problematic** dacă:
- Ai < 2GB RAM
- CPU foarte vechi
- Rulezi multe aplicații simultan

**Recomandare**: Pentru production, rulează pe un server dedicat sau cloud (AWS, DigitalOcean, etc.)
