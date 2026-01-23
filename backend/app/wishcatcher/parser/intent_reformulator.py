"""
Intent Reformulator - Construiește intent-uri complete, coerente și explicite
Transformă fragmente de text în mesaje clare pentru MVP și Business Plan
"""

import re
from typing import Dict, List, Optional, Any
import spacy


class IntentReformulator:
    """Reformulează intent-uri fragmentate în mesaje complete și coerente"""
    
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
        
        # Pattern-uri pentru extragere structurată
        self.problem_indicators = {
            "ro": ["problema", "lipsește", "nu există", "nu funcționează", "frustrant", "enervant", "dificil", "complicat"],
            "en": ["problem", "missing", "doesn't exist", "doesn't work", "frustrating", "annoying", "difficult", "complicated"]
        }
        
        self.solution_indicators = {
            "ro": ["ar trebui", "ar fi util", "ar rezolva", "ar ajuta", "necesită", "dorește"],
            "en": ["should", "would be useful", "would solve", "would help", "needs", "wants"]
        }
    
    def reformulate_intent(
        self,
        intent: str,
        language: str = "ro",
        context: Optional[Dict[str, Any]] = None,
        trigger_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reformulează intent-ul într-o structură completă și coerentă
        
        Returns:
            {
                "intent_short": str,  # 1-2 propoziții
                "intent_full": str,    # 3-5 propoziții cu context
                "structured": {
                    "what": str,
                    "why": str,
                    "who": str,
                    "when": str,
                    "how": str,
                    "problem": str,
                    "solution_type": str,
                    "key_features": List[str],
                    "pain_points": List[str]
                }
            }
        """
        # Construiește text complet din toate sursele
        full_text = self._build_full_text(intent, context, trigger_analysis)
        
        # Extrage informații structurate
        structured = self._extract_structured(full_text, language, trigger_analysis)
        
        # Construiește intent_short (1-2 propoziții)
        intent_short = self._build_intent_short(structured, language)
        
        # Construiește intent_full (3-5 propoziții cu context)
        intent_full = self._build_intent_full(structured, trigger_analysis, language)
        
        return {
            "intent_short": intent_short,
            "intent_full": intent_full,
            "structured": structured
        }
    
    def _build_full_text(
        self,
        intent: str,
        context: Optional[Dict[str, Any]],
        trigger_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """Construiește text complet din toate sursele"""
        parts = [intent]
        
        # Adaugă context
        if context:
            if isinstance(context, dict):
                context_text = context.get("post_text", "") or context.get("text", "") or ""
                if context_text and context_text != intent:
                    parts.append(context_text)
        
        # Adaugă trigger text
        if trigger_analysis:
            if isinstance(trigger_analysis, dict):
                trigger = trigger_analysis.get("trigger", {})
                if isinstance(trigger, dict):
                    trigger_text = trigger.get("text", "")
                    if trigger_text:
                        parts.append(trigger_text)
        
        return " ".join(parts)
    
    def _extract_structured(
        self,
        text: str,
        language: str,
        trigger_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extrage informații structurate din text"""
        nlp = self.nlp_models.get(language)
        
        # Extrage "what" - ce vrea utilizatorul
        what = self._extract_what(text, nlp, language)
        
        # Extrage "why" - de ce vrea (problema)
        why = self._extract_why(text, trigger_analysis, language)
        
        # Extrage "who" - pentru cine
        who = self._extract_who(text, nlp, language)
        
        # Extrage "when" - când apare problema
        when = self._extract_when(text, trigger_analysis, language)
        
        # Extrage "how" - cum ar trebui rezolvată
        how = self._extract_how(text, nlp, language)
        
        # Extrage problem-ul explicit
        problem = self._extract_problem(text, trigger_analysis, language)
        
        # Determină tipul soluției
        solution_type = self._determine_solution_type(text, language)
        
        # Extrage features cheie
        key_features = self._extract_key_features(text, nlp, language)
        
        # Extrage pain points
        pain_points = self._extract_pain_points(text, trigger_analysis, language)
        
        return {
            "what": what,
            "why": why,
            "who": who,
            "when": when,
            "how": how,
            "problem": problem,
            "solution_type": solution_type,
            "key_features": key_features,
            "pain_points": pain_points
        }
    
    def _extract_what(self, text: str, nlp, language: str) -> str:
        """Extrage ce vrea utilizatorul"""
        # Caută pattern-uri de dorință
        wish_patterns = {
            "ro": [
                r"(?:vreau|doresc|aș vrea|mi-aș dori|ar fi util|necesită)\s+(?:un|o|o?)\s*([^.!?]+)",
                r"(?:ar trebui|ar fi bine|ar fi minunat)\s+(?:să|ca)\s+([^.!?]+)",
                r"lipsește\s+(?:un|o|o?)\s*([^.!?]+)",
                r"nu există\s+(?:un|o|o?)\s*([^.!?]+)"
            ],
            "en": [
                r"(?:want|need|would like|wish for|looking for)\s+(?:a|an|the)?\s*([^.!?]+)",
                r"(?:should|would be|would be great)\s+(?:to|if)\s+([^.!?]+)",
                r"missing\s+(?:a|an|the)?\s*([^.!?]+)",
                r"doesn't exist\s+(?:a|an|the)?\s*([^.!?]+)"
            ]
        }
        
        patterns = wish_patterns.get(language, wish_patterns["en"])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                what = match.group(1).strip()
                # Curăță și limitează
                what = re.sub(r'\s+', ' ', what)
                if len(what) > 100:
                    what = what[:100] + "..."
                return what
        
        # Fallback: primele cuvinte importante
        if nlp:
            try:
                doc = nlp(text)
                # Extrage subiect + verb + obiect
                important_words = []
                for token in doc:
                    if token.pos_ in ["NOUN", "VERB", "PROPN"] and not token.is_stop:
                        important_words.append(token.text)
                if important_words:
                    return " ".join(important_words[:10])
            except:
                pass
        
        # Ultimul fallback: primele 50 de caractere
        return text[:50].strip()
    
    def _extract_why(self, text: str, trigger_analysis: Optional[Dict], language: str) -> str:
        """Extrage de ce vrea (problema/motivul)"""
        # Caută în trigger_analysis
        if trigger_analysis:
            frustration = trigger_analysis.get("frustration", {})
            if isinstance(frustration, dict):
                expressions = frustration.get("expressions", [])
                if expressions:
                    return ". ".join(expressions[:2])
            
            pain_points = trigger_analysis.get("pain_points", [])
            if pain_points:
                return ". ".join(pain_points[:2])
        
        # Caută pattern-uri de problemă în text
        problem_patterns = {
            "ro": [
                r"(?:pentru că|deoarece|fiindcă|din cauza că)\s+([^.!?]+)",
                r"(?:problema|problemei)\s+(?:este|că|e)\s+([^.!?]+)",
                r"(?:nu funcționează|nu merge|nu e bun)\s+(?:pentru|la)\s+([^.!?]+)"
            ],
            "en": [
                r"(?:because|since|due to|as)\s+([^.!?]+)",
                r"(?:problem|issue)\s+(?:is|that)\s+([^.!?]+)",
                r"(?:doesn't work|doesn't function|isn't good)\s+(?:for|at)\s+([^.!?]+)"
            ]
        }
        
        patterns = problem_patterns.get(language, problem_patterns["en"])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]
        
        return "Necesitate identificată din context"
    
    def _extract_who(self, text: str, nlp, language: str) -> str:
        """Extrage pentru cine (target audience)"""
        # Caută indicii de rol/profesie
        role_keywords = {
            "ro": ["programator", "developer", "designer", "freelancer", "student", "părinte", "antreprenor"],
            "en": ["programmer", "developer", "designer", "freelancer", "student", "parent", "entrepreneur"]
        }
        
        keywords = role_keywords.get(language, role_keywords["en"])
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                return keyword.capitalize()
        
        # Caută în context (dacă există)
        # Fallback: demographic general
        return "general users"
    
    def _extract_when(self, text: str, trigger_analysis: Optional[Dict], language: str) -> str:
        """Extrage când apare problema"""
        if trigger_analysis:
            trigger = trigger_analysis.get("trigger", {})
            if isinstance(trigger, dict):
                trigger_text = trigger.get("text", "")
                if trigger_text:
                    # Extrage primul fragment relevant
                    sentences = trigger_text.split('.')
                    if sentences:
                        return sentences[0].strip()[:100]
        
        # Caută pattern-uri temporale
        time_patterns = {
            "ro": [
                r"(?:când|atunci când|în momentul în care)\s+([^.!?]+)",
                r"(?:în situația|în cazul)\s+([^.!?]+)"
            ],
            "en": [
                r"(?:when|whenever|at the moment|in the case)\s+([^.!?]+)",
                r"(?:in situation|in case)\s+([^.!?]+)"
            ]
        }
        
        patterns = time_patterns.get(language, time_patterns["en"])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]
        
        return "Când apare nevoia"
    
    def _extract_how(self, text: str, nlp, language: str) -> str:
        """Extrage cum ar trebui rezolvată (features/soluție)"""
        # Caută pattern-uri de soluție
        solution_patterns = {
            "ro": [
                r"(?:ar trebui să|ar fi bine să|ar rezolva|ar ajuta)\s+([^.!?]+)",
                r"(?:cu|folosind|prin)\s+([^.!?]+)",
                r"(?:care să|care ar)\s+([^.!?]+)"
            ],
            "en": [
                r"(?:should|would solve|would help|by|using|with)\s+([^.!?]+)",
                r"(?:that|which)\s+(?:would|should|can)\s+([^.!?]+)"
            ]
        }
        
        patterns = solution_patterns.get(language, solution_patterns["en"])
        solutions = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                solution = match.group(1).strip()
                if len(solution) > 10:  # Ignoră soluții prea scurte
                    solutions.append(solution)
        
        if solutions:
            return ". ".join(solutions[:3])
        
        # Fallback: extrage features din noun phrases
        if nlp:
            try:
                doc = nlp(text)
                features = []
                for chunk in doc.noun_chunks:
                    if len(chunk.text) > 5 and chunk.text.lower() not in ["utilizator", "user", "oameni", "people"]:
                        features.append(chunk.text)
                if features:
                    return ", ".join(features[:5])
            except:
                pass
        
        return "Soluție bazată pe nevoile identificate"
    
    def _extract_problem(self, text: str, trigger_analysis: Optional[Dict], language: str) -> str:
        """Extrage problema explicită"""
        # Prioritizează trigger_analysis
        if trigger_analysis:
            pain_points = trigger_analysis.get("pain_points", [])
            if pain_points:
                return ". ".join(pain_points[:2])
            
            frustration = trigger_analysis.get("frustration", {})
            if isinstance(frustration, dict):
                expressions = frustration.get("expressions", [])
                if expressions:
                    return ". ".join(expressions[:2])
        
        # Caută în text
        problem_indicators = self.problem_indicators.get(language, self.problem_indicators["en"])
        text_lower = text.lower()
        
        for indicator in problem_indicators:
            if indicator in text_lower:
                # Extrage propoziția care conține indicatorul
                sentences = text.split('.')
                for sentence in sentences:
                    if indicator in sentence.lower():
                        return sentence.strip()[:150]
        
        return "Problema identificată din context"
    
    def _determine_solution_type(self, text: str, language: str) -> str:
        """Determină tipul soluției"""
        text_lower = text.lower()
        
        # Software indicators
        software_keywords = {
            "ro": ["aplicație", "app", "platformă", "software", "tool", "serviciu", "website", "site"],
            "en": ["app", "application", "platform", "software", "tool", "service", "website", "site"]
        }
        
        # Product indicators
        product_keywords = {
            "ro": ["laptop", "telefon", "produs", "device", "gadget", "echipament"],
            "en": ["laptop", "phone", "product", "device", "gadget", "equipment"]
        }
        
        keywords_sw = software_keywords.get(language, software_keywords["en"])
        keywords_prod = product_keywords.get(language, product_keywords["en"])
        
        if any(kw in text_lower for kw in keywords_sw):
            return "software"
        elif any(kw in text_lower for kw in keywords_prod):
            return "physical_product"
        else:
            return "service"
    
    def _extract_key_features(self, text: str, nlp, language: str) -> List[str]:
        """Extrage features cheie"""
        features = []
        
        # Caută pattern-uri de features
        feature_patterns = {
            "ro": [
                r"(?:cu|care are|care include|care permite)\s+([^.!?,]+)",
                r"(?:funcție|feature|opțiune|opțiunea)\s+(?:de|pentru)\s+([^.!?,]+)"
            ],
            "en": [
                r"(?:with|that has|that includes|that allows)\s+([^.!?,]+)",
                r"(?:feature|function|option)\s+(?:for|of)\s+([^.!?,]+)"
            ]
        }
        
        patterns = feature_patterns.get(language, feature_patterns["en"])
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                feature = match.group(1).strip()
                if len(feature) > 5 and len(feature) < 50:
                    features.append(feature)
        
        # Extrage din noun phrases (dacă NLP e disponibil)
        if nlp and len(features) < 5:
            try:
                doc = nlp(text)
                for chunk in doc.noun_chunks:
                    chunk_text = chunk.text.lower()
                    # Ignoră stop words și cuvinte prea comune
                    if (len(chunk.text) > 5 and 
                        chunk_text not in ["utilizator", "user", "oameni", "people", "ceva", "something"] and
                        chunk.text not in features):
                        features.append(chunk.text)
            except:
                pass
        
        return features[:10]  # Max 10 features
    
    def _extract_pain_points(self, text: str, trigger_analysis: Optional[Dict], language: str) -> List[str]:
        """Extrage pain points"""
        pain_points = []
        
        # Din trigger_analysis
        if trigger_analysis:
            pain_points_list = trigger_analysis.get("pain_points", [])
            if pain_points_list:
                pain_points.extend(pain_points_list)
        
        # Din text (caută pattern-uri negative)
        negative_patterns = {
            "ro": [
                r"(?:nu funcționează|nu merge|nu e bun|nu are|nu permite)\s+([^.!?]+)",
                r"(?:lipsește|nu există|nu se găsește)\s+([^.!?]+)",
                r"(?:frustrant|enervant|complicat|dificil)\s+(?:că|să|să)\s*([^.!?]+)"
            ],
            "en": [
                r"(?:doesn't work|doesn't function|isn't good|doesn't have|doesn't allow)\s+([^.!?]+)",
                r"(?:missing|doesn't exist|can't find)\s+([^.!?]+)",
                r"(?:frustrating|annoying|complicated|difficult)\s+(?:that|to|to)\s*([^.!?]+)"
            ]
        }
        
        patterns = negative_patterns.get(language, negative_patterns["en"])
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pain = match.group(1).strip()
                if len(pain) > 5:
                    pain_points.append(pain)
        
        return list(set(pain_points))[:10]  # Remove duplicates, max 10
    
    def _build_intent_short(self, structured: Dict[str, Any], language: str) -> str:
        """Construiește intent_short (1-2 propoziții)"""
        what = structured.get("what", "")
        solution_type = structured.get("solution_type", "")
        
        if language == "ro":
            if solution_type == "software":
                return f"Platformă/aplicație pentru {what.lower()}"
            elif solution_type == "physical_product":
                return f"Produs: {what}"
            else:
                return f"Serviciu pentru {what.lower()}"
        else:
            if solution_type == "software":
                return f"Platform/application for {what.lower()}"
            elif solution_type == "physical_product":
                return f"Product: {what}"
            else:
                return f"Service for {what.lower()}"
    
    def _build_intent_full(
        self,
        structured: Dict[str, Any],
        trigger_analysis: Optional[Dict],
        language: str
    ) -> str:
        """Construiește intent_full (3-5 propoziții cu context)"""
        parts = []
        
        what = structured.get("what", "")
        why = structured.get("why", "")
        problem = structured.get("problem", "")
        how = structured.get("how", "")
        when = structured.get("when", "")
        
        if language == "ro":
            # Propoziția 1: Ce vrea
            if what:
                parts.append(f"Utilizatorii doresc {what.lower()}.")
            
            # Propoziția 2: De ce (problema)
            if problem and problem != "Problema identificată din context":
                parts.append(f"Problema apare când {problem.lower()}.")
            elif why and why != "Necesitate identificată din context":
                parts.append(f"Motivul este că {why.lower()}.")
            
            # Propoziția 3: Când apare
            if when and when != "Când apare nevoia":
                parts.append(f"Situația apare {when.lower()}.")
            
            # Propoziția 4: Cum ar trebui rezolvată
            if how and how != "Soluție bazată pe nevoile identificate":
                parts.append(f"Soluția ar trebui să includă: {how.lower()}.")
            
            # Propoziția 5: Features (dacă există)
            features = structured.get("key_features", [])
            if features:
                features_str = ", ".join(features[:5])
                parts.append(f"Funcționalități cheie: {features_str}.")
        else:
            # English version
            if what:
                parts.append(f"Users want {what.lower()}.")
            
            if problem and problem != "Problem identified from context":
                parts.append(f"The problem occurs when {problem.lower()}.")
            elif why and why != "Need identified from context":
                parts.append(f"The reason is that {why.lower()}.")
            
            if when and when != "When the need arises":
                parts.append(f"The situation occurs {when.lower()}.")
            
            if how and how != "Solution based on identified needs":
                parts.append(f"The solution should include: {how.lower()}.")
            
            features = structured.get("key_features", [])
            if features:
                features_str = ", ".join(features[:5])
                parts.append(f"Key features: {features_str}.")
        
        # Dacă nu am construit destule, adaugă din structured
        if len(parts) < 3:
            if what:
                parts.append(what)
            if problem:
                parts.append(problem)
        
        return " ".join(parts[:5])  # Max 5 propoziții
