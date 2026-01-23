# 🔧 Configurare Amazon Product Advertising API 5.0 (GRATUIT)

## ✅ De ce PA-API 5.0?

- **GRATUIT** - Nu plătești nimic
- **OFICIAL** - API oficial de la Amazon
- **FIABIL** - Nu e blocat de anti-bot
- **COMPLET** - Acces la toate datele produselor

## 📋 Pași de Configurare

### Pasul 1: Creează Cont Amazon Associates

1. Mergi la: https://affiliate-program.amazon.co.uk/
2. Creează cont (sau loghează-te)
3. Completează formularul de înregistrare
4. Așteaptă aprobarea (1-3 zile)

### Pasul 2: Obține Associate Tag

1. După aprobare, mergi în **Account Settings**
2. Găsește **Associate Tag** (ex: `yourname-21`)
3. Notează-l - îl vei folosi ca `AMAZON_PARTNER_TAG`

### Pasul 3: Generează Vânzări Calificate

**IMPORTANT**: Pentru a accesa PA-API, trebuie să ai:
- ✅ Cont aprobat
- ✅ Cel puțin 3 vânzări calificate în ultimele 180 de zile

**Cum să generezi vânzări:**
- Distribuie link-uri de afiliat
- Oamenii cumpără prin link-urile tale
- După 3+ vânzări, poți accesa PA-API

### Pasul 4: Obține Access Key și Secret Key

1. Mergi la: https://webservices.amazon.co.uk/paapi5/documentation/register-for-pa-api.html
2. Completează formularul:
   - **Associate Tag**: Tag-ul tău (ex: `yourname-21`)
   - **Website/App**: URL-ul aplicației tale
   - **Description**: Descrierea aplicației
3. După aprobare, vei primi:
   - **Access Key** (ex: `AKIAIOSFODNN7EXAMPLE`)
   - **Secret Key** (ex: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

### Pasul 5: Configurează Variabilele de Mediu

Creează un fișier `.env` în folderul `backend/`:

```env
# Amazon PA-API 5.0 Configuration
AMAZON_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
AMAZON_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AMAZON_PARTNER_TAG=yourname-21
AMAZON_HOST=webservices.amazon.co.uk
AMAZON_REGION=eu-west-1
```

**SAU** setează-le în sistem:

**Windows (PowerShell):**
```powershell
$env:AMAZON_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
$env:AMAZON_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AMAZON_PARTNER_TAG="yourname-21"
```

**Linux/Mac:**
```bash
export AMAZON_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
export AMAZON_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AMAZON_PARTNER_TAG="yourname-21"
```

### Pasul 6: Instalează SDK-ul

```bash
cd backend
pip install paapi5-python-sdk
```

## 🧪 Testare

După configurare, testează:

```bash
cd backend
python -c "from app.product_gaps.scraper.amazon_paapi import AmazonPAAPIScraper; scraper = AmazonPAAPIScraper(); print('✅ Configured!' if scraper.is_configured() else '❌ Not configured'); products = scraper.search_products('laptop'); print(f'Found {len(products)} products')"
```

## 📊 Limitări Free Tier

- **10 rezultate per request** (suficient pentru gap finding)
- **1 request per secundă** (rate limit)
- **Necesită vânzări calificate** pentru acces complet

## ⚠️ Probleme Comune

### "Access Denied" (403)
- **Cauză**: Nu ai vânzări calificate sau contul nu e aprobat
- **Soluție**: Generează 3+ vânzări prin link-uri de afiliat

### "Invalid Credentials" (401)
- **Cauză**: Access Key sau Secret Key greșite
- **Soluție**: Verifică variabilele de mediu

### "Rate Limit Exceeded" (429)
- **Cauză**: Prea multe request-uri
- **Soluție**: Așteaptă 1 secundă între request-uri

## 🔗 Link-uri Utile

- **Documentație PA-API 5.0**: https://webservices.amazon.com/paapi5/documentation/
- **Amazon Associates**: https://affiliate-program.amazon.co.uk/
- **Register for PA-API**: https://webservices.amazon.co.uk/paapi5/documentation/register-for-pa-api.html

## ✅ După Configurare

După ce ai configurat PA-API, scraper-ul va folosi automat API-ul oficial în loc de scraping, oferind:
- ✅ Rezultate fiabile
- ✅ Date complete (prețuri, imagini, disponibilitate)
- ✅ Fără blocări anti-bot
- ✅ GRATUIT
