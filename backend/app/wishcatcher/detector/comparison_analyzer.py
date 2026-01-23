"""
Comparison Analyzer - Extrage wish-uri din comparații între produse
Comparații = wish pentru ceva mai bun sau ceva între două opțiuni
"""

import re
from typing import Dict, List, Optional
import spacy


class ComparisonAnalyzer:
    """Analizează comparații pentru wish-uri"""
    
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
        
        # Pattern-uri pentru comparații
        self.comparison_patterns = {
            "ro": [
                r"(?:X|Y).*e.*bun.*dar.*lipsește.*(?:Z|ceva)",
                r"(?:ar trebui|ar fi bine).*să.*existe.*între.*(?:X|Y)",
                r"(?:ar trebui|ar fi bine).*să.*existe.*ceva.*mai.*bun",
                r"(?:comparând|compară).*(?:între|cu)",
                r"(?:care.*e.*mai.*bun).*(?:între|between)",
                r"(?:X|Y).*are.*(?:Z|ceva).*dar.*Y.*nu",
                r"(?:ar.*fi.*perfect).*dacă.*X.*ar.*avea.*Y",
            ],
            "en": [
                r"(?:X|Y).*is.*good.*but.*missing.*(?:Z|something)",
                r"(?:should|would be).*something.*between.*(?:X|Y)",
                r"(?:should|would be).*something.*better",
                r"(?:comparing|compare).*(?:between|with)",
                r"(?:which.*is.*better).*(?:between|than)",
                r"(?:X|Y).*has.*(?:Z|something).*but.*Y.*doesn't",
                r"(?:would.*be.*perfect).*if.*X.*had.*Y",
            ]
        }
    
    def analyze_comparison(
        self,
        text: str,
        language: str = "ro"
    ) -> Optional[Dict]:
        """
        Analizează comparații pentru wish-uri
        
        Returns:
            {
                "wish": str,
                "confidence": float,
                "type": str,  # "better_wish", "hybrid_wish", "feature_wish"
                "products": List[str],  # Produsele comparate
                "evidence": List[str]
            }
        """
        text_lower = text.lower()
        patterns = self.comparison_patterns.get(language, self.comparison_patterns["en"])
        
        evidence = []
        wish_type = None
        
        # Verifică pattern-uri
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                evidence.append(match.group(0))
                
                # Determină tipul
                if "între" in pattern or "between" in pattern:
                    wish_type = "hybrid_wish"
                elif "mai.*bun" in pattern or "better" in pattern:
                    wish_type = "better_wish"
                elif "lipsește" in pattern or "missing" in pattern:
                    wish_type = "feature_wish"
                else:
                    wish_type = "comparison_wish"
                break
        
        if not wish_type or not evidence:
            return None
        
        # Extrage produsele comparate și wish-ul
        products = self._extract_products(text, language)
        wish = self._extract_wish_from_comparison(text, language, wish_type, products)
        
        if not wish:
            return None
        
        confidence = 0.75  # Comparații = wish-uri moderate
        
        return {
            "wish": wish,
            "confidence": confidence,
            "type": wish_type,
            "products": products,
            "evidence": evidence
        }
    
    def _extract_products(self, text: str, language: str) -> List[str]:
        """Extrage produsele comparate"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return []
        
        try:
            doc = nlp(text)
            products = []
            
            # Găsește entități (produse)
            for ent in doc.ents:
                if ent.label_ in ["PRODUCT", "ORG", "MISC"]:
                    products.append(ent.text)
            
            # Găsește noun phrases care ar putea fi produse
            for chunk in doc.noun_chunks:
                if len(chunk.text) > 3 and chunk.text.lower() not in ["ce", "ceva", "what", "something"]:
                    if chunk.text not in products:
                        products.append(chunk.text)
            
            return products[:5]  # Max 5 produse
        
        except Exception:
            return []
    
    def _extract_wish_from_comparison(
        self,
        text: str,
        language: str,
        wish_type: str,
        products: List[str]
    ) -> Optional[str]:
        """Extrage wish-ul din comparație"""
        nlp = self.nlp_models.get(language)
        
        if wish_type == "hybrid_wish":
            # Wish pentru ceva între două produse
            if len(products) >= 2:
                if language == "ro":
                    return f"produs între {products[0]} și {products[1]}"
                else:
                    return f"product between {products[0]} and {products[1]}"
        
        elif wish_type == "better_wish":
            # Wish pentru ceva mai bun
            if language == "ro":
                return "produs mai bun decât alternativele existente"
            else:
                return "better product than existing alternatives"
        
        elif wish_type == "feature_wish":
            # Wish pentru feature lipsă
            if nlp:
                try:
                    doc = nlp(text)
                    # Găsește ce lipsește
                    for token in doc:
                        if token.lemma_ in ["lipsește", "missing", "lacks"]:
                            for child in token.children:
                                if child.dep_ in ["nsubj", "dobj"]:
                                    feature = child.text
                                    if language == "ro":
                                        return f"produs cu {feature}"
                                    else:
                                        return f"product with {feature}"
                except:
                    pass
        
        # Fallback
        if language == "ro":
            return "produs îmbunătățit bazat pe comparație"
        else:
            return "improved product based on comparison"
