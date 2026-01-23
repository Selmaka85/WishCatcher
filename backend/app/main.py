"""
WishCatcher + Astra Genesis - FastAPI Main Application
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import uvicorn

from app.api.routes import wishes, business_plans, mvp, storage, product_gaps, software_gaps
from app.api.models import HealthResponse

app = FastAPI(
    title="WishCatcher + Astra Genesis API",
    description="Sistem complet pentru detectare dorințe și generare business plans",
    version="1.0.0"
)

# Exception handler pentru validare
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler pentru erori de validare - returnează mesaje clare"""
    # Log request body pentru debugging
    try:
        body = await request.body()
        print(f"[DEBUG] Validation error - Request body: {body.decode('utf-8')}")
    except:
        pass
    
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
        print(f"[DEBUG] Validation error - Field: {field}, Message: {error['msg']}, Type: {error['type']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "message": "Eroare de validare a datelor. Verifică că toate câmpurile sunt corecte."
        }
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(wishes.router, prefix="/api/wishes", tags=["WishCatcher"])
app.include_router(business_plans.router, prefix="/api/business-plans", tags=["Business Plans"])
app.include_router(mvp.router, prefix="/api/mvp", tags=["MVP"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])
app.include_router(product_gaps.router, prefix="/api/product-gaps", tags=["Product Gaps"])
app.include_router(software_gaps.router, prefix="/api", tags=["Software Gaps"])


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        message="WishCatcher + Astra Genesis API is running",
        version="1.0.0"
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
