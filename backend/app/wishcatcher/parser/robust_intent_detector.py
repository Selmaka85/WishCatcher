"""
Robust Intent Detector - Detectează intenția indiferent de forma cuvintelor
Multi-layer: Pattern Matching → NLP Semantic → Context Combination
Cu filtrare nonsensuri și imposibilități
"""

import spacy
import re
from typing import Dict, List, Optional
from collections import Counter
from langdetect import detect, LangDetectException


class RobustIntentDetector:
    """Detectează intenția indiferent de forma cuvintelor"""
    
    def __init__(self, languages: List[str] = ["ro", "en"]):
        self.languages = languages
        self.nlp_models = {}
        
        # Load NLP models
        try:
            if "ro" in languages:
                self.nlp_models["ro"] = spacy.load("ro_core_news_sm")
            if "en" in languages:
                self.nlp_models["en"] = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy models not found. Run: python -m spacy download ro_core_news_sm en_core_web_sm")
        
        # Language-specific patterns (EXTINS cu pattern-uri omise)
        self.patterns = {
            "ro": {
                "wish": [
                    r"mi-aș dori",
                    r"ce bine ar fi",
                    r"ar fi util",
                    r"vreau",
                    r"am nevoie",
                    r"aș vrea",
                    r"ar fi minunat",
                    r"sper că",
                    r"ar fi trebuit să",
                    r"mi-aș dori ca.*să aibă",
                    r"ar fi perfect dacă",
                    r"urăsc că.*nu",
                    r"mă enervează că.*nu"
                ],
                "negative": [  # Lipsă = Dorință
                    r"nu există",
                    r"lipsă",
                    r"nu am găsit",
                    r"nimic nu face",
                    r"nu există o",
                    r"lipsă o",
                    r"singurul lucru care lipsește",
                    r"doar lipsește",
                    r"lipsește.*funcție",
                    r"nu are",
                    r"lipsește.*feature",
                    # Categoria 1: Lipsă și Absență (NOU)
                    r"de ce nu există în românia",
                    r"de ce nu există la noi",
                    r"nu se găsește la noi",
                    r"unde pot găsi în RO",
                    r"alternativă românească la",
                    r"singura opțiune este",
                    r"există vreo aplicație pentru",
                    r"păcat că în românia nu"
                ],
                "comparison": [  # Comparații = Nevoie de îmbunătățire
                    r"ar trebui să fie",
                    r"mai bun decât",
                    r"ar putea fi",
                    r"dacă ar fi",
                    r"ar fi mai bine",
                    r"alternativă la",
                    r"alternativă pentru",
                    r"în loc de",
                    r"mai degrabă decât"
                ],
                "question": [  # Întrebări retorice = Căutare
                    r"de ce nu există",
                    r"cum fac să",
                    r"există ceva care",
                    r"unde pot găsi",
                    r"ce aplicație",
                    # Categoria 1: Lipsă și Absență (NOU)
                    r"unde pot găsi în RO",
                    r"există vreo aplicație pentru",
                    # Categoria 4: Birocrație și Software (NOU)
                    r"cum se declară",
                    r"cum automatizez",
                    r"program de gestiune care să"
                ],
                "review_negative": [  # Review-uri negative = Oportunitate
                    r"e prost pentru",
                    r"nu recomand.*pentru că",
                    r"nu funcționează pentru",
                    r"prea scump",
                    r"lipsește",
                    r"nu are"
                ],
                "price_mention": [  # Mențiuni preț = Willingness to Pay
                    r"aș plăti",
                    r"dacă ar costa",
                    r"prea scump.*am nevoie",
                    r"ar plăti.*pentru",
                    r"buget.*pentru"
                ],
                "urgency": [  # Urgență = Prioritizare
                    r"urgent.*nevoie",
                    r"de mult timp caut",
                    r"în fiecare zi.*nevoie",
                    r"de.*luni.*caut",
                    r"necesar urgent"
                ],
                "frustration": [
                    r"e frustrant",
                    r"mă enervează",
                    r"e greu",
                    r"nu pot",
                    r"e dificil",
                    r"e enervant că",
                    r"mă deranjează că",
                    r"e complicat să",
                    r"fac manual",
                    r"făcând.*manual",
                    r"trebuie să.*manual",
                    r"proces.*manual",
                    # Categoria 2: Frustrare și Eșec (NOU)
                    r"m-am săturat de",
                    r"este un calvar să",
                    r"bătaie de joc",
                    r"nu răspunde nimeni la",
                    r"groaznic",
                    r"mizerabil",
                    r"deja a 3-a oară când",
                    r"coșmar birocratic"
                ],
                # Categoria 3: Recomandări Eșuate (NOU)
                "recommendation_failed": [
                    r"o firmă serioasă de",
                    r"cineva care se pricepe la",
                    r"recomandare meseriaș",
                    r"fără țepe",
                    r"meseriaș.*serios",
                    r"instalator.*serios",
                    r"electrician.*serios"
                ],
                # Categoria 4: Birocrație și Software (NOU)
                "bureaucracy_software": [
                    r"eroare e-factura",
                    r"eroare e-transport",
                    r"export excel",
                    r"integrare cu",
                    r"e-factura.*problema",
                    r"e-transport.*problema",
                    r"anaf.*problema",
                    r"declarație.*problema"
                ]
            },
            "en": {
                "wish": [
                    r"i wish",
                    r"would be",
                    r"it would be",
                    r"i want",
                    r"i need",
                    r"looking for",
                    r"would be great",
                    r"hope.*will",
                    r"should have",
                    r"wish.*had",
                    r"would be perfect if",
                    r"hate that.*doesn't",
                    r"hate that.*does not"
                ],
                "negative": [
                    r"doesn't exist",
                    r"no.*exists",
                    r"can't find",
                    r"nothing.*does",
                    r"there's no",
                    r"lack of",
                    r"the only thing missing",
                    r"only missing",
                    r"missing.*feature",
                    r"doesn't have",
                    r"does not have"
                ],
                "comparison": [
                    r"should be",
                    r"better than",
                    r"could be",
                    r"if.*would",
                    r"would be better",
                    r"alternative to",
                    r"alternative for",
                    r"instead of",
                    r"rather than"
                ],
                "question": [
                    r"why doesn't.*exist",
                    r"how do i",
                    r"is there.*that",
                    r"where can i find",
                    r"what.*app"
                ],
                "review_negative": [
                    r"is bad for",
                    r"don't recommend.*because",
                    r"doesn't work for",
                    r"too expensive",
                    r"missing",
                    r"doesn't have"
                ],
                "price_mention": [
                    r"would pay",
                    r"if.*cost",
                    r"too expensive.*need",
                    r"pay.*for",
                    r"budget.*for"
                ],
                "urgency": [
                    r"urgent.*need",
                    r"been looking for.*months",
                    r"every day.*need",
                    r"for.*months.*looking",
                    r"urgently need"
                ],
                "frustration": [
                    r"frustrating",
                    r"annoying",
                    r"can't",
                    r"hard to",
                    r"struggling",
                    r"annoying that",
                    r"bothers me that",
                    r"complicated to",
                    r"manually doing",
                    r"doing.*manually",
                    r"have to.*manually",
                    r"manual.*process"
                ]
            }
        }
    
    def detect_intent(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Detectează intenția din text
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "language": str,
                "formulation_type": str,
                "extracted_from": str,
                "domain": str,
                "technologies": List[str]
            }
        """
        # Quick check pentru nonsensuri/imposibilități (early filtering)
        if self._is_obvious_nonsense(text):
            return {
                "intent": None,
                "confidence": 0.0,
                "language": self._detect_language(text),
                "formulation_type": "filtered_nonsense",
                "extracted_from": "post",
                "domain": "other",
                "technologies": []
            }
        
        # Detect language
        language = self._detect_language(text)
        
        # Normalize text
        normalized = self._normalize_text(text)
        
        # Layer 1: Explicit intent (pattern matching)
        explicit_intent = self._detect_explicit_intent(normalized, language)
        
        # Layer 2: Implicit intent (NLP semantic)
        # Try implicit even if explicit exists (might be better)
        implicit_intent = self._detect_implicit_intent(text, language)
        if not explicit_intent or explicit_intent.get("confidence", 0) < 0.5:
            # Use implicit if explicit is weak or missing
            if implicit_intent.get("confidence", 0) > explicit_intent.get("confidence", 0):
                explicit_intent = implicit_intent
        elif implicit_intent.get("confidence", 0) > explicit_intent.get("confidence", 0):
            # Use implicit if it's better even when explicit exists
            explicit_intent = implicit_intent
        
        # Layer 3: Context combination
        if context and context.get("comments"):
            combined_intent = self._combine_with_context(explicit_intent, context)
            if combined_intent.get("confidence", 0) > explicit_intent.get("confidence", 0):
                explicit_intent = combined_intent
        
        # Extract domain and technologies
        domain = self._extract_domain(text, language)
        technologies = self._extract_technologies(text, language)
        
        return {
            **explicit_intent,
            "domain": domain,
            "technologies": technologies
        }
    
    def _detect_language(self, text: str) -> str:
        """
        Detectează limba textului
        
        Prioritizează româna pentru texte cu caractere românești specifice
        """
        # Verifică mai întâi caractere românești specifice (cel mai sigur indicator)
        romanian_chars = ['ă', 'â', 'î', 'ș', 'ț', 'Ă', 'Â', 'Î', 'Ș', 'Ț']
        has_romanian_chars = any(char in text for char in romanian_chars)
        
        # Verifică keywords românești comune
        romanian_keywords = ["mi-aș", "ar fi", "ce bine", "vreau", "am nevoie", "aș vrea", 
                            "lipsește", "nu există", "frustrant", "enervant", "problema",
                            "serviciu", "aplicație", "platformă", "tool", "ceva"]
        has_romanian_keywords = any(kw in text.lower() for kw in romanian_keywords)
        
        # Dacă are caractere românești specifice, e sigur română
        if has_romanian_chars:
            return "ro"
        
        try:
            lang = detect(text)
            
            # Corecție: langdetect uneori confundă româna cu italiană/spaniolă
            if lang in ["it", "es", "pt", "fr"] and has_romanian_keywords:
                return "ro"
            
            return lang if lang in self.languages else "en"
        except LangDetectException:
            # Fallback: keyword matching
            if has_romanian_keywords:
                return "ro"
            return "en"
    
    def _normalize_text(self, text: str) -> str:
        """Normalizează text pentru pattern matching"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _detect_explicit_intent(self, text: str, language: str) -> Dict:
        """Layer 1: Detectează intenție explicită (pattern matching) - EXTINS"""
        lang_patterns = self.patterns.get(language, self.patterns["en"])
        
        matches = []
        confidence_weights = {
            "wish": 0.9,
            "negative": 0.85,  # Lipsă = dorință puternică
            "comparison": 0.8,  # Comparație = nevoie
            "question": 0.75,  # Întrebare = căutare
            "review_negative": 0.85,  # Review negativ = oportunitate
            "price_mention": 0.7,  # Preț = willingness to pay
            "urgency": 0.9,  # Urgență = prioritizare
            "frustration": 0.8,
            # Categorii noi (NOU)
            "recommendation_failed": 0.9,  # Recomandări eșuate = nișă liberă (foarte valoroasă)
            "bureaucracy_software": 0.9  # Birocrație și Software = B2B SaaS (foarte monetizabilă)
        }
        
        for pattern_type, patterns in lang_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Extract context around match
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 200)
                    intent_text = text[start:end].strip()
                    
                    confidence = confidence_weights.get(pattern_type, 0.7)
                    
                    matches.append({
                        "type": pattern_type,
                        "text": intent_text,
                        "confidence": confidence,
                        "match_position": match.start()
                    })
        
        if matches:
            # Sort by confidence and position (earlier = more important)
            matches.sort(key=lambda x: (x["confidence"], -x["match_position"]), reverse=True)
            best_match = matches[0]
            
            # Extract core intent
            core_intent = self._extract_core_intent(best_match["text"], language)
            
            # Extract additional metadata
            metadata = {
                "pattern_type": best_match["type"],
                "price_mentioned": self._extract_price_mention(text, language) if best_match["type"] == "price_mention" else None,
                "urgency_detected": best_match["type"] == "urgency",
                "alternative_mentioned": best_match["type"] in ["comparison", "review_negative"]
            }
            
            return {
                "intent": core_intent,
                "confidence": best_match["confidence"],
                "language": language,
                "formulation_type": "explicit",
                "extracted_from": "post",
                "metadata": metadata
            }
        
        return {
            "intent": None,
            "confidence": 0.0,
            "language": language,
            "formulation_type": "none",
            "extracted_from": "post"
        }
    
    def _detect_implicit_intent(self, text: str, language: str) -> Dict:
        """Layer 2: Detectează intenție implicită (NLP semantic)"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return {"intent": None, "confidence": 0.0}
        
        # Skip very short texts
        if len(text.strip()) < 20:
            return {"intent": None, "confidence": 0.0}
        
        try:
            doc = nlp(text)
        except Exception as e:
            print(f"[WARNING] NLP processing error: {e}")
            return {"intent": None, "confidence": 0.0}
        
        # Extract entities
        entities = [ent.text for ent in doc.ents]
        
        # Extract action verbs
        action_verbs = [
            token.lemma_ for token in doc
            if token.pos_ == "VERB" and token.dep_ in ["ROOT", "ccomp"]
        ]
        
        # Extract objects
        objects = [
            token.text for token in doc
            if token.dep_ in ["dobj", "pobj"] and token.pos_ == "NOUN"
        ]
        
        # Build intent from components
        if entities or action_verbs or objects:
            intent_parts = []
            if action_verbs:
                intent_parts.append(action_verbs[0])
            if objects:
                intent_parts.append(objects[0])
            if entities:
                intent_parts.extend(entities[:2])
            
            intent = " ".join(intent_parts)
            
            return {
                "intent": intent,
                "confidence": 0.6,
                "language": language,
                "formulation_type": "implicit",
                "extracted_from": "post"
            }
        
        return {
            "intent": None,
            "confidence": 0.0,
            "language": language,
            "formulation_type": "none",
            "extracted_from": "post"
        }
    
    def _combine_with_context(self, intent: Dict, context: Dict) -> Dict:
        """Layer 3: Combină cu contextul din comentarii"""
        if not intent.get("intent"):
            return intent
        
        comments = context.get("comments", [])
        clarifications = []
        
        for comment in comments:
            comment_text = comment.get("text", "")
            if self._is_clarification(comment_text, intent["intent"]):
                clarifications.append(comment_text)
        
        if clarifications:
            combined_intent = self._merge_intents(intent["intent"], clarifications)
            
            return {
                **intent,
                "intent": combined_intent,
                "confidence": min(intent.get("confidence", 0.5) + 0.2, 1.0),
                "extracted_from": "combined",
                "clarifications_count": len(clarifications)
            }
        
        return intent
    
    def _is_clarification(self, text: str, original_intent: str) -> bool:
        """Verifică dacă comentariul clarifică intenția"""
        clarification_patterns = [
            r"(?:i mean|vreau să spun|adică)",
            r"(?:specifically|anume|mai exact)",
            r"(?:what i need|ce am nevoie|ce vreau)"
        ]
        
        for pattern in clarification_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _merge_intents(self, original: str, clarifications: List[str]) -> str:
        """Combină intent original cu clarificări"""
        all_text = original + " " + " ".join(clarifications)
        words = all_text.lower().split()
        
        stop_words = {"the", "a", "an", "is", "are", "was", "were",
                     "de", "și", "sau", "cu", "pentru", "the", "a"}
        
        word_freq = Counter(words)
        keywords = [
            word for word, freq in word_freq.most_common(10)
            if word not in stop_words and len(word) > 3
        ]
        
        return " ".join(keywords[:5])
    
    def _is_obvious_nonsense(self, text: str) -> bool:
        """
        Verifică rapid dacă textul e nonsens evident (early filtering)
        ÎMBUNĂTĂȚIT - filtrează mai agresiv garbage-ul
        """
        text_lower = text.lower()
        
        # Pattern-uri evidente de nonsens
        obvious_nonsense_patterns = [
            r"călătorie.*soare|soare.*călătorie",
            r"invenție.*călătorie.*soare",
            r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*soare",
            r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*stele",
            r"bine.*ar.*fi.*dacă.*s.*ar.*inventa.*galaxie",
            r"invenție.*magie|magie.*invenție",
            r"invenție.*super.*putere",
            r"telepatie|telechinezie",
            r"timp.*înapoi|time.*travel",
            r"perpetuum.*mobile|perpetual.*motion",
        ]
        
        for pattern in obvious_nonsense_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Verifică dacă conține cuvinte absurde multiple
        absurd_keywords = ["soare", "sun", "stele", "stars", "galaxie", "galaxy", 
                          "magie", "magic", "super putere", "super power"]
        matches = sum(1 for keyword in absurd_keywords if keyword in text_lower)
        
        # Dacă are 2+ keywords absurde, e probabil nonsens
        if matches >= 2:
            return True
        
        # NOU: Verifică dacă e prea vag (garbage)
        vague_patterns = [
            r"ceva.*nou", r"ceva.*mai.*bun", r"o.*chestie", r"un.*lucru",
            r"something.*new", r"something.*better", r"a.*thing", r"some.*stuff"
        ]
        for pattern in vague_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Verifică dacă are și specificitate (dacă nu, e garbage)
                specific_indicators = ["pentru", "care să", "care poate", "for", "that can", "that allows"]
                if not any(ind in text_lower for ind in specific_indicators):
                    return True  # E garbage (vag fără specificitate)
        
        # NOU: Verifică dacă e prea scurt și generic (garbage)
        if len(text_lower.split()) < 5:
            # Trebuie să aibă cel puțin un indicator de wish real
            wish_indicators = ["vreau", "doresc", "nevoie", "trebuie", "want", "need", "require"]
            if not any(ind in text_lower for ind in wish_indicators):
                return True  # E garbage (prea scurt și fără indicator)
        
        return False
    
    def _extract_core_intent(self, text: str, language: str) -> str:
        """Extrage intenția core din text"""
        nlp = self.nlp_models.get(language)
        if not nlp:
            return text[:100]
        
        doc = nlp(text)
        
        # Extract subject-verb-object (SVO)
        subject = None
        verb = None
        object_ = None
        
        for token in doc:
            if token.dep_ == "nsubj" and not subject:
                subject = token.text
            elif token.pos_ == "VERB" and token.dep_ == "ROOT" and not verb:
                verb = token.lemma_
            elif token.dep_ in ["dobj", "pobj"] and not object_:
                object_ = token.text
        
        intent_parts = []
        if subject:
            intent_parts.append(subject)
        if verb:
            intent_parts.append(verb)
        if object_:
            intent_parts.append(object_)
        
        return " ".join(intent_parts) if intent_parts else text[:100]
    
    def _extract_domain(self, text: str, language: str) -> str:
        """Extrage domeniul din text"""
        domain_keywords = {
            "software": ["app", "application", "software", "platform", "website", "aplicație"],
            "finance": ["money", "budget", "finance", "investment", "bani", "buget"],
            "health": ["health", "fitness", "diet", "exercise", "sănătate"],
            "education": ["education", "learning", "course", "educație", "curs"]
        }
        
        text_lower = text.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        
        return "other"
    
    def _extract_technologies(self, text: str, language: str) -> List[str]:
        """Extrage tehnologii menționate"""
        tech_keywords = {
            "mobile": ["mobile", "app", "ios", "android", "telefon", "iphone", "smartphone"],
            "web": ["web", "website", "browser", "online", "chrome", "firefox"],
            "api": ["api", "rest", "graphql", "endpoint"],
            "database": ["database", "sql", "nosql", "db", "postgres", "mysql"],
            "desktop": ["desktop", "windows", "mac", "linux", "application"],
            "extension": ["extension", "plugin", "addon", "browser extension"]
        }
        
        technologies = []
        text_lower = text.lower()
        
        for tech, keywords in tech_keywords.items():
            if any(kw in text_lower for kw in keywords):
                technologies.append(tech)
        
        return technologies
    
    def _extract_price_mention(self, text: str, language: str) -> Optional[Dict]:
        """Extrage mențiuni de preț (willingness to pay)"""
        price_patterns = {
            "ro": [
                r"aș plăti\s+(\d+)\s*(?:euro|eur|lei|ron)",
                r"dacă ar costa\s+(\d+)\s*(?:euro|eur|lei|ron)",
                r"buget\s+(\d+)\s*(?:euro|eur|lei|ron)",
                r"(\d+)\s*(?:euro|eur|lei|ron)\s+.*lună",
                r"(\d+)\s*(?:euro|eur|lei|ron)\s+.*an"
            ],
            "en": [
                r"would pay\s+(\d+)\s*(?:euro|eur|pounds|gbp|dollars|usd)",
                r"if.*cost\s+(\d+)\s*(?:euro|eur|pounds|gbp|dollars|usd)",
                r"budget.*(\d+)\s*(?:euro|eur|pounds|gbp|dollars|usd)",
                r"(\d+)\s*(?:euro|eur|pounds|gbp|dollars|usd).*month",
                r"(\d+)\s*(?:euro|eur|pounds|gbp|dollars|usd).*year"
            ]
        }
        
        patterns = price_patterns.get(language, price_patterns["en"])
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                currency = "EUR" if "euro" in pattern or "eur" in pattern else "GBP" if "pound" in pattern else "USD"
                
                # Detect period
                period = "one-time"
                if "lună" in text_lower or "month" in text_lower:
                    period = "monthly"
                elif "an" in text_lower or "year" in text_lower:
                    period = "yearly"
                
                return {
                    "amount": amount,
                    "currency": currency,
                    "period": period,
                    "text": match.group(0)
                }
        
        return None