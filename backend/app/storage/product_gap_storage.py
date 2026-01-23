"""
Storage pentru Product Gaps identificate automat
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ProductGapStorage:
    """Stocare gap-uri identificate"""
    
    def __init__(self, storage_dir: str = "data/product_gaps"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.gaps_file = self.storage_dir / "gaps.json"
        self.index_file = self.storage_dir / "gaps_index.json"
        self.index: Dict[str, List[str]] = self._load_index()
    
    def _load_index(self) -> Dict[str, List[str]]:
        """Încarcă index-ul gap-urilor"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        """Salvează index-ul"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    def save_gaps(self, gaps: List[Dict[str, Any]]) -> int:
        """
        Salvează gap-uri identificate
        
        Args:
            gaps: Lista de gap-uri
            
        Returns:
            Număr de gap-uri noi salvate
        """
        if not gaps:
            return 0
        
        # Încarcă gap-uri existente
        existing_gaps = self.load_all_gaps()
        
        # Creează set de gap-uri existente (după product_name + from_marketplace + to_marketplace)
        existing_keys = {
            (g.get("product_name"), g.get("from_marketplace"), g.get("to_marketplace"))
            for g in existing_gaps
        }
        
        # Filtrează gap-uri noi
        new_gaps = []
        for gap in gaps:
            key = (gap.get("product_name"), gap.get("from_marketplace"), gap.get("to_marketplace"))
            if key not in existing_keys:
                gap["id"] = f"gap_{len(existing_gaps) + len(new_gaps)}_{int(datetime.now().timestamp())}"
                gap["created_at"] = datetime.now().isoformat()
                new_gaps.append(gap)
                existing_keys.add(key)
        
        if not new_gaps:
            print(f"[ProductGapStorage] No new gaps to save")
            return 0
        
        # Adaugă gap-uri noi
        all_gaps = existing_gaps + new_gaps
        
        # Salvează
        with open(self.gaps_file, 'w', encoding='utf-8') as f:
            json.dump(all_gaps, f, indent=2, ensure_ascii=False, default=str)
        
        # Actualizează index
        for gap in new_gaps:
            product_name = gap.get("product_name", "unknown")
            if product_name not in self.index:
                self.index[product_name] = []
            self.index[product_name].append(gap.get("id"))
        
        self._save_index()
        
        print(f"[ProductGapStorage] Saved {len(new_gaps)} new gaps (total: {len(all_gaps)})")
        return len(new_gaps)
    
    def load_all_gaps(self) -> List[Dict[str, Any]]:
        """Încarcă toate gap-urile"""
        if not self.gaps_file.exists():
            return []
        
        try:
            with open(self.gaps_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ProductGapStorage] Error loading gaps: {e}")
            return []
    
    def get_gaps_by_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Obține gap-uri pentru un produs specific"""
        all_gaps = self.load_all_gaps()
        return [g for g in all_gaps if g.get("product_name") == product_name]
    
    def get_gaps_by_type(self, gap_type: str) -> List[Dict[str, Any]]:
        """Obține gap-uri după tip (missing, expensive, etc.)"""
        all_gaps = self.load_all_gaps()
        return [g for g in all_gaps if g.get("type") == gap_type]
    
    def get_gaps_by_opportunity(self, opportunity_type: str) -> List[Dict[str, Any]]:
        """Obține gap-uri după tip oportunitate (fba_import, export, etc.)"""
        all_gaps = self.load_all_gaps()
        return [g for g in all_gaps if g.get("opportunity_type") == opportunity_type]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obține statistici despre gap-uri"""
        gaps = self.load_all_gaps()
        
        if not gaps:
            return {
                "total": 0,
                "by_type": {},
                "by_opportunity": {},
                "by_marketplace": {}
            }
        
        by_type = {}
        by_opportunity = {}
        by_marketplace = {}
        
        for gap in gaps:
            gap_type = gap.get("type", "unknown")
            by_type[gap_type] = by_type.get(gap_type, 0) + 1
            
            opp_type = gap.get("opportunity_type", "unknown")
            by_opportunity[opp_type] = by_opportunity.get(opp_type, 0) + 1
            
            from_mkt = gap.get("from_marketplace", "unknown")
            to_mkt = gap.get("to_marketplace", "unknown")
            key = f"{from_mkt} → {to_mkt}"
            by_marketplace[key] = by_marketplace.get(key, 0) + 1
        
        return {
            "total": len(gaps),
            "by_type": by_type,
            "by_opportunity": by_opportunity,
            "by_marketplace": by_marketplace
        }
