"""
Reality Checker - Validează dacă wish-urile sunt realiste și fezabile
Filtrează nonsensuri, imposibilități fizice și wish-uri inutile
"""

import re
from typing import Dict, List, Optional, Tuple
import spacy


class RealityChecker:
    """Validează realitatea și fezabilitatea wish-urilor"""
    
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
        
        # Pattern-uri pentru imposibilități fizice/științifice
        self.impossible_patterns = {
            "ro": [
                # Călătorii imposibile
                r"călătorie.*soare|soare.*călătorie",
                r"călătorie.*lună.*fără.*echipament",
                r"călătorie.*mart.*fără.*echipament",
                r"călătorie.*stele|stele.*călătorie",
                r"călătorie.*galaxie|galaxie.*călătorie",
                
                # Fizic imposibil
                r"invenție.*timp.*înapoi|timp.*înapoi.*invenție",
                r"mașină.*timp|timp.*mașină",
                r"teleportare.*instantanee",
                r"invenție.*perpetuum.*mobile",
                r"energie.*infinită.*fără.*sursă",
                
                # Biologic imposibil
                r"invenție.*nemurire.*completă",
                r"invenție.*regenerare.*organe.*instant",
                r"invenție.*creștere.*înălțime.*adult",
                
                # Absurd general
                r"invenție.*magie|magie.*invenție",
                r"invenție.*super.*putere|super.*putere.*invenție",
                r"invenție.*telepatie|telepatie.*invenție",
                r"invenție.*telechinezie|telechinezie.*invenție",
                
                # Nonsensuri specifice
                r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*soare",
                r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*stele",
                r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*galaxie",
            ],
            "en": [
                # Impossible travels
                r"travel.*sun|sun.*travel",
                r"travel.*moon.*without.*equipment",
                r"travel.*mars.*without.*equipment",
                r"travel.*stars|stars.*travel",
                r"travel.*galaxy|galaxy.*travel",
                
                # Physically impossible
                r"invention.*time.*travel|time.*travel.*invention",
                r"time.*machine",
                r"instant.*teleportation",
                r"invention.*perpetual.*motion",
                r"infinite.*energy.*without.*source",
                
                # Biologically impossible
                r"invention.*immortality.*complete",
                r"invention.*organ.*regeneration.*instant",
                r"invention.*grow.*height.*adult",
                
                # General absurd
                r"invention.*magic|magic.*invention",
                r"invention.*super.*power|super.*power.*invention",
                r"invention.*telepathy|telepathy.*invention",
                r"invention.*telekinesis|telekinesis.*invention",
            ]
        }
        
        # Cuvinte cheie care indică nonsens/imposibilitate
        self.nonsense_keywords = {
            "ro": [
                "soare", "stele", "galaxie", "univers", "nebunie", "absurd",
                "imposibil", "magie", "super putere", "telepatie", "telechinezie",
                "nemurire", "timp înapoi", "perpetuum mobile", "energie infinită"
            ],
            "en": [
                "sun", "stars", "galaxy", "universe", "crazy", "absurd",
                "impossible", "magic", "super power", "telepathy", "telekinesis",
                "immortality", "time travel", "perpetual motion", "infinite energy"
            ]
        }
        
        # Pattern-uri pentru wish-uri prea vagi/inutile
        self.vague_patterns = {
            "ro": [
                r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*ceva",
                r"bine.*ar.*fi.*dacă.*ar.*exista.*ceva",
                r"vreau.*ceva.*mai.*bun",
                r"vreau.*ceva.*nou",
                r"ar.*fi.*bine.*ceva",
            ],
            "en": [
                r"wish.*something.*better",
                r"wish.*something.*new",
                r"want.*something.*good",
                r"would.*be.*nice.*something",
            ]
        }
        
        # Pattern-uri pentru wish-uri care sunt deja rezolvate/standard
        self.already_solved_patterns = {
            "ro": [
                r"invenție.*telefon",  # Telefonul există deja
                r"invenție.*internet",  # Internetul există
                r"invenție.*calculator",  # Calculatoarele există
                r"invenție.*mașină",  # Mașinile există
            ],
            "en": [
                r"invention.*phone",
                r"invention.*internet",
                r"invention.*computer",
                r"invention.*car",
            ]
        }
    
    def validate_wish(
        self,
        intent: str,
        language: str = "ro",
        context: Optional[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Validează dacă un wish e realist și fezabil
        
        Returns:
            (is_valid, reason, confidence)
            - is_valid: True dacă wish-ul e valid
            - reason: Motivul pentru care e invalid (dacă e cazul)
            - confidence: Nivel de încredere în validare (0-1)
        """
        intent_lower = intent.lower()
        
        # 1. Verifică imposibilități fizice/științifice
        impossible_score = self._check_impossible(intent_lower, language)
        if impossible_score > 0.7:
            return False, "Wish imposibil fizic/științific", impossible_score
        
        # 2. Verifică nonsensuri
        nonsense_score = self._check_nonsense(intent_lower, language)
        if nonsense_score > 0.7:
            return False, "Wish nonsens/absurd", nonsense_score
        
        # 3. Verifică vagitate
        vague_score = self._check_vague(intent_lower, language)
        if vague_score > 0.8:
            return False, "Wish prea vag/inutil", vague_score
        
        # 4. Verifică dacă e deja rezolvat
        already_solved_score = self._check_already_solved(intent_lower, language)
        if already_solved_score > 0.7:
            return False, "Wish deja rezolvat/existent", already_solved_score
        
        # 5. Verifică fezabilitate tehnică (folosind NLP)
        feasibility_score = self._check_feasibility(intent, language)
        if feasibility_score < 0.3:
            return False, "Wish cu fezabilitate tehnică foarte scăzută", 1.0 - feasibility_score
        
        # 6. Verifică coerență semantică
        coherence_score = self._check_coherence(intent, language)
        if coherence_score < 0.4:
            return False, "Wish incoerent semantic", 1.0 - coherence_score
        
        # Wish valid
        overall_confidence = (feasibility_score + coherence_score) / 2
        return True, "Wish valid și realist", overall_confidence
    
    def _check_impossible(self, intent_lower: str, language: str) -> float:
        """Verifică dacă wish-ul implică imposibilități fizice"""
        patterns = self.impossible_patterns.get(language, self.impossible_patterns["en"])
        
        matches = 0
        for pattern in patterns:
            if re.search(pattern, intent_lower, re.IGNORECASE):
                matches += 1
        
        # Score bazat pe numărul de pattern-uri găsite
        if matches >= 2:
            return 1.0  # Foarte probabil imposibil
        elif matches == 1:
            return 0.7  # Probabil imposibil
        else:
            return 0.0  # Nu pare imposibil
    
    def _check_nonsense(self, intent_lower: str, language: str) -> float:
        """Verifică dacă wish-ul e nonsens/absurd"""
        keywords = self.nonsense_keywords.get(language, self.nonsense_keywords["en"])
        
        matches = sum(1 for keyword in keywords if keyword in intent_lower)
        
        # Score bazat pe numărul de keywords absurde
        if matches >= 3:
            return 1.0  # Foarte probabil nonsens
        elif matches == 2:
            return 0.7  # Probabil nonsens
        elif matches == 1:
            return 0.4  # Posibil nonsens (verifică context)
        else:
            return 0.0  # Nu pare nonsens
    
    def _check_vague(self, intent_lower: str, language: str) -> float:
        """Verifică dacă wish-ul e prea vag/inutil"""
        patterns = self.vague_patterns.get(language, self.vague_patterns["en"])
        
        for pattern in patterns:
            if re.search(pattern, intent_lower, re.IGNORECASE):
                return 0.9  # Foarte vag
        
        # Verifică dacă intent-ul e prea scurt sau generic
        if len(intent_lower.split()) < 4:
            return 0.6  # Posibil vag (prea scurt)
        
        return 0.0  # Nu pare vag
    
    def _check_already_solved(self, intent_lower: str, language: str) -> float:
        """Verifică dacă wish-ul e deja rezolvat/existent"""
        patterns = self.already_solved_patterns.get(language, self.already_solved_patterns["en"])
        
        for pattern in patterns:
            if re.search(pattern, intent_lower, re.IGNORECASE):
                return 0.8  # Probabil deja există
        
        return 0.0  # Nu pare deja rezolvat
    
    def _check_feasibility(self, intent: str, language: str) -> float:
        """Verifică fezabilitatea tehnică folosind NLP"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return 0.5  # Default dacă nu avem NLP model
        
        try:
            doc = nlp(intent)
            
            # Extrage entități și le analizează
            entities = [ent.text.lower() for ent in doc.ents]
            
            # Verifică dacă conține entități imposibile
            impossible_entities = ["soare", "sun", "stele", "stars", "galaxie", "galaxy"]
            if any(imp in " ".join(entities) for imp in impossible_entities):
                return 0.1  # Foarte scăzută fezabilitate
            
            # Verifică coerența sintactică
            # Dacă are subiect + verb + obiect = mai coerent
            has_subject = any(token.dep_ == "nsubj" for token in doc)
            has_verb = any(token.pos_ == "VERB" for token in doc)
            has_object = any(token.dep_ in ["obj", "dobj"] for token in doc)
            
            if has_subject and has_verb and has_object:
                return 0.8  # Fezabil (structură coerentă)
            elif has_subject and has_verb:
                return 0.6  # Moderat fezabil
            else:
                return 0.4  # Scăzută fezabilitate (structură incompletă)
        
        except Exception:
            return 0.5  # Default în caz de eroare
    
    def _check_coherence(self, intent: str, language: str) -> float:
        """Verifică coerența semantică"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return 0.5  # Default
        
        try:
            doc = nlp(intent)
            
            # Verifică dacă are sens semantic
            # Dacă are multe cuvinte importante (NOUN, VERB, ADJ) = mai coerent
            important_words = [token for token in doc 
                             if token.pos_ in ["NOUN", "VERB", "ADJ"] 
                             and not token.is_stop]
            
            if len(important_words) >= 5:
                return 0.8  # Coerent (multe cuvinte importante)
            elif len(important_words) >= 3:
                return 0.6  # Moderat coerent
            else:
                return 0.3  # Incoerent (prea puține cuvinte importante)
        
        except Exception:
            return 0.5  # Default
    
    def get_validation_details(self, intent: str, language: str = "ro") -> Dict:
        """
        Returnează detalii despre validare pentru debugging
        """
        intent_lower = intent.lower()
        
        return {
            "impossible_score": self._check_impossible(intent_lower, language),
            "nonsense_score": self._check_nonsense(intent_lower, language),
            "vague_score": self._check_vague(intent_lower, language),
            "already_solved_score": self._check_already_solved(intent_lower, language),
            "feasibility_score": self._check_feasibility(intent, language),
            "coherence_score": self._check_coherence(intent, language),
            "is_valid": self.validate_wish(intent, language)[0]
        }
