"""
Auto Gap Finder - Rulează automat când WishCatcher găsește wish-uri pentru produse fizice
"""

from typing import List, Dict, Any, Optional
from app.product_gaps.extractor.product_extractor import ProductExtractor
from app.product_gaps.scraper.multi_marketplace_scraper import MultiMarketplaceScraper
from app.product_gaps.detector.gap_detector import GapDetector
from app.storage.wish_storage import WishStorage


class AutoGapFinder:
    """Găsește automat gap-uri când WishCatcher colectează wish-uri"""
    
    def __init__(self):
        self.product_extractor = ProductExtractor()
        self.marketplace_scraper = MultiMarketplaceScraper()
        self.gap_detector = GapDetector()
        self.wish_storage = WishStorage()
    
    async def process_new_wishes(self, wish_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Procesează wish-uri noi și identifică gap-uri
        
        Args:
            wish_ids: Lista de ID-uri wish-uri de procesat (None = toate noile)
            
        Returns:
            Lista de gap-uri identificate
        """
        all_gaps = []
        
        # Obține wish-uri (noi sau toate)
        if wish_ids:
            wishes = [self.wish_storage.get_wish(wid) for wid in wish_ids]
            wishes = [w for w in wishes if w]  # Remove None
        else:
            # Obține toate wish-urile (sau doar noile dacă avem flag)
            wishes = self.wish_storage.load_all_wishes()
        
        print(f"\n[AutoGapFinder] ========================================")
        print(f"[AutoGapFinder] Processing {len(wishes)} wishes...")
        print(f"[AutoGapFinder] ========================================\n")
        
        # Statistici
        stats = {
            "total_wishes": len(wishes),
            "physical_products": 0,
            "products_extracted": 0,
            "gaps_found": 0,
            "skipped": 0,
            "no_physical": 0,
            "no_products_extracted": 0,
            "scraper_errors": 0
        }
        
        # Procesează fiecare wish
        for idx, wish in enumerate(wishes):
            try:
                # Convert WishData to dict
                if hasattr(wish, 'model_dump'):
                    wish_dict = wish.model_dump()
                elif hasattr(wish, 'dict'):
                    wish_dict = wish.dict()
                elif isinstance(wish, dict):
                    wish_dict = wish
                else:
                    # Try to convert Pydantic model
                    try:
                        wish_dict = dict(wish)
                    except:
                        stats["skipped"] += 1
                        continue
                
                wish_id = wish_dict.get('id', f'wish_{idx}')
                intent = wish_dict.get('intent', '')
                language = wish_dict.get('language', 'ro')
                
                # Log progres
                if (idx + 1) % 10 == 0:
                    print(f"[AutoGapFinder] Progress: {idx + 1}/{len(wishes)} wishes processed...")
                
                # Verifică dacă e produs fizic (folosește context complet)
                context = wish_dict.get("context") or wish_dict.get("full_context")
                is_physical = self.product_extractor.is_physical_product(intent, language, context)
                
                if not is_physical:
                    stats["no_physical"] += 1
                    if (idx + 1) % 20 == 0:  # Log mai des pentru debugging
                        print(f"[AutoGapFinder] Wish {wish_id} skipped (not physical product): '{intent[:80]}...'")
                    continue
                
                stats["physical_products"] += 1
                print(f"[AutoGapFinder] Wish {wish_id} identified as physical product")
                
                # Extrage produse din wish
                products = self.product_extractor.extract_products_from_wish(wish_dict)
                
                if not products:
                    stats["no_products_extracted"] += 1
                    print(f"[AutoGapFinder] ⚠️  No products extracted from wish {wish_id}")
                    print(f"  Intent: '{intent[:100]}...'")
                    continue
                
                stats["products_extracted"] += len(products)
                print(f"[AutoGapFinder] Found {len(products)} products in wish {wish_id}: {[p.get('product_name') for p in products]}")
                
                # Pentru fiecare produs, caută pe marketplace-uri
                for product in products:
                    product_name = product.get("product_name")
                    confidence = product.get("confidence", 0.5)
                    
                    if not product_name:
                        continue
                    
                    # Skip produse cu confidence prea mică (opțional)
                    if confidence < 0.5:
                        print(f"[AutoGapFinder] Skipping {product_name} (low confidence: {confidence})")
                        continue
                    
                    print(f"[AutoGapFinder] Searching for product: {product_name} (confidence: {confidence:.2f})")
                    
                    # Caută pe toate marketplace-urile
                    try:
                        marketplace_results = await self.marketplace_scraper.search_all_marketplaces(product_name)
                    except Exception as e:
                        stats["scraper_errors"] += 1
                        print(f"[AutoGapFinder] ❌ Error searching marketplaces for '{product_name}': {e}")
                        continue
                    
                    # Detectează gap-uri
                    gaps = self.gap_detector.detect_gaps(marketplace_results)
                    
                    if gaps:
                        stats["gaps_found"] += len(gaps)
                        print(f"[AutoGapFinder] ✅ Found {len(gaps)} gaps for '{product_name}':")
                        for gap in gaps:
                            gap_type = gap.get("type", "unknown")
                            opportunity = gap.get("opportunity_type", "unknown")
                            print(f"  - {gap_type} ({opportunity})")
                        
                        # Adaugă metadata la gap-uri
                        for gap in gaps:
                            gap["source_wish_id"] = wish_id
                            gap["category"] = product.get("category", "other")
                            gap["extracted_at"] = wish_dict.get('timestamp')
                            gap["product_confidence"] = confidence
                        
                        all_gaps.extend(gaps)
                    else:
                        print(f"[AutoGapFinder] No gaps found for '{product_name}'")
                    
                    # Rate limiting
                    import asyncio
                    await asyncio.sleep(2)  # Be respectful
            
            except Exception as e:
                wish_id = wish_dict.get('id', 'unknown') if 'wish_dict' in locals() else 'unknown'
                print(f"[ERROR] Error processing wish {wish_id}: {e}")
                import traceback
                traceback.print_exc()
                stats["skipped"] += 1
                continue
        
        # Print final stats
        print(f"\n[AutoGapFinder] ========================================")
        print(f"[AutoGapFinder] === FINAL STATS ===")
        print(f"[AutoGapFinder] ========================================")
        print(f"  Total wishes processed: {stats['total_wishes']}")
        print(f"  Physical products identified: {stats['physical_products']}")
        print(f"  Products extracted: {stats['products_extracted']}")
        print(f"  Gaps found: {stats['gaps_found']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Not physical products: {stats['no_physical']}")
        print(f"  No products extracted: {stats['no_products_extracted']}")
        print(f"  Scraper errors: {stats['scraper_errors']}")
        print(f"[AutoGapFinder] Total gaps found: {len(all_gaps)}")
        print(f"[AutoGapFinder] ========================================\n")
        
        print(f"[AutoGapFinder] Total gaps found: {len(all_gaps)}")
        return all_gaps
    
    async def process_wish_batch(self, wish_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesează un batch de wish-uri (folosit când WishCatcher colectează)
        
        Args:
            wish_batch: Lista de wish-uri noi colectate
            
        Returns:
            Lista de gap-uri identificate
        """
        all_gaps = []
        
        print(f"[AutoGapFinder] Processing batch of {len(wish_batch)} wishes...")
        
        for idx, wish in enumerate(wish_batch):
            try:
                wish_id = wish.get("id", f"batch_wish_{idx}")
                intent = wish.get("intent", "")
                language = wish.get("language", "ro")
                
                # Verifică dacă e produs fizic (folosește context)
                context = wish.get("context") or wish.get("full_context")
                if not self.product_extractor.is_physical_product(intent, language, context):
                    continue
                
                print(f"[AutoGapFinder] Wish {wish_id} identified as physical product")
                
                # Extrage produse
                products = self.product_extractor.extract_products_from_wish(wish)
                
                if not products:
                    continue
                
                print(f"[AutoGapFinder] Extracted {len(products)} products from wish {wish_id}")
                
                # Pentru fiecare produs
                for product in products:
                    product_name = product.get("product_name")
                    confidence = product.get("confidence", 0.5)
                    
                    if not product_name or confidence < 0.5:
                        continue
                    
                    print(f"[AutoGapFinder] Searching for: {product_name}")
                    
                    # Caută pe marketplace-uri
                    marketplace_results = await self.marketplace_scraper.search_all_marketplaces(product_name)
                    
                    # Detectează gap-uri
                    gaps = self.gap_detector.detect_gaps(marketplace_results)
                    
                    if gaps:
                        print(f"[AutoGapFinder] ✅ Found {len(gaps)} gaps for '{product_name}'")
                        for gap in gaps:
                            gap["source_wish_id"] = wish.get("id")
                            gap["category"] = product.get("category", "other")
                            gap["extracted_at"] = wish.get("timestamp")
                            gap["product_confidence"] = confidence
                        
                        all_gaps.extend(gaps)
                    
                    import asyncio
                    await asyncio.sleep(2)
            
            except Exception as e:
                print(f"[ERROR] Error processing wish in batch: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return all_gaps
