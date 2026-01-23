"""
Workaround Detector - Detectează wish-uri din workaround-uri și hacks
Când oamenii fac workaround-uri = wish puternic pentru soluție reală
"""

import re
from typing import Dict, List, Optional
import spacy


class WorkaroundDetector:
    """Detectează wish-uri din workaround-uri și soluții temporare"""
    
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
        
        # Pattern-uri pentru workaround-uri
        self.workaround_patterns = {
            "ro": [
                # Workarounds explicite
                r"(?:folosesc|fac).*manual.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*Excel.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*Google.*Sheets.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*3.*aplicații.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*mai.*multe.*tool-uri.*pentru.*(?:ce|ceva)",
                
                # Hacks
                r"(?:am.*făcut|am.*creat).*un.*hack.*pentru.*(?:ce|ceva)",
                r"(?:am.*făcut|am.*creat).*o.*soluție.*temporară.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*workaround.*pentru.*(?:ce|ceva)",
                
                # Soluții temporare
                r"(?:temporar|temporary).*soluție.*pentru.*(?:ce|ceva)",
                r"(?:provizoriu|provisional).*soluție.*pentru.*(?:ce|ceva)",
            ],
            "en": [
                # Explicit workarounds
                r"(?:using|doing).*manually.*for.*(?:what|something)",
                r"(?:using|doing).*Excel.*for.*(?:what|something)",
                r"(?:using|doing).*Google.*Sheets.*for.*(?:what|something)",
                r"(?:using|doing).*3.*apps.*for.*(?:what|something)",
                r"(?:using|doing).*multiple.*tools.*for.*(?:what|something)",
                
                # Hacks
                r"(?:made|created).*a.*hack.*for.*(?:what|something)",
                r"(?:made|created).*a.*temporary.*solution.*for.*(?:what|something)",
                r"(?:using|doing).*workaround.*for.*(?:what|something)",
                
                # Temporary solutions
                r"(?:temporary|provisional).*solution.*for.*(?:what|something)",
            ]
        }
    
    def detect_workaround_wish(
        self,
        text: str,
        language: str = "ro"
    ) -> Optional[Dict]:
        """
        Detectează wish-uri din workaround-uri
        
        Returns:
            {
                "wish": str,  # Wish-ul pentru soluție reală
                "confidence": float,
                "workaround": str,  # Workaround-ul actual
                "evidence": List[str]
            }
        """
        text_lower = text.lower()
        patterns = self.workaround_patterns.get(language, self.workaround_patterns["en"])
        
        evidence = []
        workaround = None
        
        # Verifică pattern-uri
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                evidence.append(match.group(0))
                workaround = match.group(0)
                break
        
        if not workaround:
            return None
        
        # Extrage wish-ul (soluția reală care ar înlocui workaround-ul)
        wish = self._extract_wish_from_workaround(text, language, workaround)
        
        if not wish:
            return None
        
        # Confidence mare pentru workaround-uri (sunt wish-uri puternice)
        confidence = 0.85
        
        return {
            "wish": wish,
            "confidence": confidence,
            "workaround": workaround,
            "evidence": evidence
        }
    
    def _extract_wish_from_workaround(
        self,
        text: str,
        language: str,
        workaround: str
    ) -> Optional[str]:
        """Extrage wish-ul din workaround"""
        nlp = self.nlp_models.get(language)
        
        # Pattern: "folosesc X pentru Y" → wish pentru "X automat pentru Y" sau "soluție pentru Y"
        if "manual" in workaround.lower() or "manually" in workaround.lower():
            # Extrage ce face manual
            if language == "ro":
                return "automatizare pentru procesul manual"
            else:
                return "automation for manual process"
        
        elif "excel" in workaround.lower() or "sheets" in workaround.lower():
            # Extrage ce face în Excel
            if language == "ro":
                return "aplicație dedicată pentru gestionarea datelor"
            else:
                return "dedicated app for data management"
        
        elif "3.*aplicații" in workaround.lower() or "3.*apps" in workaround.lower():
            # Extrage ce face cu 3 aplicații
            if language == "ro":
                return "aplicație unificată pentru toate funcționalitățile"
            else:
                return "unified app for all functionalities"
        
        else:
            # Generic: extrage ce face cu workaround-ul
            if nlp:
                try:
                    doc = nlp(text)
                    # Găsește obiectul
                    for token in doc:
                        if token.lemma_ in ["face", "folosi", "do", "use"]:
                            for child in token.children:
                                if child.dep_ in ["dobj", "pobj"]:
                                    obj = child.text
                                    if language == "ro":
                                        return f"soluție automată pentru {obj}"
                                    else:
                                        return f"automatic solution for {obj}"
                except:
                    pass
        
        # Fallback
        if language == "ro":
            return "soluție automată pentru procesul manual"
        else:
            return "automatic solution for manual process"
