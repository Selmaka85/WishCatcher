"""
API Routes pentru Product Gaps (eMAG vs Amazon)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any
from app.api.models import (
    ProductGapRequest,
    ProductGapResponse,
    ProductGap,
    FBACalculationRequest,
    FBAAnalysis
)
from app.product_gaps.scraper.product_scraper import ProductScraper
from app.product_gaps.scraper.multi_marketplace_scraper import MultiMarketplaceScraper
from app.product_gaps.fba_calculator import FBACalculator
from app.product_gaps.auto_gap_finder import AutoGapFinder
from app.storage.product_gap_storage import ProductGapStorage

router = APIRouter()
scraper = ProductScraper()
multi_scraper = MultiMarketplaceScraper()
fba_calculator = FBACalculator()
auto_gap_finder = AutoGapFinder()
gap_storage = ProductGapStorage()


@router.post("/search", response_model=ProductGapResponse)
async def search_product_gaps(request: ProductGapRequest):
    """
    Caută gap-uri de produse între eMAG și Amazon UK
    """
    try:
        # Find product gaps
        gaps_data = await scraper.find_product_gaps(
            category=request.category,
            max_price=request.max_price
        )
        
        # Calculate profit margins for gaps
        gaps = []
        for gap_data in gaps_data:
            # Calculate profit margin if we have prices
            if gap_data.get("amazon_uk_price") and gap_data.get("emag_price"):
                amazon_price_lei = gap_data["amazon_uk_price"] * 5.5  # Convert £ to lei
                profit_margin = ((gap_data["emag_price"] - amazon_price_lei) / gap_data["emag_price"]) * 100
                gap_data["profit_margin"] = round(profit_margin, 2)
            elif gap_data.get("amazon_uk_price"):
                # Estimate profit margin for missing products (assume 30% markup)
                estimated_emag_price = gap_data["amazon_uk_price"] * 5.5 * 1.3
                amazon_price_lei = gap_data["amazon_uk_price"] * 5.5
                profit_margin = ((estimated_emag_price - amazon_price_lei) / estimated_emag_price) * 100
                gap_data["profit_margin"] = round(profit_margin, 2)
            
            gaps.append(ProductGap(**gap_data))
        
        return ProductGapResponse(
            gaps=gaps,
            total_found=len(gaps),
            search_params={
                "category": request.category,
                "max_price": request.max_price,
                "search_volume": request.search_volume
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error searching product gaps: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error searching product gaps: {str(e)}")


@router.post("/calculate-fba", response_model=FBAAnalysis)
async def calculate_fba(request: FBACalculationRequest):
    """
    Calculează profitabilitatea FBA pentru un produs
    """
    try:
        analysis = fba_calculator.calculate_profitability(
            amazon_price=request.amazon_price,
            import_costs=request.import_costs,
            fba_costs=request.fba_costs,
            selling_price=request.selling_price,
            quantity=request.quantity
        )
        
        return FBAAnalysis(**analysis)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error calculating FBA: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error calculating FBA: {str(e)}")


@router.get("/auto", response_model=Dict[str, Any])
async def get_auto_gaps(
    opportunity_type: Optional[str] = None,
    gap_type: Optional[str] = None
):
    """
    Obține gap-uri identificate automat
    
    - **opportunity_type**: Filtrează după tip oportunitate (fba_import, export, dropshipping)
    - **gap_type**: Filtrează după tip gap (missing, expensive)
    """
    try:
        if opportunity_type:
            gaps = gap_storage.get_gaps_by_opportunity(opportunity_type)
        elif gap_type:
            gaps = gap_storage.get_gaps_by_type(gap_type)
        else:
            gaps = gap_storage.load_all_gaps()
        
        stats = gap_storage.get_stats()
        
        return {
            "gaps": gaps,
            "total": len(gaps),
            "stats": stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error getting auto gaps: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting auto gaps: {str(e)}")


@router.post("/process-wishes")
async def process_wishes_for_gaps(wish_ids: Optional[List[str]] = None):
    """
    Procesează wish-uri pentru identificare gap-uri (manual trigger)
    
    - **wish_ids**: Lista de ID-uri wish-uri (None = toate)
    """
    try:
        gaps = await auto_gap_finder.process_new_wishes(wish_ids)
        
        if gaps:
            saved_count = gap_storage.save_gaps(gaps)
            return {
                "message": f"Processed wishes and found {len(gaps)} gaps",
                "gaps_saved": saved_count,
                "total_gaps": len(gaps)
            }
        else:
            return {
                "message": "No gaps found",
                "gaps_saved": 0,
                "total_gaps": 0
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error processing wishes for gaps: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing wishes: {str(e)}")
