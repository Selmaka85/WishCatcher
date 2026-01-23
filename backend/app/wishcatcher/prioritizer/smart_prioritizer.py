"""
Smart Prioritizer - Prioritizare multi-factor cu timing analysis
Nu doar business score, ci și urgență, timing, market readiness
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SmartPrioritizer:
    """Prioritizează wish-uri inteligent bazat pe multiple factori"""
    
    def prioritize(
        self,
        wish_data: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Prioritizează wish-ul bazat pe multiple factori
        
        Returns:
            {
                "priority_score": float,  # 0-1
                "urgency": str,  # "low", "medium", "high", "critical"
                "timing": str,  # "now", "soon", "later", "not_now"
                "market_readiness": str,  # "ready", "almost", "not_ready"
                "factors": Dict  # Detalii despre fiecare factor
            }
        """
        factors = {}
        
        # 1. Urgență
        urgency = self._calculate_urgency(wish_data, context)
        factors["urgency"] = urgency
        
        # 2. Timing
        timing = self._calculate_timing(wish_data, context)
        factors["timing"] = timing
        
        # 3. Market Readiness
        market_readiness = self._calculate_market_readiness(wish_data)
        factors["market_readiness"] = market_readiness
        
        # 4. Business Score (deja calculat)
        business_score = wish_data.get("business_score", 0.5)
        factors["business_score"] = business_score
        
        # 5. Competition Level
        competition = self._calculate_competition(wish_data)
        factors["competition"] = competition
        
        # 6. Calculează priority score
        priority_score = self._calculate_priority_score(factors)
        
        return {
            "priority_score": priority_score,
            "urgency": urgency["level"],
            "timing": timing["level"],
            "market_readiness": market_readiness["level"],
            "factors": factors
        }
    
    def _calculate_urgency(self, wish_data: Dict, context: Optional[Dict]) -> Dict:
        """Calculează urgența wish-ului"""
        trigger_analysis = wish_data.get("trigger_analysis", {})
        emotional_intensity = trigger_analysis.get("emotional_intensity", 0.5)
        
        # Verifică pattern-uri de urgență în text
        intent = wish_data.get("intent", "").lower()
        urgency_keywords = ["urgent", "urgent", "imediat", "immediately", "de mult timp", "for a while"]
        has_urgency = any(kw in intent for kw in urgency_keywords)
        
        # Calculează level
        if emotional_intensity > 0.8 or has_urgency:
            level = "critical"
            score = 1.0
        elif emotional_intensity > 0.6:
            level = "high"
            score = 0.8
        elif emotional_intensity > 0.4:
            level = "medium"
            score = 0.6
        else:
            level = "low"
            score = 0.4
        
        return {
            "level": level,
            "score": score,
            "emotional_intensity": emotional_intensity,
            "has_urgency_keywords": has_urgency
        }
    
    def _calculate_timing(self, wish_data: Dict, context: Optional[Dict]) -> Dict:
        """Calculează dacă e momentul potrivit"""
        # Verifică dacă există trend-uri sau evenimente relevante
        # Pentru acum, folosește business score ca proxy
        business_score = wish_data.get("business_score", 0.5)
        market_analysis = wish_data.get("market_analysis", {})
        market_size = market_analysis.get("market_size", "medium")
        
        # Market size mare + business score mare = timing bun
        if market_size == "large" and business_score > 0.7:
            level = "now"
            score = 1.0
        elif market_size == "medium" and business_score > 0.6:
            level = "soon"
            score = 0.8
        elif business_score > 0.5:
            level = "later"
            score = 0.6
        else:
            level = "not_now"
            score = 0.4
        
        return {
            "level": level,
            "score": score,
            "market_size": market_size,
            "business_score": business_score
        }
    
    def _calculate_market_readiness(self, wish_data: Dict) -> Dict:
        """Calculează dacă piața e pregătită"""
        market_analysis = wish_data.get("market_analysis", {})
        competition = market_analysis.get("competition", "medium")
        market_size = market_analysis.get("market_size", "medium")
        
        # Market size mare + competition scăzută = market ready
        if market_size == "large" and competition == "low":
            level = "ready"
            score = 1.0
        elif market_size == "medium" and competition in ["low", "medium"]:
            level = "almost"
            score = 0.8
        elif market_size in ["medium", "large"]:
            level = "almost"
            score = 0.7
        else:
            level = "not_ready"
            score = 0.5
        
        return {
            "level": level,
            "score": score,
            "market_size": market_size,
            "competition": competition
        }
    
    def _calculate_competition(self, wish_data: Dict) -> Dict:
        """Calculează nivelul de competiție"""
        market_analysis = wish_data.get("market_analysis", {})
        competition = market_analysis.get("competition", "medium")
        
        competition_scores = {
            "low": 1.0,  # Low competition = good
            "medium": 0.7,
            "high": 0.4
        }
        
        return {
            "level": competition,
            "score": competition_scores.get(competition, 0.5)
        }
    
    def _calculate_priority_score(self, factors: Dict) -> float:
        """Calculează priority score final"""
        # Weights pentru fiecare factor
        weights = {
            "urgency": 0.25,
            "timing": 0.20,
            "market_readiness": 0.20,
            "business_score": 0.25,
            "competition": 0.10
        }
        
        # Extrage scores
        urgency_score = factors.get("urgency", {}).get("score", 0.5)
        timing_score = factors.get("timing", {}).get("score", 0.5)
        market_readiness_score = factors.get("market_readiness", {}).get("score", 0.5)
        business_score = factors.get("business_score", 0.5)
        competition_score = factors.get("competition", {}).get("score", 0.5)
        
        # Calculare weighted sum
        priority_score = (
            urgency_score * weights["urgency"] +
            timing_score * weights["timing"] +
            market_readiness_score * weights["market_readiness"] +
            business_score * weights["business_score"] +
            competition_score * weights["competition"]
        )
        
        return min(priority_score, 1.0)
