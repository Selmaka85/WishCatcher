"""
Proactive Wish Detector - Detectează wish-uri înainte să fie exprimate explicit
Analizează pattern-uri care preced wish-urile (frustrare crescândă, failed attempts, etc.)
"""

import re
from typing import Dict, List, Optional, Tuple
import spacy


class ProactiveWishDetector:
    """Detectează wish-uri proactiv din pattern-uri de frustrare și eșecuri"""
    
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
        
        # Pattern-uri care preced wish-uri
        self.pre_wish_patterns = {
            "ro": [
                # Frustrare crescândă
                r"(?:am încercat|am testat|am folosit).*dar.*nu.*funcționează",
                r"(?:am încercat|am testat|am folosit).*dar.*e.*prost",
                r"(?:am încercat|am testat|am folosit).*dar.*nu.*rezolvă",
                r"(?:m-am săturat|m-am plictisit).*de.*(?:să|să fac)",
                r"(?:e frustrant|e enervant|e complicat).*să.*(?:fac|folosesc)",
                
                # Failed attempts
                r"(?:am căutat|am încercat să găsesc).*dar.*nu.*există",
                r"(?:am căutat|am încercat să găsesc).*dar.*nu.*am.*găsit",
                r"(?:nu.*găsesc|nu.*există).*pentru.*(?:ce|ceva)",
                
                # Workarounds (indică wish implicit)
                r"(?:folosesc|fac).*manual.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*Excel.*pentru.*(?:ce|ceva)",
                r"(?:folosesc|fac).*3.*aplicații.*pentru.*(?:ce|ceva)",
                r"(?:am.*nevoie|trebuie).*să.*(?:fac|folosesc).*manual",
                
                # Comparisons (indică wish pentru ceva mai bun)
                r"(?:X|Y).*e.*bun.*dar.*lipsește.*(?:Z|ceva)",
                r"(?:ar trebui|ar fi bine).*să.*existe.*între.*(?:X|Y)",
                r"(?:ar trebui|ar fi bine).*să.*existe.*ceva.*mai.*bun",
            ],
            "en": [
                # Growing frustration
                r"(?:tried|tested|used).*but.*doesn't.*work",
                r"(?:tried|tested|used).*but.*it's.*bad",
                r"(?:tried|tested|used).*but.*doesn't.*solve",
                r"(?:getting.*tired|sick.*of).*(?:doing|using)",
                r"(?:frustrating|annoying|complicated).*(?:to|doing)",
                
                # Failed attempts
                r"(?:searched|tried.*to.*find).*but.*doesn't.*exist",
                r"(?:searched|tried.*to.*find).*but.*couldn't.*find",
                r"(?:can't.*find|doesn't.*exist).*for.*(?:what|something)",
                
                # Workarounds
                r"(?:using|doing).*manually.*for.*(?:what|something)",
                r"(?:using|doing).*Excel.*for.*(?:what|something)",
                r"(?:using|doing).*3.*apps.*for.*(?:what|something)",
                r"(?:need|have.*to).*(?:do|use).*manually",
                
                # Comparisons
                r"(?:X|Y).*is.*good.*but.*missing.*(?:Z|something)",
                r"(?:should|would.*be).*something.*between.*(?:X|Y)",
                r"(?:should|would.*be).*something.*better",
            ]
        }
        
        # Pattern-uri pentru "wish în devenire"
        self.emerging_wish_patterns = {
            "ro": [
                r"(?:de.*mult.*timp|de.*ceva.*timp).*(?:caut|am.*nevoie)",
                r"(?:ar.*trebui|ar.*fi.*bine).*să.*existe",
                r"(?:nu.*înțeleg|nu.*știu).*de.*ce.*nu.*există",
                r"(?:sunt.*sigur|cred).*că.*ar.*fi.*util",
            ],
            "en": [
                r"(?:for.*a.*while|for.*some.*time).*(?:looking|need)",
                r"(?:should|would.*be).*if.*existed",
                r"(?:don't.*understand|don't.*know).*why.*doesn't.*exist",
                r"(?:sure|think).*it.*would.*be.*useful",
            ]
        }
    
    def detect_proactive_wish(
        self,
        text: str,
        language: str = "ro",
        context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Detectează wish-uri proactiv din pattern-uri de frustrare/eșec
        
        Returns:
            {
                "wish": str,  # Wish-ul dedus
                "confidence": float,
                "type": str,  # "pre_wish", "emerging_wish", "workaround_wish"
                "trigger": str,  # Ce a declanșat detecția
                "evidence": List[str]  # Dovezi din text
            }
        """
        text_lower = text.lower()
        patterns = self.pre_wish_patterns.get(language, self.pre_wish_patterns["en"])
        emerging_patterns = self.emerging_wish_patterns.get(language, self.emerging_wish_patterns["en"])
        
        evidence = []
        wish_type = None
        trigger = None
        
        # 1. Verifică pattern-uri pre-wish
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                evidence.append(match.group(0))
                if "workaround" in pattern or "manual" in pattern or "Excel" in pattern:
                    wish_type = "workaround_wish"
                    trigger = "workaround_detected"
                elif "comparison" in pattern or "între" in pattern or "between" in pattern:
                    wish_type = "comparison_wish"
                    trigger = "comparison_detected"
                else:
                    wish_type = "pre_wish"
                    trigger = "frustration_detected"
                break
        
        # 2. Verifică pattern-uri emerging wish
        if not wish_type:
            for pattern in emerging_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    evidence.append(match.group(0))
                    wish_type = "emerging_wish"
                    trigger = "emerging_pattern_detected"
                    break
        
        if not wish_type or not evidence:
            return None
        
        # 3. Extrage wish-ul dedus
        wish = self._extract_wish_from_context(text, language, wish_type, evidence)
        
        if not wish:
            return None
        
        # 4. Calculează confidence
        confidence = self._calculate_confidence(evidence, wish_type, text)
        
        return {
            "wish": wish,
            "confidence": confidence,
            "type": wish_type,
            "trigger": trigger,
            "evidence": evidence
        }
    
    def _extract_wish_from_context(
        self,
        text: str,
        language: str,
        wish_type: str,
        evidence: List[str]
    ) -> Optional[str]:
        """Extrage wish-ul dedus din context"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            # Fallback: extrage din pattern-uri simple
            return self._extract_wish_simple(text, language, wish_type)
        
        try:
            doc = nlp(text)
            
            # Pentru workaround wish: extrage ce face manual
            if wish_type == "workaround_wish":
                # Caută pattern: "fac X manual pentru Y" → wish pentru "X automat pentru Y"
                for token in doc:
                    if token.lemma_ in ["face", "folosi", "do", "use"]:
                        # Găsește obiectul
                        for child in token.children:
                            if child.dep_ in ["dobj", "pobj"]:
                                obj = child.text
                                # Construiește wish
                                if language == "ro":
                                    return f"automatizare pentru {obj}"
                                else:
                                    return f"automation for {obj}"
            
            # Pentru comparison wish: extrage ce lipsește
            elif wish_type == "comparison_wish":
                # Caută pattern: "X e bun dar lipsește Y" → wish pentru "X cu Y"
                for token in doc:
                    if token.lemma_ in ["lipsește", "missing", "lacks"]:
                        # Găsește ce lipsește
                        for child in token.children:
                            if child.dep_ in ["nsubj", "dobj"]:
                                missing = child.text
                                # Construiește wish
                                if language == "ro":
                                    return f"produs cu {missing}"
                                else:
                                    return f"product with {missing}"
            
            # Pentru pre-wish: extrage ce ar rezolva problema
            else:
                # Caută verbe de acțiune și obiecte
                verbs = [token.lemma_ for token in doc if token.pos_ == "VERB" and token.dep_ == "ROOT"]
                objects = [token.text for token in doc if token.dep_ in ["dobj", "pobj"] and token.pos_ == "NOUN"]
                
                if verbs and objects:
                    if language == "ro":
                        return f"{verbs[0]} {objects[0]}"
                    else:
                        return f"{verbs[0]} {objects[0]}"
        
        except Exception:
            pass
        
        # Fallback
        return self._extract_wish_simple(text, language, wish_type)
    
    def _extract_wish_simple(self, text: str, language: str, wish_type: str) -> Optional[str]:
        """Extrage wish simplu din text (fallback)"""
        # Extrage primele cuvinte importante
        words = text.split()
        important_words = [w for w in words if len(w) > 4 and w.lower() not in ["pentru", "care", "that", "which"]]
        
        if len(important_words) >= 3:
            if language == "ro":
                return " ".join(important_words[:5])
            else:
                return " ".join(important_words[:5])
        
        return None
    
    def _calculate_confidence(self, evidence: List[str], wish_type: str, text: str) -> float:
        """Calculează confidence pentru wish-ul dedus"""
        base_confidence = 0.5
        
        # Mai multe dovezi = mai mare confidence
        if len(evidence) >= 2:
            base_confidence += 0.2
        
        # Tipuri de wish-uri diferite au confidence diferit
        if wish_type == "workaround_wish":
            base_confidence += 0.2  # Workarounds = wish puternic
        elif wish_type == "comparison_wish":
            base_confidence += 0.15  # Comparații = wish moderat
        elif wish_type == "pre_wish":
            base_confidence += 0.1  # Pre-wish = wish moderat
        else:
            base_confidence += 0.05  # Emerging = wish slab
        
        # Text mai lung = mai mult context = mai mare confidence
        if len(text) > 200:
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
