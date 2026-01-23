"""
Software Gap Storage - Stocare persistentă pentru gap-uri software identificate
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class SoftwareGapStorage:
    """Stocare pentru gap-uri software"""
    
    def __init__(self, storage_dir: str = "data/software_gaps"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.gaps_file = self.storage_dir / "software_gaps.json"
    
    def save_gaps(self, gaps: List[Dict[str, Any]]) -> int:
        """
        Salvează gap-uri software
        
        Args:
            gaps: Lista de gap-uri software
            
        Returns:
            Numărul de gap-uri salvate
        """
        if not gaps:
            return 0
        
        # Încarcă gap-uri existente
        existing_gaps = self.load_all_gaps()
        
        # Adaugă gap-uri noi (evită duplicate)
        existing_ids = {gap.get("id") for gap in existing_gaps if gap.get("id")}
        
        new_gaps = []
        for gap in gaps:
            # Generează ID dacă nu există
            if not gap.get("id"):
                gap["id"] = f"software_gap_{datetime.now().timestamp()}_{len(existing_gaps)}"
            
            # Evită duplicate
            if gap.get("id") not in existing_ids:
                gap["saved_at"] = datetime.now().isoformat()
                new_gaps.append(gap)
                existing_ids.add(gap.get("id"))
        
        # Adaugă gap-uri noi la existente
        all_gaps = existing_gaps + new_gaps
        
        # Salvează
        try:
            with open(self.gaps_file, 'w', encoding='utf-8') as f:
                json.dump(all_gaps, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[SoftwareGapStorage] Saved {len(new_gaps)} new software gaps (total: {len(all_gaps)})")
            return len(new_gaps)
        
        except Exception as e:
            print(f"[ERROR] Could not save software gaps: {e}")
            return 0
    
    def load_all_gaps(self) -> List[Dict[str, Any]]:
        """Încarcă toate gap-urile software"""
        if not self.gaps_file.exists():
            return []
        
        try:
            with open(self.gaps_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load software gaps: {e}")
            return []
    
    def get_gaps_by_type(self, gap_type: str) -> List[Dict[str, Any]]:
        """Obține gap-uri după tip"""
        all_gaps = self.load_all_gaps()
        return [gap for gap in all_gaps if gap.get("type") == gap_type]
    
    def get_gaps_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Obține gap-uri după categorie"""
        all_gaps = self.load_all_gaps()
        return [gap for gap in all_gaps if gap.get("category") == category]
    
    def get_gaps_by_opportunity_score(self, min_score: float = 0.6) -> List[Dict[str, Any]]:
        """Obține gap-uri cu opportunity score >= min_score"""
        all_gaps = self.load_all_gaps()
        return [
            gap for gap in all_gaps
            if gap.get("opportunity_score", 0.0) >= min_score
        ]
