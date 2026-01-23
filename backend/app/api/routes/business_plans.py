"""
Astra Genesis - Business Plan API Routes
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List
from app.api.models import (
    BusinessPlanRequest, BusinessPlanResponse
)
from app.astra_genesis.business_plan.business_plan_generator import BusinessPlanGenerator
from app.storage.business_plan_storage import BusinessPlanStorage
from app.storage.wish_storage import WishStorage

router = APIRouter()
business_plan_storage = BusinessPlanStorage()
wish_storage = WishStorage()


@router.post("/generate", response_model=BusinessPlanResponse)
async def generate_business_plan(request: BusinessPlanRequest):
    """
    Generează business plan pentru un wish
    
    - **wish_id**: ID-ul wish-ului
    - **include_mvp**: Include MVP structure în implementation plan
    """
    try:
        # Load wish from storage
        wish = wish_storage.get_wish(request.wish_id)
        
        if not wish:
            raise HTTPException(status_code=404, detail=f"Wish {request.wish_id} not found")
        
        # Convert wish to dict format
        # Handle domain (could be Enum or string)
        domain_value = wish.domain
        if hasattr(wish.domain, 'value'):
            domain_value = wish.domain.value
        elif isinstance(wish.domain, str):
            domain_value = wish.domain
        else:
            domain_value = str(wish.domain)
        
        # Handle feasibility - could be string or dict
        feasibility_data = wish.feasibility
        if isinstance(feasibility_data, str):
            # If it's a string, convert to dict format expected by generator
            feasibility_data = {"tech": feasibility_data, "cost": "medium", "time": "2-3 months"}
        elif not feasibility_data:
            feasibility_data = {}
        
        wish_data = {
            "intent": wish.intent,
            "intent_full": getattr(wish, 'intent_full', None) or wish.intent,
            "structured": getattr(wish, 'structured', None) or {},
            "domain": domain_value,
            "score": wish.score,
            "trigger_analysis": wish.trigger_analysis.model_dump() if wish.trigger_analysis else {},
            "market_analysis": wish.market_analysis or {},
            "monetization": wish.monetization or {},
            "feasibility": feasibility_data,
            "technologies": wish.technologies or []
        }
        
        generator = BusinessPlanGenerator()
        business_plan = generator.generate(wish_data)
        
        # Create BusinessPlanResponse
        business_plan_response = BusinessPlanResponse(
            id=f"bp_{request.wish_id}_{int(datetime.now().timestamp())}",
            wish_id=request.wish_id,
            **business_plan,
            generated_at=datetime.now()
        )
        
        # Save to storage (automatically saves MD + JSON + PDF)
        business_plan_storage.save_business_plan(business_plan_response)
        
        return business_plan_response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error generating business plan: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{business_plan_id}", response_model=BusinessPlanResponse)
async def get_business_plan(business_plan_id: str, version: int = None):
    """Obține un business plan specific"""
    plan = business_plan_storage.get_business_plan(business_plan_id, version)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Business plan not found")
    
    return BusinessPlanResponse(**plan)


@router.get("/", response_model=List[BusinessPlanResponse])
async def list_business_plans(
    limit: int = 100,
    offset: int = 0,
    wish_id: str = None
):
    """Listează business plan-uri"""
    plans = business_plan_storage.list_business_plans(limit=limit, offset=offset, wish_id=wish_id)
    return [BusinessPlanResponse(**plan) for plan in plans]


@router.get("/{business_plan_id}/export")
async def export_business_plan(business_plan_id: str, format: str = "all"):
    """
    Exportă business plan în format specificat
    
    - **format**: "json", "md", "pdf", sau "all"
    """
    try:
        exported_files = business_plan_storage.export_business_plan(business_plan_id, format)
        
        if not exported_files:
            raise HTTPException(status_code=404, detail="Business plan not found or no files to export")
        
        return {
            "message": f"Business plan {business_plan_id} exported successfully",
            "files": {k: str(v) for k, v in exported_files.items()}
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
