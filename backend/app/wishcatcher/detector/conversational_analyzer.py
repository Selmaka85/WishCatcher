"""
Conversational Analyzer - Analizează thread-uri complete pentru wish-uri
Wish-urile apar adesea în conversații, nu în postări individuale
"""

from typing import Dict, List, Optional
from collections import Counter


class ConversationalAnalyzer:
    """Analizează conversații complete pentru wish-uri"""
    
    def analyze_conversation(
        self,
        post_text: str,
        comments: List[Dict],
        language: str = "ro"
    ) -> Optional[Dict]:
        """
        Analizează conversația completă pentru wish-uri
        
        Args:
            post_text: Textul postării inițiale
            comments: Lista de comentarii
            language: Limba conversației
        
        Returns:
            {
                "wish": str,
                "confidence": float,
                "consensus": float,  # Cât de mulți oameni acord
                "evidence": List[str],
                "source": str  # "post", "comment", "consensus"
            }
        """
        # 1. Analizează post-ul inițial
        post_wish = self._extract_wish_from_text(post_text, language)
        
        # 2. Analizează comentariile
        comment_wishes = []
        for comment in comments:
            comment_text = comment.get("text", "")
            if comment_text:
                wish = self._extract_wish_from_text(comment_text, language)
                if wish:
                    comment_wishes.append(wish)
        
        # 3. Detectează consensus (wish-uri similare în multiple comentarii)
        consensus_wish = self._detect_consensus(comment_wishes)
        
        # 4. Alege wish-ul cel mai bun
        if consensus_wish:
            return {
                "wish": consensus_wish["wish"],
                "confidence": min(consensus_wish["confidence"] + 0.2, 1.0),  # Bonus pentru consensus
                "consensus": consensus_wish["consensus"],
                "evidence": consensus_wish["evidence"],
                "source": "consensus"
            }
        elif post_wish:
            return {
                "wish": post_wish,
                "confidence": 0.7,
                "consensus": 0.0,
                "evidence": [post_text[:100]],
                "source": "post"
            }
        elif comment_wishes:
            # Wish din primul comentariu relevant
            return {
                "wish": comment_wishes[0],
                "confidence": 0.65,
                "consensus": len(comment_wishes) / max(len(comments), 1),
                "evidence": [comment_wishes[0]],
                "source": "comment"
            }
        
        return None
    
    def _extract_wish_from_text(self, text: str, language: str) -> Optional[str]:
        """Extrage wish simplu din text"""
        # Pattern-uri de wish
        wish_patterns = {
            "ro": [
                r"(?:vreau|doresc|mi-aș dori|ar fi util).*?([^.!?]+)",
                r"(?:ar trebui|ar fi bine).*?să.*?existe.*?([^.!?]+)",
                r"(?:lipsește|nu există).*?([^.!?]+)",
            ],
            "en": [
                r"(?:want|wish|would like).*?([^.!?]+)",
                r"(?:should|would be).*?if.*?existed.*?([^.!?]+)",
                r"(?:missing|doesn't exist).*?([^.!?]+)",
            ]
        }
        
        import re
        patterns = wish_patterns.get(language, wish_patterns["en"])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                wish = match.group(1).strip()
                if len(wish) > 10:  # Minim 10 caractere
                    return wish[:100]  # Limitează la 100 caractere
        
        return None
    
    def _detect_consensus(self, wishes: List[str]) -> Optional[Dict]:
        """Detectează consensus (wish-uri similare în multiple comentarii)"""
        if len(wishes) < 2:
            return None
        
        # Contorizează wish-uri similare
        wish_counts = Counter(wishes)
        
        # Găsește wish-ul cel mai comun
        most_common = wish_counts.most_common(1)
        if most_common:
            wish, count = most_common[0]
            if count >= 2:  # Cel puțin 2 oameni acord
                consensus = count / len(wishes)
                return {
                    "wish": wish,
                    "confidence": 0.8,
                    "consensus": consensus,
                    "evidence": [w for w in wishes if w == wish]
                }
        
        return None
