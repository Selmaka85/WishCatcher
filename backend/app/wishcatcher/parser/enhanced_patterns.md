# Enhanced Patterns pentru Detectare Dorințe - Analiză Completă

## 🔍 Pattern-uri Omișe (Important!)

### 1. **Expresii Negative** (Lipsă = Dorință)
- "Nu există..." → Dorință pentru ce lipsește
- "Lipsă..." → Nevoie de soluție
- "Nu am găsit..." → Căutare activă = dorință
- "Nimic nu face..." → Oportunitate

**Exemple:**
- "Nu există o aplicație bună pentru..."
- "Lipsă o platformă care să..."
- "Nu am găsit nimic care să..."

### 2. **Comparații & Sugestii de Îmbunătățire**
- "Ar trebui să fie..." → Dorință de îmbunătățire
- "Mai bun decât..." → Nevoie de alternativă
- "Ar putea fi..." → Sugestie = dorință
- "Dacă ar fi..." → Wish conditional

**Exemple:**
- "Ar trebui să fie mai simplu să..."
- "Mai bun decât X ar fi..."
- "Ar putea fi util dacă..."

### 3. **Review-uri Negative** (Frustrare = Dorință)
- "X e prost pentru..." → Nevoie de alternativă
- "Nu recomand X pentru că..." → Dorință de ceva mai bun
- "X nu funcționează pentru..." → Oportunitate

**Exemple:**
- "YNAB e prea scump pentru mine"
- "Splitwise nu are feature-ul X"
- "Nu recomand X, am nevoie de Y"

### 4. **Întrebări Retorice** (Căutare = Dorință)
- "De ce nu există..." → Dorință exprimată indirect
- "Cum fac să..." → Nevoie de soluție
- "Există ceva care..." → Căutare activă

**Exemple:**
- "De ce nu există o aplicație pentru..."
- "Cum fac să împart cheltuielile?"
- "Există ceva care să facă X?"

### 5. **Expresii de Regret & Speranță**
- "Ar fi trebuit să..." → Dorință retrospectivă
- "Sper că..." → Wish pentru viitor
- "Ar fi minunat dacă..." → Wish expres

**Exemple:**
- "Ar fi trebuit să existe..."
- "Sper că va apărea..."
- "Ar fi minunat dacă ar fi..."

### 6. **Mențiuni de Preț/Buget** (Willingness to Pay)
- "Aș plăti X pentru..." → Direct willingness to pay
- "Dacă ar costa X..." → Price sensitivity
- "Prea scump, am nevoie de..." → Nevoie la preț mai mic

**Exemple:**
- "Aș plăti €10/lună pentru..."
- "Dacă ar costa mai puțin..."
- "Prea scump, vreau ceva la €5"

### 7. **Mențiuni de Timp/Urgență**
- "Urgent am nevoie de..." → Urgență = willingness to pay mai mare
- "De mult timp caut..." → Nevoie persistentă
- "În fiecare zi am nevoie de..." → Nevoie frecventă

**Exemple:**
- "Urgent am nevoie de..."
- "De 6 luni caut..."
- "În fiecare zi trebuie să..."

### 8. **Referințe la Competitori**
- "X face asta, dar..." → Nevoie de îmbunătățire
- "Am încercat X, dar..." → Nevoie de alternativă
- "X + Y ar fi perfect" → Combinare de features

**Exemple:**
- "Splitwise face asta, dar lipsește X"
- "Am încercat YNAB, dar e prea complex"
- "X + Y ar fi perfect pentru mine"

### 9. **Expresii de Frustrare Indirectă**
- "E enervant că..." → Frustrare = pain point
- "Mă deranjează că..." → Nevoie de soluție
- "E complicat să..." → Nevoie de simplificare

**Exemple:**
- "E enervant că trebuie să..."
- "Mă deranjează că nu pot..."
- "E complicat să fac X manual"

### 10. **Sugestii de Integrare**
- "Ar fi util dacă X ar face Y" → Feature request
- "Dacă X ar integra cu Y..." → Nevoie de integrare
- "X ar trebui să aibă Y" → Feature missing

**Exemple:**
- "Ar fi util dacă Splitwise ar avea goal setting"
- "Dacă YNAB ar integra cu Revolut..."
- "X ar trebui să aibă feature Y"

## 🎯 Pattern-uri pentru Produse/Servicii

### 1. **Mențiuni de Categorii**
- "Un fel de X dar pentru Y" → Produs hibrid
- "Ca X dar mai simplu" → Simplificare
- "X pentru Y" → Niche product

### 2. **Mențiuni de Platformă**
- "Pe mobile ar fi util..." → Mobile-first
- "Pe desktop am nevoie de..." → Desktop app
- "Browser extension ar fi..." → Extension

### 3. **Mențiuni de Integrare**
- "Cu X ar fi perfect" → Integration need
- "Dacă ar merge cu Y..." → Compatibility

## 📊 Context-uri Omișe

### 1. **Thread Context**
- Răspunsuri la întrebări = clarificări
- Upvotes pe comentarii = validare
- Discussion depth = engagement

### 2. **User History**
- Post history = pattern-uri
- Comment history = interese
- Subreddit membership = niche

### 3. **Temporal Context**
- Post timing = urgență
- Frequency = nevoie persistentă
- Trends = oportunități emergente

## 🔧 Recomandări Implementare

### 1. Extinde Pattern Matching
Adaugă toate pattern-urile de mai sus în `robust_intent_detector.py`

### 2. Analiză Review-uri
Detectează review-uri negative = dorințe de alternativă

### 3. Analiză Comparații
Detectează comparații = nevoie de îmbunătățire

### 4. Extract Price Mentions
Extrage mențiuni de preț = willingness to pay

### 5. Extract Urgency
Detectează urgență = prioritizare
