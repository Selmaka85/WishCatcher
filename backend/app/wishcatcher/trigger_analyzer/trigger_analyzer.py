"""
Trigger Analyzer - Analizează trigger-ul/cauza/frustrarea care a declansat dorința
"""

import spacy
import re
from typing import Dict, List, Optional


class TriggerAnalyzer:
    """Analizează trigger-ul/cauza/frustrarea care a declansat dorința"""
    
    def __init__(self):
        try:
            self.nlp_ro = spacy.load("ro_core_news_sm")
            self.nlp_en = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp_ro = None
            self.nlp_en = None
        
        # Patterns pentru trigger events
        self.trigger_patterns = {
            "ro": {
                "event": [
                    r"(?:am avut|am pățit|s-a întâmplat|am realizat).*?că",
                    r"(?:după ce|odată ce|când).*?am",
                    r"(?:recent|azi|săptămâna trecută).*?am"
                ],
                "frustration": [
                    r"(?:e frustrant|mă enervează|e enervant).*?că",
                    r"(?:nu pot|nu reușesc|e imposibil).*?să",
                    r"(?:e greu|e dificil|e complicat).*?să"
                ],
                "pain_point": [
                    r"(?:pierd|consum|irosesc).*?timp",
                    r"(?:costă|plătesc|cheltui).*?prea mult",
                    r"(?:risc|pericol|problema).*?că"
                ]
            },
            "en": {
                "event": [
                    r"(?:i had|i experienced|it happened|i realized).*?that",
                    r"(?:after|once|when).*?i",
                    r"(?:recently|today|last week).*?i"
                ],
                "frustration": [
                    r"(?:frustrating|annoying|irritating).*?that",
                    r"(?:can't|cannot|unable).*?to",
                    r"(?:hard|difficult|complicated).*?to"
                ],
                "pain_point": [
                    r"(?:waste|lose|spend).*?time",
                    r"(?:cost|pay|spend).*?too much",
                    r"(?:risk|danger|problem).*?that"
                ]
            }
        }
    
    def analyze(self, text: str, full_context: Optional[Dict] = None) -> Dict:
        """
        Analizează textul pentru trigger/cauză/frustrare
        
        Returns:
            {
                "trigger": {...},
                "frustration": {...},
                "pain_points": [...],
                "context": {...},
                "emotional_intensity": float
            }
        """
        # Detect language
        language = self._detect_language(text)
        
        # Analyze text
        doc = self._get_nlp_doc(text, language)
        
        # Analyze context if available
        if full_context:
            context_text = full_context.get("post_text", text)
            if full_context.get("comments"):
                context_text += " " + " ".join(
                    c.get("text", "") for c in full_context["comments"][:5]
                )
        else:
            context_text = text
        
        return {
            "trigger": self._detect_trigger(text, context_text, language),
            "frustration": self._extract_frustration(text, context_text, language),
            "pain_points": self._identify_pain_points(text, context_text, language),
            "context": self._analyze_context(text, language),
            "emotional_intensity": self._measure_emotional_intensity(text, language)
        }
    
    def _detect_language(self, text: str) -> str:
        """Detectează limba"""
        romanian_keywords = ["mi-aș", "ar fi", "ce bine", "vreau", "am nevoie", "e frustrant"]
        if any(kw in text.lower() for kw in romanian_keywords):
            return "ro"
        return "en"
    
    def _get_nlp_doc(self, text: str, language: str):
        """Obține spaCy doc"""
        if language == "ro" and self.nlp_ro:
            return self.nlp_ro(text)
        elif language == "en" and self.nlp_en:
            return self.nlp_en(text)
        return None
    
    def _detect_trigger(self, text: str, context: str, language: str) -> Dict:
        """Detectează evenimentul declanșator"""
        patterns = self.trigger_patterns.get(language, self.trigger_patterns["en"])
        event_patterns = patterns.get("event", [])
        
        trigger_text = None
        trigger_type = None
        
        for pattern in event_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                start = match.end()
                end = min(start + 200, len(context))
                trigger_text = context[start:end].strip()
                trigger_type = "event"
                break
            if trigger_text:
                break
        
        return {
            "type": trigger_type,
            "text": trigger_text,
            "confidence": 0.8 if trigger_text else 0.3
        }
    
    def _extract_frustration(self, text: str, context: str, language: str) -> Dict:
        """Extrage frustrarea exprimată"""
        patterns = self.trigger_patterns.get(language, self.trigger_patterns["en"])
        frustration_patterns = patterns.get("frustration", [])
        
        frustrations = []
        for pattern in frustration_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                start = match.start()
                end = min(match.end() + 100, len(context))
                frustration_text = context[start:end].strip()
                frustrations.append(frustration_text)
        
        sentiment_score = self._analyze_sentiment(text, language)
        
        return {
            "expressions": frustrations,
            "sentiment": sentiment_score,
            "intensity": abs(sentiment_score) if sentiment_score < 0 else 0
        }
    
    def _identify_pain_points(self, text: str, context: str, language: str) -> List[Dict]:
        """Identifică pain points concrete"""
        patterns = self.trigger_patterns.get(language, self.trigger_patterns["en"])
        pain_patterns = patterns.get("pain_point", [])
        
        pain_points = []
        for pattern in pain_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                start = match.start()
                end = min(match.end() + 100, len(context))
                pain_text = context[start:end].strip()
                
                pain_type = self._categorize_pain_point(pain_text, language)
                severity = self._estimate_severity(pain_text, language)
                
                pain_points.append({
                    "text": pain_text,
                    "type": pain_type,
                    "severity": severity
                })
        
        return pain_points
    
    def _analyze_context(self, text: str, language: str) -> Dict:
        """Analizează contextul"""
        context_info = {
            "role": None,
            "situation": None,
            "constraints": []
        }
        
        # Extract role/profession
        role_keywords = {
            "ro": ["student", "părinte", "angajat", "antreprenor"],
            "en": ["student", "parent", "employee", "entrepreneur"]
        }
        
        keywords = role_keywords.get(language, role_keywords["en"])
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                context_info["role"] = keyword
                break
        
        return context_info
    
    def _measure_emotional_intensity(self, text: str, language: str) -> float:
        """Măsoară intensitatea emoțională (0-1)"""
        emotional_words = {
            "ro": {
                "frustrant": -0.8,
                "enervant": -0.7,
                "urgent": 0.9,
                "necesar": 0.7,
                "important": 0.6
            },
            "en": {
                "frustrating": -0.8,
                "annoying": -0.7,
                "urgent": 0.9,
                "necessary": 0.7,
                "important": 0.6
            }
        }
        
        words = emotional_words.get(language, emotional_words["en"])
        intensity = 0.0
        count = 0
        
        text_lower = text.lower()
        for word, score in words.items():
            if word in text_lower:
                intensity += abs(score)
                count += 1
        
        return intensity / max(count, 1)
    
    def _analyze_sentiment(self, text: str, language: str) -> float:
        """Analizează sentiment (simplificat)"""
        negative_words = {
            "ro": ["frustrant", "enervant", "greu", "dificil", "problema"],
            "en": ["frustrating", "annoying", "hard", "difficult", "problem"]
        }
        
        positive_words = {
            "ro": ["bine", "util", "ajutor", "soluție"],
            "en": ["good", "useful", "help", "solution"]
        }
        
        neg_words = negative_words.get(language, negative_words["en"])
        pos_words = positive_words.get(language, positive_words["en"])
        
        sentiment = 0.0
        text_lower = text.lower()
        
        for word in neg_words:
            if word in text_lower:
                sentiment -= 0.2
        
        for word in pos_words:
            if word in text_lower:
                sentiment += 0.2
        
        return sentiment
    
    def _categorize_pain_point(self, text: str, language: str) -> str:
        """Categorizează pain point"""
        text_lower = text.lower()
        
        if "timp" in text_lower or "time" in text_lower:
            return "time"
        elif "cost" in text_lower or "bani" in text_lower or "money" in text_lower:
            return "cost"
        elif "risc" in text_lower or "risk" in text_lower or "pericol" in text_lower:
            return "risk"
        else:
            return "effort"
    
    def _estimate_severity(self, text: str, language: str) -> str:
        """Estimează severitatea pain point"""
        high_severity_words = {
            "ro": ["urgent", "critic", "imposibil", "mare"],
            "en": ["urgent", "critical", "impossible", "major"]
        }
        
        medium_severity_words = {
            "ro": ["greu", "dificil", "problema"],
            "en": ["hard", "difficult", "problem"]
        }
        
        high_words = high_severity_words.get(language, high_severity_words["en"])
        medium_words = medium_severity_words.get(language, medium_severity_words["en"])
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in high_words):
            return "high"
        elif any(word in text_lower for word in medium_words):
            return "medium"
        else:
            return "low"
