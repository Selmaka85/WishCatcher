"""
Market Research Validator - Validează wish-uri cu date externe
Google Trends, SimilarWeb, Crunchbase pentru validare
"""

import requests
from typing import Dict, Optional
import os
from datetime import datetime, timedelta


class MarketResearchValidator:
    """Validează wish-uri cu market research extern"""
    
    def __init__(self):
        self.google_trends_api_key = os.getenv("GOOGLE_TRENDS_API_KEY")
        self.similarweb_api_key = os.getenv("SIMILARWEB_API_KEY")
        self.crunchbase_api_key = os.getenv("CRUNCHBASE_API_KEY")
    
    def validate_wish(
        self,
        wish: str,
        language: str = "ro",
        country: str = "RO"
    ) -> Dict:
        """
        Validează wish-ul cu market research
        
        Returns:
            {
                "is_valid": bool,
                "trending": Optional[bool],  # E trending pe Google?
                "market_size": Optional[str],  # "small", "medium", "large"
                "competition": Optional[str],  # "low", "medium", "high"
                "similar_startups": Optional[int],  # Câte startup-uri similare există
                "confidence": float,
                "evidence": Dict
            }
        """
        evidence = {}
        
        # 1. Google Trends (dacă e disponibil)
        trending = self._check_google_trends(wish, country)
        if trending is not None:
            evidence["trending"] = trending
        
        # 2. SimilarWeb (dacă e disponibil)
        market_data = self._check_similarweb(wish)
        if market_data:
            evidence.update(market_data)
        
        # 3. Crunchbase (dacă e disponibil)
        startups_count = self._check_crunchbase(wish)
        if startups_count is not None:
            evidence["similar_startups"] = startups_count
        
        # 4. Calculează validare
        is_valid, confidence = self._calculate_validation(evidence)
        
        return {
            "is_valid": is_valid,
            "trending": evidence.get("trending"),
            "market_size": evidence.get("market_size"),
            "competition": evidence.get("competition"),
            "similar_startups": evidence.get("similar_startups"),
            "confidence": confidence,
            "evidence": evidence
        }
    
    def _check_google_trends(self, wish: str, country: str) -> Optional[bool]:
        """Verifică dacă wish-ul e trending pe Google Trends"""
        # Notă: Google Trends nu are API oficial gratuit
        # Alternativă: folosește pytrends library sau scraping
        
        # Pentru acum, returnează None (necesită implementare)
        # TODO: Implementează cu pytrends dacă e necesar
        return None
    
    def _check_similarweb(self, wish: str) -> Optional[Dict]:
        """Verifică market data pe SimilarWeb"""
        # SimilarWeb are API plătit
        # Pentru acum, returnează None
        # TODO: Implementează dacă ai API key
        return None
    
    def _check_crunchbase(self, wish: str) -> Optional[int]:
        """Verifică câte startup-uri similare există pe Crunchbase"""
        # Crunchbase are API plătit
        # Pentru acum, returnează None
        # TODO: Implementează dacă ai API key
        return None
    
    def _calculate_validation(self, evidence: Dict) -> tuple:
        """Calculează validare bazată pe evidență"""
        if not evidence:
            return True, 0.5  # Default: valid, confidence mediu
        
        # Trending = valid
        if evidence.get("trending") is True:
            return True, 0.8
        
        # Market size mare = valid
        if evidence.get("market_size") == "large":
            return True, 0.85
        
        # Competition scăzută = valid
        if evidence.get("competition") == "low":
            return True, 0.8
        
        # Puține startup-uri similare = valid (oportunitate)
        if evidence.get("similar_startups", 999) < 5:
            return True, 0.75
        
        # Default
        return True, 0.6
