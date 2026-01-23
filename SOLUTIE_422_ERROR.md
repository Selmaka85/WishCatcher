# 🔧 Soluție Eroare 422 (Unprocessable Entity)

## Problema

Frontend-ul primea eroarea `422 (Unprocessable Entity)` când încerca să trimită request la `/api/wishes/collect`.

## Cauze Identificate

1. **`sources` array gol** - Frontend-ul putea trimite `sources: []` când nu era selectat nimic
2. **`filters` undefined** - Frontend-ul trimitea `undefined` în loc de `null`
3. **Validare Pydantic strictă** - Backend-ul necesita validare mai clară

## Soluții Aplicate

### 1. Validare Backend (`backend/app/api/models.py`)

```python
class WishRequest(BaseModel):
    sources: List[str] = Field(
        default=["reddit", "quora"], 
        min_length=1,  # ← Adăugat: cel puțin o sursă
        description="Lista de surse (trebuie să conțină cel puțin o sursă)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Filtre geografice/culturale"
    )
    limit: int = Field(
        default=100, 
        ge=1, 
        le=1000, 
        description="Număr maxim de wish-uri de colectat"
    )
```

### 2. Validare Frontend (`frontend/lib/api.ts`)

```typescript
collect: async (sources: string[], filters: any, limit: number = 100) => {
  // Validare: sources nu poate fi gol
  if (!sources || sources.length === 0) {
    throw new Error('Trebuie să selectezi cel puțin o sursă')
  }
  
  const response = await api.post('/api/wishes/collect', {
    sources,
    filters: filters || null, // ← Trimite null în loc de undefined
    limit,
  })
  return response.data
},
```

### 3. Exception Handler Backend (`backend/app/main.py`)

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler pentru erori de validare - returnează mesaje clare"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "message": "Eroare de validare a datelor. Verifică că toate câmpurile sunt corecte."
        }
    )
```

## Verificare

După aceste modificări:

1. **Frontend validează** că `sources` nu este gol înainte de trimitere
2. **Backend validează** că `sources` are cel puțin un element
3. **Backend returnează** mesaje clare de eroare când validarea eșuează
4. **Frontend trimite** `null` în loc de `undefined` pentru `filters`

## Testare

1. Selectează cel puțin o sursă în frontend
2. Apasă "Colectează Wish-uri"
3. Ar trebui să funcționeze fără eroare 422

## Dacă încă apare eroarea 422

1. **Verifică în browser console** exact ce eroare returnează backend-ul
2. **Verifică Network tab** - vezi exact ce body este trimis
3. **Verifică backend logs** - vezi ce eroare de validare apare

Eroarea ar trebui să fie rezolvată acum! ✅
