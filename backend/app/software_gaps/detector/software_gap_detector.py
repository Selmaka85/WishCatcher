"""
Software Gap Detector - Detectează gap-uri în software/servicii digitale
Identifică oportunități pentru software inexistent sau de calitate slabă
"""

from typing import Dict, List, Optional, Any


class SoftwareGapDetector:
    """Detectează gap-uri în software și servicii digitale"""
    
    def __init__(self):
        # Threshold-uri
        self.missing_threshold = 0.3  # Existence score < 0.3 = missing
        self.low_quality_threshold = 0.5  # Quality score < 0.5 = low quality
        self.opportunity_score_threshold = 0.6  # Minimum opportunity score
    
    def detect_gaps(
        self,
        wish_data: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detectează gap-uri software din wish și validare
        
        Args:
            wish_data: Datele wish-ului
            validation_result: Rezultatul validării existenței
            
        Returns:
            Lista de gap-uri software identificate
        """
        gaps = []
        
        gap_type = validation_result.get("gap_type", "unknown")
        existence_score = validation_result.get("existence_score", 0.0)
        quality_score = validation_result.get("quality_score", 0.0)
        
        # 1. Gap: Software complet inexistent
        if gap_type == "missing" or existence_score < self.missing_threshold:
            gap = self._create_missing_gap(wish_data, validation_result)
            if gap:
                gaps.append(gap)
        
        # 2. Gap: Software există dar e de calitate slabă
        elif gap_type == "low_quality" or (existence_score >= self.missing_threshold and quality_score < self.low_quality_threshold):
            gap = self._create_low_quality_gap(wish_data, validation_result)
            if gap:
                gaps.append(gap)
        
        # 3. Gap: Feature gap (există dar lipsește funcționalitate specifică)
        gap = self._create_feature_gap(wish_data, validation_result)
        if gap:
            gaps.append(gap)
        
        # 4. Gap: Localization gap (există dar nu e în română)
        if wish_data.get("language") == "ro":
            gap = self._create_localization_gap(wish_data, validation_result)
            if gap:
                gaps.append(gap)
        
        return gaps
    
    def _create_missing_gap(
        self,
        wish_data: Dict,
        validation_result: Dict
    ) -> Optional[Dict[str, Any]]:
        """Creează gap pentru software inexistent"""
        opportunity_score = self._calculate_opportunity_score(wish_data, validation_result, "missing")
        
        if opportunity_score < self.opportunity_score_threshold:
            return None
        
        return {
            "type": "missing",
            "gap_type": "software_missing",
            "opportunity_type": "new_software",
            "product_name": wish_data.get("intent", ""),
            "category": wish_data.get("domain", "software"),
            "description": wish_data.get("intent_full", wish_data.get("intent", "")),
            "functionality": wish_data.get("precise_context", {}).get("functionality", ""),
            "existence_score": validation_result.get("existence_score", 0.0),
            "quality_score": validation_result.get("quality_score", 0.0),
            "opportunity_score": opportunity_score,
            "platforms_checked": list(validation_result.get("platforms", {}).keys()),
            "platforms_found": [
                p for p, r in validation_result.get("platforms", {}).items()
                if r.get("exists")
            ],
            "risk_level": "low",  # Software missing = low risk (oportunitate clară)
            "feasibility": wish_data.get("feasibility", "medium"),
            "market_size": wish_data.get("market_analysis", {}).get("market_size", "medium"),
            "source_wish_id": wish_data.get("id"),
            "extracted_at": wish_data.get("timestamp")
        }
    
    def _create_low_quality_gap(
        self,
        wish_data: Dict,
        validation_result: Dict
    ) -> Optional[Dict[str, Any]]:
        """Creează gap pentru software de calitate slabă"""
        opportunity_score = self._calculate_opportunity_score(wish_data, validation_result, "low_quality")
        
        if opportunity_score < self.opportunity_score_threshold:
            return None
        
        # Găsește alternative existente (pentru referință)
        existing_alternatives = []
        for platform, result in validation_result.get("platforms", {}).items():
            if result.get("exists"):
                if platform == "github" and result.get("top_repository"):
                    existing_alternatives.append({
                        "platform": "github",
                        "name": result["top_repository"].get("name"),
                        "url": result["top_repository"].get("url"),
                        "quality_score": result.get("quality_score", 0.0)
                    })
                elif platform == "app_store" and result.get("top_app"):
                    existing_alternatives.append({
                        "platform": "app_store",
                        "name": result["top_app"].get("name"),
                        "url": result["top_app"].get("url"),
                        "quality_score": result.get("quality_score", 0.0)
                    })
        
        return {
            "type": "low_quality",
            "gap_type": "software_low_quality",
            "opportunity_type": "better_software",
            "product_name": wish_data.get("intent", ""),
            "category": wish_data.get("domain", "software"),
            "description": wish_data.get("intent_full", wish_data.get("intent", "")),
            "functionality": wish_data.get("precise_context", {}).get("functionality", ""),
            "existence_score": validation_result.get("existence_score", 0.0),
            "quality_score": validation_result.get("quality_score", 0.0),
            "opportunity_score": opportunity_score,
            "existing_alternatives": existing_alternatives,
            "platforms_checked": list(validation_result.get("platforms", {}).keys()),
            "risk_level": "medium",  # Low quality = medium risk (trebuie să fii mai bun)
            "feasibility": wish_data.get("feasibility", "medium"),
            "market_size": wish_data.get("market_analysis", {}).get("market_size", "medium"),
            "source_wish_id": wish_data.get("id"),
            "extracted_at": wish_data.get("timestamp")
        }
    
    def _create_feature_gap(
        self,
        wish_data: Dict,
        validation_result: Dict
    ) -> Optional[Dict[str, Any]]:
        """Creează gap pentru funcționalitate lipsă"""
        # Verifică dacă există software dar lipsește funcționalitate specifică
        functionality = wish_data.get("precise_context", {}).get("functionality", "")
        if not functionality:
            return None
        
        # Dacă există software dar funcționalitatea nu e menționată în descrieri
        platforms = validation_result.get("platforms", {})
        has_software = any(r.get("exists") for r in platforms.values())
        
        if not has_software:
            return None  # Nu e feature gap dacă nu există deloc
        
        # Verifică dacă funcționalitatea e menționată în descrieri
        functionality_keywords = set(functionality.lower().split())
        mentions_functionality = False
        
        for platform, result in platforms.items():
            if result.get("exists"):
                description = ""
                if platform == "github" and result.get("top_repository"):
                    description = result["top_repository"].get("description", "").lower()
                elif platform == "app_store" and result.get("top_app"):
                    description = result["top_app"].get("description", "").lower()
                
                if description:
                    desc_keywords = set(description.split())
                    if functionality_keywords.intersection(desc_keywords):
                        mentions_functionality = True
                        break
        
        # Dacă există software dar nu menționează funcționalitatea = feature gap
        if has_software and not mentions_functionality:
            opportunity_score = self._calculate_opportunity_score(wish_data, validation_result, "feature_gap")
            
            if opportunity_score >= self.opportunity_score_threshold:
                return {
                    "type": "feature_gap",
                    "gap_type": "software_feature_missing",
                    "opportunity_type": "feature_addition",
                    "product_name": wish_data.get("intent", ""),
                    "category": wish_data.get("domain", "software"),
                    "description": wish_data.get("intent_full", wish_data.get("intent", "")),
                    "missing_functionality": functionality,
                    "existence_score": validation_result.get("existence_score", 0.0),
                    "quality_score": validation_result.get("quality_score", 0.0),
                    "opportunity_score": opportunity_score,
                    "platforms_checked": list(platforms.keys()),
                    "risk_level": "low",  # Feature gap = low risk
                    "feasibility": wish_data.get("feasibility", "medium"),
                    "source_wish_id": wish_data.get("id"),
                    "extracted_at": wish_data.get("timestamp")
                }
        
        return None
    
    def _create_localization_gap(
        self,
        wish_data: Dict,
        validation_result: Dict
    ) -> Optional[Dict[str, Any]]:
        """Creează gap pentru localizare (există dar nu e în română)"""
        # Verifică dacă există software dar nu e localizat în română
        platforms = validation_result.get("platforms", {})
        
        # Verifică App Store (are informații despre localizare)
        app_store_result = platforms.get("app_store", {})
        if app_store_result.get("exists"):
            # Dacă există pe App Store dar nu e în română = localization gap
            # (simplificat - în realitate ar trebui să verificăm limba aplicației)
            opportunity_score = self._calculate_opportunity_score(wish_data, validation_result, "localization")
            
            if opportunity_score >= self.opportunity_score_threshold:
                return {
                    "type": "localization_gap",
                    "gap_type": "software_not_localized",
                    "opportunity_type": "localization",
                    "product_name": wish_data.get("intent", ""),
                    "category": wish_data.get("domain", "software"),
                    "description": wish_data.get("intent_full", wish_data.get("intent", "")),
                    "target_language": "ro",
                    "existence_score": validation_result.get("existence_score", 0.0),
                    "quality_score": validation_result.get("quality_score", 0.0),
                    "opportunity_score": opportunity_score,
                    "risk_level": "low",  # Localization = low risk
                    "feasibility": "high",  # Localization e fezabil
                    "source_wish_id": wish_data.get("id"),
                    "extracted_at": wish_data.get("timestamp")
                }
        
        return None
    
    def _calculate_opportunity_score(
        self,
        wish_data: Dict,
        validation_result: Dict,
        gap_type: str
    ) -> float:
        """Calculează scorul de oportunitate (0-1)"""
        score = 0.0
        
        # Business score (0.3)
        business_score = wish_data.get("business_score", 0.5)
        score += business_score * 0.3
        
        # Frequency (0.2)
        frequency = wish_data.get("frequency", 1)
        if frequency >= 5:
            score += 0.2
        elif frequency >= 3:
            score += 0.15
        elif frequency >= 2:
            score += 0.1
        
        # Market size (0.2)
        market_size = wish_data.get("market_analysis", {}).get("market_size", "medium")
        if market_size == "large":
            score += 0.2
        elif market_size == "medium":
            score += 0.15
        else:
            score += 0.1
        
        # Feasibility (0.2)
        feasibility = wish_data.get("feasibility", "medium")
        if feasibility == "high":
            score += 0.2
        elif feasibility == "medium":
            score += 0.15
        else:
            score += 0.1
        
        # Gap type bonus (0.1)
        if gap_type == "missing":
            score += 0.1  # Missing = mai mare oportunitate
        elif gap_type == "low_quality":
            score += 0.05  # Low quality = oportunitate moderată
        
        return min(score, 1.0)
