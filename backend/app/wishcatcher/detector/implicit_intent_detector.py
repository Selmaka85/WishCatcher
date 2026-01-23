"""
Implicit Intent Detector - Detectează wish-uri din acțiuni și comportament
Nu caută formulări explicite, ci analizează ce oamenii fac (nu ce spun)
"""

import re
from typing import Dict, List, Optional
import spacy


class ImplicitIntentDetector:
    """Detectează wish-uri implicite din acțiuni și pattern-uri comportamentale"""
    
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
        
        # Pattern-uri pentru acțiuni care indică wish-uri
        self.action_patterns = {
            "ro": [
                # Căutări repetate
                r"(?:am.*căutat|am.*încercat.*să.*găsesc).*de.*(?:mult|ceva).*timp",
                r"(?:caut|am.*căutat).*de.*(?:luni|săptămâni|ani)",
                
                # Comparații între produse
                r"(?:compar|compară|comparând).*(?:între|cu)",
                r"(?:care.*e.*mai.*bun|which.*is.*better).*(?:între|between)",
                
                # Întrebări despre existență
                r"(?:există|exist).*ceva.*pentru.*(?:ce|ceva)",
                r"(?:există|exist).*aplicație.*pentru.*(?:ce|ceva)",
                r"(?:există|exist).*produs.*pentru.*(?:ce|ceva)",
                
                # Review-uri negative (indică wish pentru alternativă)
                r"(?:nu.*recomand|nu.*sugerez|don't.*recommend).*pentru.*(?:ce|ceva)",
                r"(?:e.*prost|e.*rău|it's.*bad).*pentru.*(?:ce|ceva)",
                
                # Abandon (indică wish pentru ceva mai bun)
                r"(?:am.*renunțat|am.*abandonat).*la.*(?:ce|ceva)",
                r"(?:nu.*mai.*folosesc|don't.*use.*anymore).*(?:pentru|for)",
            ],
            "en": [
                # Repeated searches
                r"(?:searched|tried.*to.*find).*for.*(?:a.*while|some.*time)",
                r"(?:looking|searching).*for.*(?:months|weeks|years)",
                
                # Product comparisons
                r"(?:compare|comparing).*(?:between|with)",
                r"(?:which.*is.*better|what's.*better).*(?:between|than)",
                
                # Existence questions
                r"(?:exists|exist).*something.*for.*(?:what|something)",
                r"(?:exists|exist).*app.*for.*(?:what|something)",
                r"(?:exists|exist).*product.*for.*(?:what|something)",
                
                # Negative reviews
                r"(?:don't.*recommend|wouldn't.*suggest).*for.*(?:what|something)",
                r"(?:it's.*bad|it's.*terrible).*for.*(?:what|something)",
                
                # Abandonment
                r"(?:gave.*up|abandoned).*on.*(?:what|something)",
                r"(?:don't.*use.*anymore|stopped.*using).*(?:for|because)",
            ]
        }
    
    def detect_implicit_wish(
        self,
        text: str,
        language: str = "ro",
        context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Detectează wish-uri implicite din acțiuni și comportament
        
        Returns:
            {
                "wish": str,
                "confidence": float,
                "type": str,  # "search_wish", "comparison_wish", "alternative_wish"
                "evidence": List[str]
            }
        """
        text_lower = text.lower()
        patterns = self.action_patterns.get(language, self.action_patterns["en"])
        
        evidence = []
        wish_type = None
        
        # Verifică pattern-uri
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                evidence.append(match.group(0))
                
                # Determină tipul
                if "căutat" in pattern or "search" in pattern:
                    wish_type = "search_wish"
                elif "compar" in pattern or "compare" in pattern:
                    wish_type = "comparison_wish"
                elif "există" in pattern or "exists" in pattern:
                    wish_type = "existence_wish"
                elif "nu.*recomand" in pattern or "don't.*recommend" in pattern:
                    wish_type = "alternative_wish"
                elif "renunțat" in pattern or "abandon" in pattern:
                    wish_type = "alternative_wish"
                else:
                    wish_type = "implicit_wish"
                break
        
        if not wish_type or not evidence:
            return None
        
        # Extrage wish-ul
        wish = self._extract_wish_from_action(text, language, wish_type, evidence)
        
        if not wish:
            return None
        
        # Calculează confidence
        confidence = self._calculate_confidence(evidence, wish_type, text)
        
        return {
            "wish": wish,
            "confidence": confidence,
            "type": wish_type,
            "evidence": evidence
        }
    
    def _extract_wish_from_action(
        self,
        text: str,
        language: str,
        wish_type: str,
        evidence: List[str]
    ) -> Optional[str]:
        """Extrage wish-ul din acțiune"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return self._extract_wish_simple(text, language)
        
        try:
            doc = nlp(text)
            
            # Pentru search wish: extrage ce caută
            if wish_type == "search_wish":
                for token in doc:
                    if token.lemma_ in ["căuta", "găsi", "search", "find"]:
                        # Găsește obiectul
                        for child in token.children:
                            if child.dep_ in ["dobj", "pobj"]:
                                return child.text
            
            # Pentru comparison wish: extrage ce ar fi ideal
            elif wish_type == "comparison_wish":
                # Caută pattern: "între X și Y" → wish pentru "ceva între X și Y"
                for token in doc:
                    if token.text.lower() in ["între", "between"]:
                        # Găsește X și Y
                        objects = [child.text for child in token.children if child.pos_ == "NOUN"]
                        if len(objects) >= 2:
                            if language == "ro":
                                return f"produs între {objects[0]} și {objects[1]}"
                            else:
                                return f"product between {objects[0]} and {objects[1]}"
            
            # Pentru existence wish: extrage ce ar trebui să existe
            elif wish_type == "existence_wish":
                for token in doc:
                    if token.lemma_ in ["exista", "exist"]:
                        # Găsește ce ar trebui să existe
                        for child in token.children:
                            if child.dep_ in ["nsubj", "dobj"]:
                                return child.text
            
            # Pentru alternative wish: extrage ce ar fi mai bun
            elif wish_type == "alternative_wish":
                # Caută pattern: "nu recomand X" → wish pentru "alternativă la X"
                for token in doc:
                    if token.lemma_ in ["recomanda", "sugera", "recommend", "suggest"]:
                        # Găsește obiectul
                        for child in token.children:
                            if child.dep_ in ["dobj", "pobj"]:
                                obj = child.text
                                if language == "ro":
                                    return f"alternativă la {obj}"
                                else:
                                    return f"alternative to {obj}"
        
        except Exception:
            pass
        
        return self._extract_wish_simple(text, language)
    
    def _extract_wish_simple(self, text: str, language: str) -> Optional[str]:
        """Extrage wish simplu (fallback)"""
        words = text.split()
        important_words = [w for w in words if len(w) > 4]
        if len(important_words) >= 3:
            return " ".join(important_words[:5])
        return None
    
    def _calculate_confidence(self, evidence: List[str], wish_type: str, text: str) -> float:
        """Calculează confidence"""
        base_confidence = 0.6  # Implicit wishes au confidence mai mare (sunt din acțiuni)
        
        if len(evidence) >= 2:
            base_confidence += 0.15
        
        if wish_type == "alternative_wish":
            base_confidence += 0.1  # Alternative wishes = wish puternic
        elif wish_type == "search_wish":
            base_confidence += 0.05  # Search wishes = wish moderat
        
        return min(base_confidence, 0.9)
