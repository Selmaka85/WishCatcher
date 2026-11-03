"""
Wish Storage - Stocare persistentă pentru wish-uri
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.api.models import WishData, WishResponse

class WishStorage:
    """Stocare wish-uri în fișiere JSON"""
    
    def __init__(self, storage_dir: str = "data/wishes"):
        """
        Inițializează storage
        
        Args:
            storage_dir: Directorul unde se salvează wish-urile
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Fișier principal pentru toate wish-urile
        self.wishes_file = self.storage_dir / "wishes.json"
        
        # Folder pentru wish-uri individuale (pentru backup)
        self.individual_dir = self.storage_dir / "individual"
        self.individual_dir.mkdir(parents=True, exist_ok=True)
    
    def save_wishes(self, wishes: List[WishData]) -> None:
        """
        Salvează wish-uri în fișier JSON
        
        Args:
            wishes: Lista de wish-uri de salvat
        """
        # Încarcă wish-uri existente
        existing_wishes = self.load_all_wishes()
        
        # Adaugă wish-uri noi (evită duplicate după ID)
        existing_ids = {w.id for w in existing_wishes}
        new_wishes = [w for w in wishes if w.id not in existing_ids]
        
        if not new_wishes:
            print(f"[Storage] Nu sunt wish-uri noi de salvat")
            return
        
        # Adaugă wish-uri noi
        all_wishes = existing_wishes + new_wishes
        
        # Salvează în fișier principal
        wishes_dict = [self._wish_to_dict(w) for w in all_wishes]
        
        with open(self.wishes_file, 'w', encoding='utf-8') as f:
            json.dump(wishes_dict, f, indent=2, ensure_ascii=False, default=str)
        
        # Salvează wish-uri individuale (pentru backup și acces rapid)
        for wish in new_wishes:
            self._save_individual_wish(wish)
        
        print(f"[Storage] Salvate {len(new_wishes)} wish-uri noi (total: {len(all_wishes)})")
    
    def load_all_wishes(self) -> List[WishData]:
        """
        Încarcă toate wish-urile din storage
        
        Returns:
            Lista de wish-uri
        """
        if not self.wishes_file.exists():
            return []
        
        try:
            with open(self.wishes_file, 'r', encoding='utf-8') as f:
                wishes_dict = json.load(f)
            
            wishes = [self._dict_to_wish(w) for w in wishes_dict]
            return wishes
        except Exception as e:
            print(f"[Storage] Eroare la încărcare: {e}")
            return []
    
    def get_wish(self, wish_id: str) -> Optional[WishData]:
        """
        Obține un wish specific după ID
        
        Args:
            wish_id: ID-ul wish-ului
            
        Returns:
            WishData sau None dacă nu există
        """
        wishes = self.load_all_wishes()
        for wish in wishes:
            if wish.id == wish_id:
                return wish
        return None
    
    def list_wishes(
        self, 
        limit: int = 100, 
        offset: int = 0,
        source: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[WishData]:
        """
        Listează wish-uri cu filtre și paginare
        
        Args:
            limit: Număr maxim de wish-uri
            offset: Offset pentru paginare
            source: Filtru după sursă
            domain: Filtru după domeniu
            
        Returns:
            Lista de wish-uri filtrate
        """
        wishes = self.load_all_wishes()
        
        # Aplică filtre
        if source:
            wishes = [w for w in wishes if w.source == source]
        
        if domain:
            wishes = [w for w in wishes if w.domain == domain]
        
        # Sortează după business_score (descrescător)
        wishes.sort(key=lambda w: w.business_score, reverse=True)
        
        # Paginare
        return wishes[offset:offset + limit]
    
    def _save_individual_wish(self, wish: WishData) -> None:
        """Salvează un wish individual în fișier separat"""
        wish_file = self.individual_dir / f"{wish.id}.json"
        
        wish_dict = self._wish_to_dict(wish)
        
        with open(wish_file, 'w', encoding='utf-8') as f:
            json.dump(wish_dict, f, indent=2, ensure_ascii=False, default=str)
    
    def _wish_to_dict(self, wish: WishData) -> Dict[str, Any]:
        """Convertește WishData la dict pentru JSON"""
        result = {
            "id": wish.id,
            "intent": wish.intent,
            "domain": wish.domain,
            "score": wish.score,
            "business_score": wish.business_score,
            "technologies": wish.technologies,
            "feasibility": wish.feasibility,
            "trigger_analysis": wish.trigger_analysis.model_dump() if wish.trigger_analysis else None,
            "source": wish.source,
            "timestamp": wish.timestamp.isoformat() if isinstance(wish.timestamp, datetime) else str(wish.timestamp),
            "frequency": wish.frequency,
            "market_analysis": wish.market_analysis,
            "monetization": wish.monetization,
            "context_frame": wish.context_frame,
        }
        
        # Adaugă câmpurile noi dacă există
        if hasattr(wish, 'intent_full') and wish.intent_full:
            result["intent_full"] = wish.intent_full
        if hasattr(wish, 'structured') and wish.structured:
            result["structured"] = wish.structured
        
        # Adaugă câmpurile de prioritizare și validare
        if hasattr(wish, 'priority_score') and wish.priority_score is not None:
            result["priority_score"] = wish.priority_score
        if hasattr(wish, 'urgency') and wish.urgency:
            result["urgency"] = wish.urgency
        if hasattr(wish, 'timing') and wish.timing:
            result["timing"] = wish.timing
        if hasattr(wish, 'market_readiness') and wish.market_readiness:
            result["market_readiness"] = wish.market_readiness
        if hasattr(wish, 'market_validation') and wish.market_validation:
            result["market_validation"] = wish.market_validation
        
        return result
    
    def _dict_to_wish(self, wish_dict: Dict[str, Any]) -> WishData:
        """Convertește dict la WishData"""
        # Parse timestamp
        if isinstance(wish_dict.get("timestamp"), str):
            try:
                wish_dict["timestamp"] = datetime.fromisoformat(wish_dict["timestamp"])
            except:
                wish_dict["timestamp"] = datetime.now()
        
        # Parse trigger_analysis
        if wish_dict.get("trigger_analysis"):
            from app.api.models import TriggerAnalysis
            try:
                if isinstance(wish_dict["trigger_analysis"], dict):
                    wish_dict["trigger_analysis"] = TriggerAnalysis(**wish_dict["trigger_analysis"])
                else:
                    wish_dict["trigger_analysis"] = None
            except Exception as e:
                print(f"[Storage] Warning: Could not parse trigger_analysis: {e}")
                wish_dict["trigger_analysis"] = None
        
        # Păstrează câmpurile noi (intent_full, structured) dacă există
        # Acestea sunt opționale în model, deci nu vor cauza erori
        
        # Păstrează câmpurile de prioritizare și validare dacă există
        # Acestea sunt opționale în model, deci nu vor cauza erori
        
        return WishData(**wish_dict)
    
    def export_to_json(self, output_file: str = "data/wishes_export.json") -> str:
        """
        Exportă toate wish-urile într-un fișier JSON
        
        Args:
            output_file: Path-ul fișierului de export
            
        Returns:
            Path-ul fișierului exportat
        """
        wishes = self.load_all_wishes()
        wishes_dict = [self._wish_to_dict(w) for w in wishes]
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "export_date": datetime.now().isoformat(),
                "total": len(wishes),
                "wishes": wishes_dict
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"[Storage] Exportat {len(wishes)} wish-uri în {output_path}")
        return str(output_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obține statistici despre wish-uri
        
        Returns:
            Dict cu statistici
        """
        wishes = self.load_all_wishes()
        
        if not wishes:
            return {
                "total": 0,
                "by_source": {},
                "by_domain": {},
                "avg_business_score": 0.0
            }
        
        # Statistici după sursă
        by_source = {}
        for wish in wishes:
            by_source[wish.source] = by_source.get(wish.source, 0) + 1
        
        # Statistici după domeniu
        by_domain = {}
        for wish in wishes:
            by_domain[wish.domain] = by_domain.get(wish.domain, 0) + 1
        
        # Business score mediu
        avg_score = sum(w.business_score for w in wishes) / len(wishes)
        
        return {
            "total": len(wishes),
            "by_source": by_source,
            "by_domain": by_domain,
            "avg_business_score": round(avg_score, 3)
        }
