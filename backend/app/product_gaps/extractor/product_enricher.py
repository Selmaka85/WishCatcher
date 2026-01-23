"""
Product Enricher - Îmbogățește informațiile despre produse fizice
Pentru identificare ușoară și vânzare pe Amazon/eMAG
"""

import re
from typing import Dict, List, Optional, Any
import spacy


class ProductEnricher:
    """Îmbogățește informațiile despre produse fizice pentru vânzare"""
    
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
    
    def enrich_product(
        self,
        product_name: str,
        wish_data: Dict[str, Any],
        language: str = "ro"
    ) -> Dict[str, Any]:
        """
        Îmbogățește informațiile despre produs pentru vânzare
        
        Returns:
            {
                "product_name": str,
                "product_category": str,
                "brand": Optional[str],
                "model": Optional[str],
                "specifications": Dict[str, str],
                "intent_summary": str,
                "problem": str,
                "requirements": List[str],
                "use_case": str,
                "urgency": str,
                "context": str,
                "price_range": Optional[str],
                "market_opportunity": {
                    "demand_level": str,
                    "competition": str,
                    "profit_margin_estimate": str,
                    "fba_eligible": bool,
                    "best_marketplace": str
                }
            }
        """
        intent = wish_data.get("intent", "")
        structured = wish_data.get("structured", {})
        trigger_analysis = wish_data.get("trigger_analysis", {})
        
        # Extrage brand și model
        brand, model = self._extract_brand_model(product_name, language)
        
        # Extrage specificații
        specifications = self._extract_specifications(intent, structured, language)
        
        # Construiește intent_summary
        intent_summary = self._build_intent_summary(structured, language)
        
        # Extrage problem-ul
        problem = structured.get("problem", "") or self._extract_problem_from_intent(intent, trigger_analysis, language)
        
        # Extrage requirements
        requirements = self._extract_requirements(intent, structured, language)
        
        # Determină use_case
        use_case = self._determine_use_case(structured, trigger_analysis, language)
        
        # Determină urgency
        urgency = self._determine_urgency(trigger_analysis, structured)
        
        # Construiește context
        context = self._build_context(structured, trigger_analysis, language)
        
        # Estimează price_range
        price_range = self._estimate_price_range(product_name, specifications, language)
        
        # Analizează market opportunity
        market_opportunity = self._analyze_market_opportunity(
            product_name, structured, wish_data
        )
        
        return {
            "product_name": product_name,
            "product_category": self._determine_category(product_name, language),
            "brand": brand,
            "model": model,
            "specifications": specifications,
            "intent_summary": intent_summary,
            "problem": problem,
            "requirements": requirements,
            "use_case": use_case,
            "urgency": urgency,
            "context": context,
            "price_range": price_range,
            "market_opportunity": market_opportunity
        }
    
    def _extract_brand_model(self, product_name: str, language: str) -> tuple:
        """Extrage brand și model din numele produsului"""
        brands = {
            "ro": ["apple", "samsung", "xiaomi", "huawei", "sony", "lg", "dell", "hp", "lenovo", "asus", "acer", "msi", "razer", "logitech"],
            "en": ["apple", "samsung", "xiaomi", "huawei", "sony", "lg", "dell", "hp", "lenovo", "asus", "acer", "msi", "razer", "logitech"]
        }
        
        brand_list = brands.get(language, brands["en"])
        product_lower = product_name.lower()
        
        brand = None
        for b in brand_list:
            if b in product_lower:
                brand = b.capitalize()
                break
        
        # Extrage model (numere, coduri de model)
        model_match = re.search(r'([A-Z0-9]+[-]?[A-Z0-9]+)', product_name)
        model = model_match.group(1) if model_match else None
        
        return brand, model
    
    def _extract_specifications(
        self,
        intent: str,
        structured: Dict[str, Any],
        language: str
    ) -> Dict[str, str]:
        """Extrage specificații tehnice"""
        specs = {}
        
        # Caută specificații comune
        spec_patterns = {
            "ro": [
                (r"(\d+)\s*GB\s*(?:RAM|ram)", "RAM"),
                (r"(\d+)\s*TB\s*(?:SSD|ssd|HDD|hdd)", "Storage"),
                (r"(\d+)\"", "Screen Size"),
                (r"(?:procesor|processor)\s+([A-Za-z0-9\s]+)", "Processor"),
                (r"(?:GPU|gpu|graphics)\s+([A-Za-z0-9\s]+)", "GPU")
            ],
            "en": [
                (r"(\d+)\s*GB\s*(?:RAM|ram)", "RAM"),
                (r"(\d+)\s*TB\s*(?:SSD|ssd|HDD|hdd)", "Storage"),
                (r"(\d+)\"", "Screen Size"),
                (r"(?:processor|CPU)\s+([A-Za-z0-9\s]+)", "Processor"),
                (r"(?:GPU|graphics)\s+([A-Za-z0-9\s]+)", "GPU")
            ]
        }
        
        patterns = spec_patterns.get(language, spec_patterns["en"])
        full_text = intent + " " + structured.get("what", "") + " " + structured.get("how", "")
        
        for pattern, spec_name in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                specs[spec_name] = match.group(1) if match.groups() else match.group(0)
        
        return specs
    
    def _build_intent_summary(self, structured: Dict[str, Any], language: str) -> str:
        """Construiește rezumat intent pentru produs"""
        what = structured.get("what", "")
        use_case = structured.get("use_case", "")
        
        if language == "ro":
            if use_case:
                return f"Utilizatorul dorește {what.lower()} pentru {use_case.lower()}"
            else:
                return f"Utilizatorul dorește {what.lower()}"
        else:
            if use_case:
                return f"User wants {what.lower()} for {use_case.lower()}"
            else:
                return f"User wants {what.lower()}"
    
    def _extract_problem_from_intent(
        self,
        intent: str,
        trigger_analysis: Optional[Dict],
        language: str
    ) -> str:
        """Extrage problem-ul din intent"""
        if trigger_analysis:
            pain_points = trigger_analysis.get("pain_points", [])
            if pain_points:
                return ". ".join(pain_points[:2])
        
        # Caută în intent
        problem_patterns = {
            "ro": [
                r"(?:problema|problemei)\s+(?:este|că|e)\s+([^.!?]+)",
                r"(?:nu funcționează|nu merge|nu e bun)\s+(?:pentru|la)\s+([^.!?]+)"
            ],
            "en": [
                r"(?:problem|issue)\s+(?:is|that)\s+([^.!?]+)",
                r"(?:doesn't work|doesn't function)\s+(?:for|at)\s+([^.!?]+)"
            ]
        }
        
        patterns = problem_patterns.get(language, problem_patterns["en"])
        for pattern in patterns:
            match = re.search(pattern, intent, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]
        
        return "Produs necesar pentru nevoi identificate"
    
    def _extract_requirements(
        self,
        intent: str,
        structured: Dict[str, Any],
        language: str
    ) -> List[str]:
        """Extrage cerințe/requirements"""
        requirements = []
        
        # Din structured.how
        how = structured.get("how", "")
        if how:
            # Extrage features din "how"
            features = structured.get("key_features", [])
            requirements.extend(features)
        
        # Din specificații
        specs = self._extract_specifications(intent, structured, language)
        for spec_name, spec_value in specs.items():
            requirements.append(f"{spec_name}: {spec_value}")
        
        return requirements[:10]  # Max 10 requirements
    
    def _determine_use_case(
        self,
        structured: Dict[str, Any],
        trigger_analysis: Optional[Dict],
        language: str
    ) -> str:
        """Determină use case-ul"""
        # Din structured.who și structured.how
        who = structured.get("who", "")
        how = structured.get("how", "")
        
        use_cases = {
            "ro": {
                "programator": "programare și dezvoltare software",
                "developer": "programare și dezvoltare software",
                "designer": "design grafic și creativitate",
                "student": "studii și proiecte academice",
                "gaming": "gaming și entertainment"
            },
            "en": {
                "programmer": "programming and software development",
                "developer": "programming and software development",
                "designer": "graphic design and creativity",
                "student": "studies and academic projects",
                "gaming": "gaming and entertainment"
            }
        }
        
        cases = use_cases.get(language, use_cases["en"])
        text_lower = (who + " " + how).lower()
        
        for key, value in cases.items():
            if key in text_lower:
                return value
        
        return "general use"
    
    def _determine_urgency(
        self,
        trigger_analysis: Optional[Dict],
        structured: Dict[str, Any]
    ) -> str:
        """Determină urgența"""
        if trigger_analysis:
            emotional_intensity = trigger_analysis.get("emotional_intensity", 0.5)
            if emotional_intensity > 0.7:
                return "high"
            elif emotional_intensity > 0.4:
                return "medium"
        
        return "medium"
    
    def _build_context(
        self,
        structured: Dict[str, Any],
        trigger_analysis: Optional[Dict],
        language: str
    ) -> str:
        """Construiește context"""
        parts = []
        
        who = structured.get("who", "")
        when = structured.get("when", "")
        
        if language == "ro":
            if who:
                parts.append(f"Utilizator: {who}")
            if when:
                parts.append(f"Situație: {when}")
        else:
            if who:
                parts.append(f"User: {who}")
            if when:
                parts.append(f"Situation: {when}")
        
        return ". ".join(parts) if parts else "Context general"
    
    def _estimate_price_range(
        self,
        product_name: str,
        specifications: Dict[str, str],
        language: str
    ) -> Optional[str]:
        """Estimează range-ul de preț"""
        # Estimări bazate pe tipul produsului și specificații
        product_lower = product_name.lower()
        
        if "laptop" in product_lower or "notebook" in product_lower:
            ram = specifications.get("RAM", "")
            if ram:
                ram_gb = int(re.search(r'(\d+)', ram).group(1)) if re.search(r'(\d+)', ram) else 0
                if ram_gb >= 16:
                    return "4000-8000 lei"
                elif ram_gb >= 8:
                    return "2000-4000 lei"
            return "2000-6000 lei"
        
        elif "phone" in product_lower or "smartphone" in product_lower or "telefon" in product_lower:
            return "1000-5000 lei"
        
        elif "headphones" in product_lower or "căști" in product_lower:
            return "200-1000 lei"
        
        elif "tablet" in product_lower or "tabletă" in product_lower:
            return "1000-3000 lei"
        
        return None
    
    def _analyze_market_opportunity(
        self,
        product_name: str,
        structured: Dict[str, Any],
        wish_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analizează oportunitatea de piață"""
        # Analiză simplificată bazată pe structured și wish_data
        problem = structured.get("problem", "")
        urgency = self._determine_urgency(wish_data.get("trigger_analysis"), structured)
        
        # Estimează demand level
        demand_level = "medium"
        if urgency == "high":
            demand_level = "high"
        
        # Estimează competition (simplified)
        competition = "medium"
        
        # Estimează profit margin
        profit_margin = "25-35%"
        
        # FBA eligible (simplified - majoritatea produselor electronice sunt)
        fba_eligible = True
        
        # Best marketplace (va fi determinat de GapDetector)
        best_marketplace = "to_be_determined"
        
        return {
            "demand_level": demand_level,
            "competition": competition,
            "profit_margin_estimate": profit_margin,
            "fba_eligible": fba_eligible,
            "best_marketplace": best_marketplace
        }
    
    def _determine_category(self, product_name: str, language: str) -> str:
        """Determină categoria produsului"""
        product_lower = product_name.lower()
        
        categories = {
            "electronics": ["laptop", "notebook", "computer", "pc", "telefon", "smartphone", "tablet", "tabletă"],
            "audio": ["căști", "headphones", "headset", "boxe", "speakers"],
            "wearables": ["smartwatch", "ceas", "watch"],
            "accessories": ["keyboard", "mouse", "monitor", "ecran"]
        }
        
        for category, keywords in categories.items():
            if any(kw in product_lower for kw in keywords):
                return category
        
        return "other"
