"""
API Routes pentru Software Gaps
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from app.software_gaps.software_gap_finder import SoftwareGapFinder
from app.software_gaps.storage.software_gap_storage import SoftwareGapStorage

router = APIRouter(prefix="/software-gaps", tags=["software-gaps"])


@router.get("/all", response_model=Dict[str, Any])
async def get_all_software_gaps(
    min_opportunity_score: float = 0.6,
    gap_type: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Obține toate gap-urile software identificate
    
    Query params:
        min_opportunity_score: Scor minim de oportunitate (default: 0.6)
        gap_type: Tip gap (missing, low_quality, feature_gap, localization_gap)
        category: Categorie (software, service)
    """
    try:
        storage = SoftwareGapStorage()
        
        if gap_type:
            gaps = storage.get_gaps_by_type(gap_type)
        elif category:
            gaps = storage.get_gaps_by_category(category)
        else:
            gaps = storage.load_all_gaps()
        
        # Filtrează după opportunity score
        filtered_gaps = [
            gap for gap in gaps
            if gap.get("opportunity_score", 0.0) >= min_opportunity_score
        ]
        
        # Sortează după opportunity score (desc)
        filtered_gaps.sort(key=lambda x: x.get("opportunity_score", 0.0), reverse=True)
        
        return {
            "total": len(filtered_gaps),
            "gaps": filtered_gaps
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error getting software gaps: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting software gaps: {str(e)}")


@router.get("/by-type/{gap_type}", response_model=Dict[str, Any])
async def get_software_gaps_by_type(gap_type: str):
    """Obține gap-uri software după tip"""
    try:
        storage = SoftwareGapStorage()
        gaps = storage.get_gaps_by_type(gap_type)
        
        return {
            "type": gap_type,
            "total": len(gaps),
            "gaps": gaps
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error getting software gaps by type {gap_type}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting software gaps by type: {str(e)}")


@router.post("/process-wishes")
async def process_wishes_for_software_gaps():
    """
    Procesează manual toate wish-urile pentru gap-uri software
    """
    try:
        gap_finder = SoftwareGapFinder()
        gaps = await gap_finder.process_new_wishes()
        
        if gaps:
            storage = SoftwareGapStorage()
            saved = storage.save_gaps(gaps)
            
            return {
                "success": True,
                "gaps_found": len(gaps),
                "gaps_saved": saved
            }
        else:
            return {
                "success": True,
                "gaps_found": 0,
                "gaps_saved": 0,
                "message": "No software gaps found"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error processing wishes for software gaps: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing wishes for software gaps: {str(e)}")
