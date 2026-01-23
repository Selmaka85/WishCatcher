"""
Negative Space Analyzer - Identifică ce lipsește din piață
Analizează categorii de produse/servicii și identifică gap-uri
"""

from typing import Dict, List, Optional
import spacy


class NegativeSpaceAnalyzer:
    """Identifică ce lipsește din piață (negative space)"""
    
    def __init__(self):
        self.nlp_models = {}
        try:
            self.nlp_models["ro"] = spacy.load("ro_core_news_sm")
        except OSError:
            pass
        try:
            self.nlp_models["en"] = spacy.load("en_core_web_sm")
        except OSError:
            pass
        
        # Categorii de produse/servicii cunoscute
        self.product_categories = {
            "ro": [
                "software", "aplicație", "app", "platformă", "serviciu",
                "produs", "tool", "serviciu", "echipament", "device"
            ],
            "en": [
                "software", "application", "app", "platform", "service",
                "product", "tool", "equipment", "device"
            ]
        }
    
    def analyze_negative_space(
        self,
        wish_data_list: List[Dict],
        language: str = "ro"
    ) -> List[Dict]:
        """
        Analizează wish-urile pentru a identifica gap-uri în piață
        
        Args:
            wish_data_list: Lista de wish-uri deja colectate
            language: Limba analiză
        
        Returns:
            Lista de gap-uri identificate
        """
        gaps = []
        
        # 1. Grupează wish-uri după categorie
        categories = self._group_by_category(wish_data_list, language)
        
        # 2. Identifică categorii cu multe wish-uri (indică gap)
        for category, wishes in categories.items():
            if len(wishes) >= 3:  # Cel puțin 3 wish-uri în aceeași categorie
                gap = self._identify_gap(category, wishes, language)
                if gap:
                    gaps.append(gap)
        
        # 3. Identifică funcționalități care lipsesc (din comparații)
        missing_features = self._identify_missing_features(wish_data_list, language)
        gaps.extend(missing_features)
        
        return gaps
    
    def _group_by_category(self, wish_data_list: List[Dict], language: str) -> Dict[str, List[Dict]]:
        """Grupează wish-uri după categorie"""
        categories = {}
        
        for wish in wish_data_list:
            intent = wish.get("intent", "").lower()
            domain = wish.get("domain", "other")
            
            # Determină categoria
            category = domain  # Default: domain
            
            # Verifică dacă intent-ul menționează o categorie specifică
            keywords = self.product_categories.get(language, self.product_categories["en"])
            for keyword in keywords:
                if keyword in intent:
                    category = keyword
                    break
            
            if category not in categories:
                categories[category] = []
            categories[category].append(wish)
        
        return categories
    
    def _identify_gap(self, category: str, wishes: List[Dict], language: str) -> Optional[Dict]:
        """Identifică gap-ul în categorie"""
        # Analizează wish-urile pentru a identifica ce lipsește
        common_patterns = []
        
        for wish in wishes:
            intent = wish.get("intent", "")
            structured = wish.get("structured", {})
            problem = structured.get("problem", "")
            
            if problem:
                common_patterns.append(problem)
        
        # Găsește pattern-ul cel mai comun
        if common_patterns:
            from collections import Counter
            pattern_counts = Counter(common_patterns)
            most_common = pattern_counts.most_common(1)[0]
            
            if most_common[1] >= 2:  # Cel puțin 2 wish-uri cu același pattern
                return {
                    "category": category,
                    "gap": most_common[0],
                    "wish_count": len(wishes),
                    "confidence": min(most_common[1] / len(wishes), 1.0),
                    "wishes": [w.get("id") for w in wishes]
                }
        
        return None
    
    def _identify_missing_features(self, wish_data_list: List[Dict], language: str) -> List[Dict]:
        """Identifică funcționalități care lipsesc"""
        missing_features = []
        
        # Analizează wish-urile pentru funcționalități lipsă
        feature_patterns = {}
        
        for wish in wish_data_list:
            structured = wish.get("structured", {})
            key_features = structured.get("key_features", [])
            
            for feature in key_features:
                if feature not in feature_patterns:
                    feature_patterns[feature] = []
                feature_patterns[feature].append(wish.get("id"))
        
        # Găsește funcționalități care apar în multiple wish-uri (indică gap)
        for feature, wish_ids in feature_patterns.items():
            if len(wish_ids) >= 2:
                missing_features.append({
                    "type": "missing_feature",
                    "feature": feature,
                    "wish_count": len(wish_ids),
                    "confidence": min(len(wish_ids) / 10, 1.0),
                    "wishes": wish_ids
                })
        
        return missing_features
