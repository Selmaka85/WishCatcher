"""
Storage API Routes - Export și statistici
"""

from fastapi import APIRouter, HTTPException
from app.storage.wish_storage import WishStorage
from typing import Dict, Any

router = APIRouter()

# Inițializează storage
wish_storage = WishStorage()


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Obține statistici despre wish-uri"""
    return wish_storage.get_stats()


@router.post("/export")
async def export_wishes(output_file: str = "data/wishes_export.json") -> Dict[str, str]:
    """
    Exportă toate wish-urile într-un fișier JSON
    
    - **output_file**: Path-ul fișierului de export (opțional)
    """
    try:
        export_path = wish_storage.export_to_json(output_file)
        return {
            "status": "success",
            "message": f"Wish-uri exportate cu succes",
            "file_path": export_path,
            "total": len(wish_storage.load_all_wishes())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la export: {str(e)}")
