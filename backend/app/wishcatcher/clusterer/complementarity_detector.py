"""
Complementarity Detector - Detectează dorințe complementare (N flexibil)
Rule-based cu validare semantică (spaCy embeddings)
"""

import spacy
from typing import Dict, List, Optional, Any
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class ComplementarityDetector:
    """Detectează dorințe complementare (N flexibil)"""
    
    def __init__(self):
        try:
            self.nlp_ro = spacy.load("ro_core_news_sm")
            self.nlp_en = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp_ro = None
            self.nlp_en = None
    
    async def detect_complementarity(
        self,
        wish_ids: List[str],
        min_similarity: float = 0.7,
        max_wishes: int = 7
    ) -> Dict:
        """
        Detectează dorințe complementare
        
        Args:
            wish_ids: Lista de ID-uri de wish-uri
            min_similarity: Similaritate minimă (0.7 default)
            max_wishes: Număr maxim de wish-uri de combinat (7 default)
        
        Returns:
            {
                "combined_wish_id": str,
                "original_wishes": List[str],
                "combined_intent": str,
                "similarity_score": float,
                "business_score": float
            }
        """
        # TODO: Load wishes from database
        # For now, use mock data
        wishes = self._load_wishes_mock(wish_ids)
        
        if len(wishes) < 2:
            raise ValueError("Need at least 2 wishes to combine")
        
        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(wishes)
        
        # Find complementary groups
        complementary_groups = self._find_complementary_groups(
            wishes,
            similarity_matrix,
            min_similarity,
            max_wishes
        )
        
        if not complementary_groups:
            raise ValueError("No complementary wishes found")
        
        # Select best group (highest average similarity)
        best_group = max(complementary_groups, key=lambda g: g["avg_similarity"])
        
        # Combine intents
        combined_intent = self._combine_intents(best_group["wishes"])
        
        # Calculate combined business score
        combined_business_score = self._calculate_combined_business_score(
            best_group["wishes"]
        )
        
        return {
            "combined_wish_id": f"combined_{'_'.join(wish_ids[:3])}",
            "original_wishes": best_group["wish_ids"],
            "combined_intent": combined_intent,
            "similarity_score": best_group["avg_similarity"],
            "business_score": combined_business_score
        }
    
    def _load_wishes_mock(self, wish_ids: List[str]) -> List[Dict]:
        """Mock function - în realitate ar încărca din DB"""
        return [
            {"id": wid, "intent": f"Intent for {wid}", "domain": "software"}
            for wid in wish_ids
        ]
    
    def _calculate_similarity_matrix(self, wishes: List[Dict]) -> np.ndarray:
        """Calculează matricea de similaritate"""
        # Extract embeddings
        embeddings = []
        for wish in wishes:
            intent = wish.get("intent", "")
            language = self._detect_language(intent)
            nlp = self.nlp_ro if language == "ro" else self.nlp_en
            
            if nlp:
                doc = nlp(intent)
                # Use average of word vectors
                embedding = doc.vector
            else:
                # Fallback: simple embedding
                embedding = np.zeros(300)
            
            embeddings.append(embedding)
        
        embeddings = np.array(embeddings)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(embeddings)
        
        return similarity_matrix
    
    def _find_complementary_groups(
        self,
        wishes: List[Dict],
        similarity_matrix: np.ndarray,
        min_similarity: float,
        max_wishes: int
    ) -> List[Dict]:
        """Găsește grupuri de wish-uri complementare"""
        groups = []
        
        # Start with each wish as seed
        for i, wish in enumerate(wishes):
            group = {
                "wish_ids": [wish["id"]],
                "wishes": [wish],
                "indices": [i],
                "avg_similarity": 1.0
            }
            
            # Add complementary wishes
            for j, other_wish in enumerate(wishes):
                if i == j:
                    continue
                
                similarity = similarity_matrix[i][j]
                
                # Check if complementary
                if (similarity >= min_similarity and
                    self._are_complementary(wish, other_wish) and
                    len(group["wishes"]) < max_wishes):
                    
                    group["wish_ids"].append(other_wish["id"])
                    group["wishes"].append(other_wish)
                    group["indices"].append(j)
                    
                    # Recalculate average similarity
                    group_similarities = [
                        similarity_matrix[group["indices"][k]][group["indices"][l]]
                        for k in range(len(group["indices"]))
                        for l in range(k + 1, len(group["indices"]))
                    ]
                    group["avg_similarity"] = np.mean(group_similarities)
            
            # Only add groups with at least 2 wishes
            if len(group["wishes"]) >= 2:
                groups.append(group)
        
        return groups
    
    def _are_complementary(self, wish1: Dict, wish2: Dict) -> bool:
        """Verifică dacă două wish-uri sunt complementare"""
        # Same domain
        if wish1.get("domain") != wish2.get("domain"):
            return False
        
        # Same context (simplified check)
        intent1 = wish1.get("intent", "").lower()
        intent2 = wish2.get("intent", "").lower()
        
        # Check for common keywords (same context)
        common_keywords = set(intent1.split()) & set(intent2.split())
        if len(common_keywords) < 2:
            return False
        
        # Check if they don't contradict
        if self._contradict(wish1, wish2):
            return False
        
        return True
    
    def _contradict(self, wish1: Dict, wish2: Dict) -> bool:
        """Verifică dacă wish-urile se contrazic"""
        # Simple contradiction check
        intent1 = wish1.get("intent", "").lower()
        intent2 = wish2.get("intent", "").lower()
        
        contradictions = [
            ("free", "paid"),
            ("simple", "complex"),
            ("mobile", "desktop"),
            ("online", "offline")
        ]
        
        for neg, pos in contradictions:
            if (neg in intent1 and pos in intent2) or (pos in intent1 and neg in intent2):
                return True
        
        return False
    
    def _combine_intents(self, wishes: List[Dict]) -> str:
        """Combină intențiile într-un intent combinat"""
        intents = [w.get("intent", "") for w in wishes]
        
        # Extract keywords from all intents
        all_keywords = []
        for intent in intents:
            words = intent.lower().split()
            # Remove stop words
            stop_words = {"the", "a", "an", "is", "are", "for", "de", "și", "sau"}
            keywords = [w for w in words if w not in stop_words and len(w) > 3]
            all_keywords.extend(keywords)
        
        # Get most common keywords
        from collections import Counter
        keyword_freq = Counter(all_keywords)
        top_keywords = [word for word, freq in keyword_freq.most_common(5)]
        
        # Combine into intent
        combined = " ".join(top_keywords)
        
        return combined
    
    def _calculate_combined_business_score(self, wishes: List[Dict]) -> float:
        """Calculează scor business combinat"""
        scores = [w.get("business_score", 0.5) for w in wishes]
        
        # Average + bonus for combination
        avg_score = np.mean(scores)
        combination_bonus = min(len(wishes) * 0.05, 0.2)  # Max 20% bonus
        
        return min(avg_score + combination_bonus, 1.0)
    
    def _detect_language(self, text: str) -> str:
        """Detectează limba"""
        romanian_keywords = ["mi-aș", "ar fi", "ce bine", "vreau"]
        if any(kw in text.lower() for kw in romanian_keywords):
            return "ro"
        return "en"
