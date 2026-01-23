"""
Astra Genesis - MVP Generator API Routes
"""

from fastapi import APIRouter, HTTPException
from app.api.models import MVPRequest, MVPResponse
from app.astra_genesis.mvp_generator.mvp_structure_generator import MVPStructureGenerator
from app.storage.mvp_storage import MVPStorage
from app.storage.wish_storage import WishStorage
from datetime import datetime
from typing import List

router = APIRouter()
mvp_storage = MVPStorage()
wish_storage = WishStorage()


@router.post("/generate", response_model=MVPResponse)
async def generate_mvp(request: MVPRequest):
    """
    Generează MVP structure pentru un wish
    
    - **wish_id**: ID-ul wish-ului
    - **business_plan_id**: ID-ul business plan-ului (opțional)
    """
    try:
        # Verify wish exists
        wish = wish_storage.get_wish(request.wish_id)
        if not wish:
            raise HTTPException(status_code=404, detail=f"Wish {request.wish_id} not found")
        
        generator = MVPStructureGenerator()
        # Pasează wish_data pentru a folosi structured
        wish_dict = wish.model_dump() if hasattr(wish, 'model_dump') else (wish.dict() if hasattr(wish, 'dict') else wish)
        
        # Get business_plan_id if provided (it's optional in MVPRequest)
        business_plan_id = getattr(request, 'business_plan_id', None)
        
        mvp_structure = generator.generate(
            wish_id=request.wish_id,
            business_plan_id=business_plan_id,
            wish_data=wish_dict
        )
        
        # Create MVPResponse
        mvp_response = MVPResponse(
            id=f"mvp_{request.wish_id}_{int(datetime.now().timestamp())}",
            wish_id=request.wish_id,
            structure=mvp_structure["structure"],
            files=mvp_structure["files"],
            generated_at=datetime.now()
        )
        
        # Save to storage (automatically creates ZIP archive)
        mvp_storage.save_mvp(mvp_response)
        
        return mvp_response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error generating MVP structure: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{mvp_id}", response_model=MVPResponse)
async def get_mvp(mvp_id: str):
    """Obține un MVP structure specific"""
    mvp = mvp_storage.get_mvp(mvp_id)
    
    if not mvp:
        raise HTTPException(status_code=404, detail="MVP not found")
    
    return MVPResponse(**mvp)


@router.get("/", response_model=List[MVPResponse])
async def list_mvps(
    limit: int = 100,
    offset: int = 0,
    wish_id: str = None
):
    """Listează MVP-uri"""
    mvps = mvp_storage.list_mvps(limit=limit, offset=offset, wish_id=wish_id)
    return [MVPResponse(**mvp) for mvp in mvps]


@router.get("/{mvp_id}/export")
async def export_mvp_zip(mvp_id: str):
    """Exportă MVP ca ZIP archive"""
    zip_file = mvp_storage.export_mvp_zip(mvp_id)
    
    if not zip_file:
        raise HTTPException(status_code=404, detail="MVP not found or ZIP not available")
    
    return {
        "message": f"MVP {mvp_id} exported successfully",
        "zip_file": str(zip_file),
        "download_url": f"/api/mvp/{mvp_id}/download"
    }
