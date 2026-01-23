"""
Software Gap Finder - Găsește automat gap-uri software când WishCatcher colectează wish-uri
Similar cu AutoGapFinder dar pentru software/servicii digitale
"""

from typing import List, Dict, Any, Optional
from app.software_gaps.validator.software_existence_validator import SoftwareExistenceValidator
from app.software_gaps.detector.software_gap_detector import SoftwareGapDetector
from app.storage.wish_storage import WishStorage
from app.wishcatcher.extractor.precise_context_extractor import PreciseContextExtractor


class SoftwareGapFinder:
    """Găsește automat gap-uri software când WishCatcher colectează wish-uri"""
    
    def __init__(self):
        self.existence_validator = SoftwareExistenceValidator()
        self.gap_detector = SoftwareGapDetector()
        self.wish_storage = WishStorage()
        self.precise_extractor = PreciseContextExtractor()
    
    async def process_new_wishes(self, wish_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Procesează wish-uri noi și identifică gap-uri software
        
        Args:
            wish_ids: Lista de ID-uri wish-uri de procesat (None = toate noile)
            
        Returns:
            Lista de gap-uri software identificate
        """
        all_gaps = []
        
        # Obține wish-uri (noi sau toate)
        if wish_ids:
            wishes = [self.wish_storage.get_wish(wid) for wid in wish_ids]
            wishes = [w for w in wishes if w]
        else:
            wishes = self.wish_storage.load_all_wishes()
        
        print(f"\n[SoftwareGapFinder] ========================================")
        print(f"[SoftwareGapFinder] Processing {len(wishes)} wishes for software gaps...")
        print(f"[SoftwareGapFinder] ========================================\n")
        
        # Statistici
        stats = {
            "total_wishes": len(wishes),
            "software_wishes": 0,
            "gaps_found": 0,
            "skipped": 0,
            "not_software": 0,
            "validation_errors": 0
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
                    print(f"[SoftwareGapFinder] Progress: {idx + 1}/{len(wishes)} wishes processed...")
                
                # Verifică dacă e software/serviciu digital (folosește PreciseContextExtractor)
                context = wish_dict.get("context") or wish_dict.get("full_context")
                precise_context = self.precise_extractor.extract_precise_context(
                    text=intent,
                    language=language,
                    context=context
                )
                
                if not precise_context or not precise_context.get("is_valid", False):
                    stats["not_software"] += 1
                    if (idx + 1) % 20 == 0:
                        print(f"[SoftwareGapFinder] Wish {wish_id} skipped (not valid software/service)")
                    continue
                
                # Verifică tipul entității
                entity_type = precise_context.get("entity_type", "unknown")
                if entity_type not in ["software", "service"]:
                    stats["not_software"] += 1
                    if (idx + 1) % 20 == 0:
                        print(f"[SoftwareGapFinder] Wish {wish_id} skipped (not software/service: {entity_type})")
                    continue
                
                stats["software_wishes"] += 1
                print(f"[SoftwareGapFinder] Wish {wish_id} identified as software/service: '{intent[:80]}...'")
                
                # Extrage informații precise
                software_name = precise_context.get("entity_name", intent)
                functionality = precise_context.get("functionality", "")
                
                # Validează existența software-ului
                try:
                    validation_result = await self.existence_validator.validate_software(
                        software_name=software_name,
                        functionality=functionality,
                        language=language
                    )
                except Exception as e:
                    stats["validation_errors"] += 1
                    print(f"[SoftwareGapFinder] ❌ Error validating software for wish {wish_id}: {e}")
                    continue
                
                # Adaugă precise_context la wish_dict pentru gap detector
                wish_dict["precise_context"] = precise_context.get("extracted_context", {})
                
                # Detectează gap-uri
                gaps = self.gap_detector.detect_gaps(wish_dict, validation_result)
                
                if gaps:
                    stats["gaps_found"] += len(gaps)
                    print(f"[SoftwareGapFinder] ✅ Found {len(gaps)} software gaps for wish {wish_id}:")
                    for gap in gaps:
                        gap_type = gap.get("type", "unknown")
                        opportunity = gap.get("opportunity_type", "unknown")
                        opportunity_score = gap.get("opportunity_score", 0.0)
                        print(f"  - {gap_type} ({opportunity}) - Score: {opportunity_score:.2f}")
                    
                    # Adaugă metadata la gap-uri
                    for gap in gaps:
                        gap["source_wish_id"] = wish_id
                        gap["category"] = precise_context.get("category", "software")
                        gap["specificity_score"] = precise_context.get("specificity_score", 0.0)
                        gap["relevance_score"] = precise_context.get("relevance_score", 0.0)
                    
                    all_gaps.extend(gaps)
                else:
                    print(f"[SoftwareGapFinder] No software gaps found for wish {wish_id}")
                
                # Rate limiting
                import asyncio
                await asyncio.sleep(1)  # Be respectful with APIs
            
            except Exception as e:
                wish_id = wish_dict.get('id', 'unknown') if 'wish_dict' in locals() else 'unknown'
                print(f"[ERROR] Error processing wish {wish_id}: {e}")
                import traceback
                traceback.print_exc()
                stats["skipped"] += 1
                continue
        
        # Print final stats
        print(f"\n[SoftwareGapFinder] ========================================")
        print(f"[SoftwareGapFinder] === FINAL STATS ===")
        print(f"[SoftwareGapFinder] ========================================")
        print(f"  Total wishes processed: {stats['total_wishes']}")
        print(f"  Software/service wishes: {stats['software_wishes']}")
        print(f"  Software gaps found: {stats['gaps_found']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Not software: {stats['not_software']}")
        print(f"  Validation errors: {stats['validation_errors']}")
        print(f"[SoftwareGapFinder] Total gaps found: {len(all_gaps)}")
        print(f"[SoftwareGapFinder] ========================================\n")
        
        return all_gaps
    
    async def process_wish_batch(self, wish_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesează un batch de wish-uri (folosit când WishCatcher colectează)
        
        Args:
            wish_batch: Lista de wish-uri noi colectate
            
        Returns:
            Lista de gap-uri software identificate
        """
        all_gaps = []
        
        print(f"[SoftwareGapFinder] Processing batch of {len(wish_batch)} wishes for software gaps...")
        
        for idx, wish in enumerate(wish_batch):
            try:
                wish_id = wish.get("id", f"batch_wish_{idx}")
                intent = wish.get("intent", "")
                language = wish.get("language", "ro")
                
                # Verifică dacă e software/serviciu digital
                context = wish.get("context") or wish.get("full_context")
                precise_context = self.precise_extractor.extract_precise_context(
                    text=intent,
                    language=language,
                    context=context
                )
                
                if not precise_context or not precise_context.get("is_valid", False):
                    continue
                
                entity_type = precise_context.get("entity_type", "unknown")
                if entity_type not in ["software", "service"]:
                    continue
                
                print(f"[SoftwareGapFinder] Wish {wish_id} identified as software/service")
                
                # Extrage informații
                software_name = precise_context.get("entity_name", intent)
                functionality = precise_context.get("functionality", "")
                
                # Validează existența
                validation_result = await self.existence_validator.validate_software(
                    software_name=software_name,
                    functionality=functionality,
                    language=language
                )
                
                # Adaugă precise_context
                wish["precise_context"] = precise_context.get("extracted_context", {})
                
                # Detectează gap-uri
                gaps = self.gap_detector.detect_gaps(wish, validation_result)
                
                if gaps:
                    print(f"[SoftwareGapFinder] ✅ Found {len(gaps)} software gaps for wish {wish_id}")
                    for gap in gaps:
                        gap["source_wish_id"] = wish.get("id")
                        gap["category"] = precise_context.get("category", "software")
                    
                    all_gaps.extend(gaps)
                
                import asyncio
                await asyncio.sleep(1)
            
            except Exception as e:
                print(f"[ERROR] Error processing wish in batch: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return all_gaps
