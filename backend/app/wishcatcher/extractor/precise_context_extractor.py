"""
Precise Context Extractor - Extrage context precis ca ChatGPT/Google
Identifică exact ce produse, servicii sau softuri se caută cu adevărat
Filtrează garbage-ul și false positives
"""

import re
import spacy
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter


class PreciseContextExtractor:
    """
    Extrage context precis și identifică specific produse/servicii/softuri
    Similar cu ChatGPT/Google - doar informații relevante și precise
    """
    
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
        
        # Categorii specifice de produse/servicii/softuri
        self.product_categories = {
            "ro": {
                "software": ["aplicație", "app", "software", "platformă", "sistem", "tool", "program", "serviciu online"],
                "hardware": ["laptop", "telefon", "tabletă", "monitor", "tastatură", "mouse", "webcam", "microfon", "boxe", "cască"],
                "service": ["serviciu", "consultanță", "coaching", "curs", "training", "suport", "asistență"],
                "physical": ["produs", "echipament", "device", "gadget", "accesoriu", "componentă"]
            },
            "en": {
                "software": ["application", "app", "software", "platform", "system", "tool", "program", "online service"],
                "hardware": ["laptop", "phone", "tablet", "monitor", "keyboard", "mouse", "webcam", "microphone", "speakers", "headphones"],
                "service": ["service", "consulting", "coaching", "course", "training", "support", "assistance"],
                "physical": ["product", "equipment", "device", "gadget", "accessory", "component"]
            }
        }
        
        # Keywords care indică wish real (nu garbage)
        self.real_wish_indicators = {
            "ro": [
                # Specificitate
                "pentru", "care să", "care poate", "care permite", "care ajută",
                # Urgență/nevoie
                "am nevoie", "trebuie", "necesită", "lipsește", "nu există",
                # Comparație/alternativă
                "mai bun", "alternativă", "în loc de", "decât",
                # Funcționalitate specifică
                "să facă", "să rezolve", "să automatizeze", "să gestioneze", "să calculeze"
            ],
            "en": [
                # Specificity
                "for", "that can", "that allows", "that helps",
                # Urgency/need
                "need", "require", "missing", "doesn't exist",
                # Comparison/alternative
                "better", "alternative", "instead of", "than",
                # Specific functionality
                "to do", "to solve", "to automate", "to manage", "to calculate"
            ]
        }
        
        # Keywords care indică garbage (nu wish real)
        self.garbage_indicators = {
            "ro": [
                # Prea vag
                "ceva", "o chestie", "un lucru", "vreo ceva", "ceva nou", "ceva mai bun",
                # Nonsens
                "magie", "super putere", "telepatie", "telechinezie",
                # Imposibil
                "soare", "stele", "galaxie", "timp înapoi", "nemurire",
                # Deja există
                "telefon", "internet", "calculator", "mașină"  # (dacă e "invenție telefon" = garbage)
            ],
            "en": [
                # Too vague
                "something", "a thing", "some stuff", "something new", "something better",
                # Nonsense
                "magic", "super power", "telepathy", "telekinesis",
                # Impossible
                "sun", "stars", "galaxy", "time travel", "immortality",
                # Already exists
                "phone", "internet", "computer", "car"  # (if "invention phone" = garbage)
            ]
        }
        
        # Pattern-uri pentru extragere precisă
        self.precise_patterns = {
            "ro": [
                # Produs specific
                r"(?:vreau|doresc|am nevoie|trebuie|necesită).*?(?:un|o|unul|una).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Nume propriu
                r"(?:vreau|doresc|am nevoie).*?(?:aplicație|app|software|platformă|sistem).*?(?:pentru|care să|care poate).*?([^.!?]+)",
                r"(?:lipsește|nu există).*?(?:aplicație|app|software|produs|serviciu).*?(?:pentru|care să).*?([^.!?]+)",
                # Funcționalitate specifică
                r"(?:ar trebui|ar fi util).*?(?:să existe|să fie).*?(?:aplicație|app|software|produs|serviciu).*?(?:care să|care poate|care permite).*?([^.!?]+)",
                # Comparație specifică
                r"(?:alternativă|mai bun).*?(?:la|decât|pentru).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ],
            "en": [
                # Specific product
                r"(?:want|need|require|looking for).*?(?:a|an|the).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Proper noun
                r"(?:want|need|looking for).*?(?:app|application|software|platform|system).*?(?:for|that can|that allows).*?([^.!?]+)",
                r"(?:missing|doesn't exist).*?(?:app|application|software|product|service).*?(?:for|that can).*?([^.!?]+)",
                # Specific functionality
                r"(?:should|would be useful).*?(?:to exist|to be).*?(?:app|application|software|product|service).*?(?:that can|that allows|that helps).*?([^.!?]+)",
                # Specific comparison
                r"(?:alternative|better).*?(?:to|than|for).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]
        }
    
    def extract_precise_context(
        self,
        text: str,
        language: str = "ro",
        context: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extrage context precis - doar informații relevante și specifice
        Similar cu ChatGPT/Google - filtrează garbage-ul
        
        Returns:
            {
                "is_valid": bool,  # Dacă e wish real (nu garbage)
                "entity_type": str,  # "product", "service", "software", "unknown"
                "entity_name": str,  # Numele specific al entității
                "category": str,  # Categoria (ex: "software", "hardware", "service")
                "functionality": str,  # Funcționalitatea specifică
                "specificity_score": float,  # Cât de specific e (0-1)
                "relevance_score": float,  # Cât de relevant e (0-1)
                "extracted_context": Dict,  # Context extras precis
                "rejection_reason": Optional[str]  # De ce a fost respins (dacă e cazul)
            }
        """
        # 1. Verifică dacă e garbage (early rejection)
        is_garbage, garbage_reason = self._is_garbage(text, language)
        if is_garbage:
            return {
                "is_valid": False,
                "entity_type": "unknown",
                "entity_name": "",
                "category": "",
                "functionality": "",
                "specificity_score": 0.0,
                "relevance_score": 0.0,
                "extracted_context": {},
                "rejection_reason": garbage_reason
            }
        
        # 2. Extrage entități specifice
        entities = self._extract_specific_entities(text, language)
        
        # 3. Determină tipul entității (product/service/software)
        entity_type, category = self._determine_entity_type(text, entities, language)
        
        # 4. Extrage funcționalitatea specifică
        functionality = self._extract_functionality(text, language)
        
        # 5. Calculează specificitatea
        specificity_score = self._calculate_specificity(text, entities, functionality, language)
        
        # 6. Calculează relevanța
        relevance_score = self._calculate_relevance(text, entity_type, functionality, language)
        
        # 7. Validează final (trebuie să fie suficient de specific și relevant)
        is_valid = specificity_score >= 0.6 and relevance_score >= 0.6
        
        # 8. Construiește context precis
        extracted_context = {
            "entities": entities,
            "entity_type": entity_type,
            "category": category,
            "functionality": functionality,
            "keywords": self._extract_keywords(text, language),
            "intent_indicators": self._extract_intent_indicators(text, language)
        }
        
        return {
            "is_valid": is_valid,
            "entity_type": entity_type,
            "entity_name": entities.get("primary", "") if entities else "",
            "category": category,
            "functionality": functionality,
            "specificity_score": specificity_score,
            "relevance_score": relevance_score,
            "extracted_context": extracted_context,
            "rejection_reason": None if is_valid else f"Specificity: {specificity_score:.2f}, Relevance: {relevance_score:.2f}"
        }
    
    def _is_garbage(self, text: str, language: str) -> Tuple[bool, str]:
        """Verifică dacă textul e garbage (nu wish real)"""
        text_lower = text.lower()
        
        # Verifică keywords de garbage
        garbage_keywords = self.garbage_indicators.get(language, self.garbage_indicators["en"])
        garbage_count = sum(1 for keyword in garbage_keywords if keyword in text_lower)
        
        if garbage_count >= 2:
            return True, f"Too many garbage keywords ({garbage_count})"
        
        # Verifică dacă e prea vag
        vague_patterns = [
            r"ceva.*nou", r"ceva.*mai.*bun", r"o.*chestie", r"un.*lucru",
            r"something.*new", r"something.*better", r"a.*thing", r"some.*stuff"
        ]
        for pattern in vague_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, "Too vague (contains 'something'/'ceva' without specifics)"
        
        # Verifică dacă nu are specificitate
        real_wish_keywords = self.real_wish_indicators.get(language, self.real_wish_indicators["en"])
        real_wish_count = sum(1 for keyword in real_wish_keywords if keyword in text_lower)
        
        if real_wish_count == 0 and len(text.split()) < 8:
            return True, "No specificity indicators and too short"
        
        return False, ""
    
    def _extract_specific_entities(self, text: str, language: str) -> Dict[str, str]:
        """Extrage entități specifice (produse, servicii, softuri)"""
        entities = {}
        nlp = self.nlp_models.get(language)
        
        if nlp:
            try:
                doc = nlp(text)
                
                # Extrage entități NER
                for ent in doc.ents:
                    if ent.label_ in ["PRODUCT", "ORG", "MISC", "PERSON"]:
                        if not entities.get("primary"):
                            entities["primary"] = ent.text
                        entities[ent.label_.lower()] = ent.text
                
                # Extrage noun phrases care ar putea fi entități
                for chunk in doc.noun_chunks:
                    # Filtrează stop words și cuvinte generice
                    if len(chunk.text) > 3 and chunk.text.lower() not in ["ce", "ceva", "what", "something", "un", "o", "a", "an"]:
                        if not entities.get("primary"):
                            entities["primary"] = chunk.text
                        if "nouns" not in entities:
                            entities["nouns"] = []
                        entities["nouns"].append(chunk.text)
            except Exception:
                pass
        
        # Fallback: pattern matching
        if not entities:
            patterns = self.precise_patterns.get(language, self.precise_patterns["en"])
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entity = match.group(1).strip()
                    if len(entity) > 3:
                        entities["primary"] = entity
                        break
        
        return entities
    
    def _determine_entity_type(self, text: str, entities: Dict, language: str) -> Tuple[str, str]:
        """Determină tipul entității (product/service/software)"""
        text_lower = text.lower()
        categories = self.product_categories.get(language, self.product_categories["en"])
        
        # Verifică software
        for keyword in categories["software"]:
            if keyword in text_lower:
                return "software", "software"
        
        # Verifică hardware
        for keyword in categories["hardware"]:
            if keyword in text_lower:
                return "product", "hardware"
        
        # Verifică service
        for keyword in categories["service"]:
            if keyword in text_lower:
                return "service", "service"
        
        # Verifică physical product
        for keyword in categories["physical"]:
            if keyword in text_lower:
                return "product", "physical"
        
        # Default
        return "unknown", "other"
    
    def _extract_functionality(self, text: str, language: str) -> str:
        """Extrage funcționalitatea specifică"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return ""
        
        try:
            doc = nlp(text)
            
            # Caută verbe de acțiune cu obiecte
            functionality_parts = []
            for token in doc:
                if token.pos_ == "VERB" and token.dep_ == "ROOT":
                    # Găsește obiectul
                    obj = None
                    for child in token.children:
                        if child.dep_ in ["dobj", "pobj"]:
                            obj = child.text
                            break
                    
                    if obj:
                        functionality_parts.append(f"{token.lemma_} {obj}")
            
            if functionality_parts:
                return " ".join(functionality_parts[:3])  # Max 3 funcționalități
        
        except Exception:
            pass
        
        return ""
    
    def _calculate_specificity(self, text: str, entities: Dict, functionality: str, language: str) -> float:
        """Calculează cât de specific e wish-ul (0-1)"""
        score = 0.0
        
        # 1. Are entități specifice? (0.3)
        if entities.get("primary"):
            score += 0.3
            # Bonus dacă e nume propriu sau termen tehnic
            if entities["primary"][0].isupper() or len(entities["primary"].split()) > 1:
                score += 0.1
        
        # 2. Are funcționalitate specifică? (0.3)
        if functionality:
            score += 0.3
            # Bonus dacă are multiple funcționalități
            if len(functionality.split()) > 3:
                score += 0.1
        
        # 3. Are keywords de specificitate? (0.2)
        real_wish_keywords = self.real_wish_indicators.get(language, self.real_wish_indicators["en"])
        keyword_count = sum(1 for keyword in real_wish_keywords if keyword in text.lower())
        if keyword_count >= 2:
            score += 0.2
        elif keyword_count == 1:
            score += 0.1
        
        # 4. Nu e vag? (0.1)
        vague_patterns = ["ceva", "something", "o chestie", "a thing"]
        if not any(vp in text.lower() for vp in vague_patterns):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_relevance(self, text: str, entity_type: str, functionality: str, language: str) -> float:
        """Calculează cât de relevant e wish-ul (0-1)"""
        score = 0.0
        
        # 1. Are tip de entitate identificat? (0.3)
        if entity_type != "unknown":
            score += 0.3
        
        # 2. Are funcționalitate? (0.3)
        if functionality:
            score += 0.3
        
        # 3. Are indicatoare de nevoie/urgență? (0.2)
        need_indicators = {
            "ro": ["nevoie", "trebuie", "necesită", "lipsește", "nu există"],
            "en": ["need", "require", "missing", "doesn't exist"]
        }
        indicators = need_indicators.get(language, need_indicators["en"])
        if any(ind in text.lower() for ind in indicators):
            score += 0.2
        
        # 4. Are context suficient? (0.2)
        if len(text.split()) >= 10:
            score += 0.2
        elif len(text.split()) >= 6:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_keywords(self, text: str, language: str) -> List[str]:
        """Extrage keywords relevante"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return []
        
        try:
            doc = nlp(text)
            keywords = []
            
            # Extrage NOUN, VERB, ADJ (fără stop words)
            for token in doc:
                if token.pos_ in ["NOUN", "VERB", "ADJ"] and not token.is_stop:
                    if len(token.lemma_) > 3:
                        keywords.append(token.lemma_)
            
            return keywords[:10]  # Max 10 keywords
        
        except Exception:
            return []
    
    def _extract_intent_indicators(self, text: str, language: str) -> List[str]:
        """Extrage indicatoare de intent"""
        indicators = []
        real_wish_keywords = self.real_wish_indicators.get(language, self.real_wish_indicators["en"])
        
        for keyword in real_wish_keywords:
            if keyword in text.lower():
                indicators.append(keyword)
        
        return indicators
