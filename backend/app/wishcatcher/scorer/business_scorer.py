"""
Business Scorer - Calculează scor business (frecvență + monetizare + fezabilitate)
"""

from typing import Dict, Any
from app.api.models import Feasibility, MarketSize


class BusinessScorer:
    """Calculează scor business pentru wish-uri"""
    
    def calculate_business_score(self, wish_data: Dict[str, Any]) -> float:
        """
        Calculează scor total business
        
        Formula: Frecvență (40%) + Monetizare (40%) + Fezabilitate (20%)
        """
        frequency_score = self._calculate_frequency_score(wish_data)
        monetization_score = self._calculate_monetization_score(wish_data)
        feasibility_score = self._calculate_feasibility_score(wish_data)
        
        # Weighted sum
        total_score = (
            frequency_score * 0.4 +
            monetization_score * 0.4 +
            feasibility_score * 0.2
        )
        
        return min(total_score, 1.0)
    
    def _calculate_frequency_score(self, wish_data: Dict) -> float:
        """Calculează scor frecvență (0-1)"""
        frequency = wish_data.get("frequency", 1)
        
        # Normalize frequency (0-1000 range)
        if frequency >= 100:
            return 1.0
        elif frequency >= 50:
            return 0.8
        elif frequency >= 20:
            return 0.6
        elif frequency >= 10:
            return 0.4
        else:
            return 0.2
    
    def _calculate_monetization_score(self, wish_data: Dict) -> float:
        """Calculează scor monetizare (0-1)"""
        monetization = wish_data.get("monetization", {})
        
        # Willingness to pay (din trigger analysis)
        trigger_analysis = wish_data.get("trigger_analysis", {})
        emotional_intensity = trigger_analysis.get("emotional_intensity", 0.5)
        
        # Market size
        market_analysis = wish_data.get("market_analysis", {})
        market_size = market_analysis.get("market_size", "medium")
        
        market_score = {
            "small": 0.3,
            "medium": 0.6,
            "large": 1.0
        }.get(market_size, 0.6)
        
        # Urgency (din emotional intensity)
        urgency_score = emotional_intensity
        
        # Combined
        monetization_score = (market_score * 0.5 + urgency_score * 0.5)
        
        return min(monetization_score, 1.0)
    
    def _calculate_feasibility_score(self, wish_data: Dict) -> float:
        """Calculează scor fezabilitate (0-1)"""
        feasibility = wish_data.get("feasibility", {})
        
        tech = feasibility.get("tech", "medium")
        cost = feasibility.get("cost", "medium")
        time = feasibility.get("time", "medium")
        
        tech_score = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4,
            "impossible": 0.0
        }.get(tech, 0.7)
        
        cost_score = {
            "low": 1.0,
            "medium": 0.7,
            "high": 0.4
        }.get(cost, 0.7)
        
        time_score = {
            "1-2 months": 1.0,
            "2-3 months": 0.9,
            "3-6 months": 0.7,
            "6+ months": 0.4
        }.get(time, 0.7)
        
        # Average
        feasibility_score = (tech_score + cost_score + time_score) / 3
        
        return feasibility_score
    
    def get_feasibility(self, wish_data: Dict) -> Feasibility:
        """Obține feasibility level"""
        score = self._calculate_feasibility_score(wish_data)
        
        if score >= 0.8:
            return Feasibility.HIGH
        elif score >= 0.5:
            return Feasibility.MEDIUM
        elif score >= 0.2:
            return Feasibility.LOW
        else:
            return Feasibility.IMPOSSIBLE
    
    def get_market_analysis(self, wish_data: Dict) -> Dict:
        """Generează analiză de piață"""
        trigger_analysis = wish_data.get("trigger_analysis", {})
        context = trigger_analysis.get("context", {})
        
        # Infer market size from frequency
        frequency = wish_data.get("frequency", 1)
        if frequency >= 100:
            market_size = "large"
        elif frequency >= 20:
            market_size = "medium"
        else:
            market_size = "small"
        
        return {
            "market_size": market_size,
            "target_demographic": context.get("role", "general"),
            "geographic_scope": "regional",  # Default
            "competition": "medium"  # Default
        }
    
    def get_monetization_analysis(self, wish_data: Dict) -> Dict:
        """Generează analiză monetizare"""
        trigger_analysis = wish_data.get("trigger_analysis", {})
        emotional_intensity = trigger_analysis.get("emotional_intensity", 0.5)
        
        # Infer pricing from urgency
        if emotional_intensity > 0.7:
            price = "€15-30/mo"
            model = "subscription"
        elif emotional_intensity > 0.4:
            price = "€5-15/mo"
            model = "subscription"
        else:
            price = "€10-20 one-time"
            model = "one-time"
        
        return {
            "model": model,
            "estimated_price": price,
            "potential_revenue": "€50K-200K/an"  # Default estimate
        }
