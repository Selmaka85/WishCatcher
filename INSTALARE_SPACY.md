# 📦 Instalare Modele spaCy - Ghid Complet

## ✅ Status Actual

Modelul română (`ro_core_news_sm`) a fost instalat cu succes!

## 🔧 Comenzi de Instalare

### Opțiunea 1: Cu `--user` (Recomandat pentru Windows)

```bash
python -m spacy download ro_core_news_sm --user
python -m spacy download en_core_web_sm --user
```

### Opțiunea 2: Fără `--user` (Dacă ai permisiuni admin)

```bash
python -m spacy download ro_core_news_sm
python -m spacy download en_core_web_sm
```

### Opțiunea 3: Direct cu pip (Alternativă)

```bash
pip install https://github.com/explosion/spacy-models/releases/download/ro_core_news_sm-3.7.0/ro_core_news_sm-3.7.0-py3-none-any.whl
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl
```

## 🐛 Probleme Comune și Soluții

### Problema 1: "Permission denied" sau "Access denied"

**Cauză:** Nu ai permisiuni de scriere în directorul Python global.

**Soluție:**
```bash
# Folosește --user flag
python -m spacy download ro_core_news_sm --user
```

### Problema 2: "Module not found" după instalare

**Cauză:** Modelul este instalat într-un loc diferit de unde Python îl caută.

**Soluție:**
```bash
# Verifică unde este instalat
python -c "import spacy; print(spacy.util.find_model('ro_core_news_sm'))"

# Sau reinstalează fără --user (dacă ai permisiuni)
python -m spacy download ro_core_news_sm
```

### Problema 3: "Connection error" sau "Download failed"

**Cauză:** Probleme de rețea sau firewall.

**Soluție:**
```bash
# Instalează manual din GitHub
pip install https://github.com/explosion/spacy-models/releases/download/ro_core_news_sm-3.7.0/ro_core_news_sm-3.7.0-py3-none-any.whl
```

### Problema 4: "Version mismatch"

**Cauză:** Versiunea spaCy nu se potrivește cu modelul.

**Soluție:**
```bash
# Verifică versiunea spaCy
python -c "import spacy; print(spacy.__version__)"

# Instalează versiunea corectă
pip install spacy==3.7.2
python -m spacy download ro_core_news_sm --user
```

## ✅ Verificare Instalare

### Test Rapid

```bash
python -c "import spacy; nlp = spacy.load('ro_core_news_sm'); print('Model romana OK!')"
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('Model engleza OK!')"
```

### Test Complet

```bash
cd backend
python -c "
import spacy

# Test română
nlp_ro = spacy.load('ro_core_news_sm')
doc_ro = nlp_ro('Test în română')
print(f'Română: {len(doc_ro)} tokeni')

# Test engleză
nlp_en = spacy.load('en_core_web_sm')
doc_en = nlp_en('Test in English')
print(f'Engleză: {len(doc_en)} tokeni')

print('Toate modelele funcționează!')
"
```

## 📍 Unde Sunt Instalate Modelele

### Cu `--user` flag:
- **Windows:** `C:\Users\[username]\AppData\Roaming\Python\Python310\site-packages\`
- **Linux/Mac:** `~/.local/lib/python3.X/site-packages/`

### Fără `--user` flag:
- **Windows:** `C:\Program Files\Python310\Lib\site-packages\`
- **Linux/Mac:** `/usr/local/lib/python3.X/site-packages/`

## 🔍 Verificare Loc Instalare

```bash
python -c "import spacy; import os; print(os.path.dirname(spacy.util.find_model('ro_core_news_sm')))"
```

## 🚀 Comenzi Rapide (Copy-Paste)

```bash
# Instalează ambele modele
python -m spacy download ro_core_news_sm --user
python -m spacy download en_core_web_sm --user

# Verifică instalarea
python -c "import spacy; nlp = spacy.load('ro_core_news_sm'); print('OK')"
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('OK')"
```

## 📝 Note

- **Versiunea spaCy:** 3.7.2 (compatibilă cu modelele 3.7.0)
- **Dimensiune modele:**
  - `ro_core_news_sm`: ~13 MB
  - `en_core_web_sm`: ~15 MB
- **Timp instalare:** ~30-60 secunde (depinde de conexiune)

---

**Modelul română este deja instalat și funcționează!** ✅
