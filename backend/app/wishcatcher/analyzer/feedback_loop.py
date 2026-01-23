"""
Feedback Loop System - Învață din wish-urile de succes
Track-uiește wish-uri care au devenit produse reale și ajustează scoring-ul
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class FeedbackLoop:
    """Sistem de învățare din wish-urile de succes"""
    
    def __init__(self, storage_dir: str = "data/feedback"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.storage_dir / "wish_feedback.json"
        
        # Încarcă feedback existent
        self.feedback_data = self._load_feedback()
    
    def record_success(
        self,
        wish_id: str,
        success_type: str,  # "became_product", "high_business_score", "validated"
        details: Optional[Dict] = None
    ):
        """Înregistrează un wish de succes"""
        if wish_id not in self.feedback_data:
            self.feedback_data[wish_id] = {
                "successes": [],
                "failures": [],
                "patterns": {}
            }
        
        success_record = {
            "type": success_type,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.feedback_data[wish_id]["successes"].append(success_record)
        self._save_feedback()
    
    def record_failure(
        self,
        wish_id: str,
        failure_type: str,  # "invalidated", "low_quality", "duplicate"
        details: Optional[Dict] = None
    ):
        """Înregistrează un wish eșuat"""
        if wish_id not in self.feedback_data:
            self.feedback_data[wish_id] = {
                "successes": [],
                "failures": [],
                "patterns": {}
            }
        
        failure_record = {
            "type": failure_type,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.feedback_data[wish_id]["failures"].append(failure_record)
        self._save_feedback()
    
    def get_success_patterns(self) -> Dict:
        """Returnează pattern-uri din wish-urile de succes"""
        patterns = {
            "successful_domains": {},
            "successful_sources": {},
            "successful_keywords": {},
            "successful_confidence_ranges": {}
        }
        
        for wish_id, data in self.feedback_data.items():
            if len(data["successes"]) > len(data["failures"]):
                # Wish de succes
                # TODO: Extrage pattern-uri din wish-ul de succes
                pass
        
        return patterns
    
    def adjust_scoring(
        self,
        wish_data: Dict
    ) -> float:
        """
        Ajustează scoring-ul bazat pe feedback
        
        Returns:
            Adjusted score (0-1)
        """
        base_score = wish_data.get("business_score", 0.5)
        
        # Verifică dacă există pattern-uri de succes similare
        patterns = self.get_success_patterns()
        
        # TODO: Ajustează score bazat pe pattern-uri
        # Pentru acum, returnează score-ul original
        return base_score
    
    def _load_feedback(self) -> Dict:
        """Încarcă feedback din storage"""
        if not self.feedback_file.exists():
            return {}
        
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_feedback(self):
        """Salvează feedback în storage"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Could not save feedback: {e}")
