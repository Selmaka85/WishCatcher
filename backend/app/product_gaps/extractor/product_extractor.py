"""
Product Extractor - Extrage automat nume produse din wish-uri
"""

import re
from typing import List, Dict, Optional, Any
import spacy
from .product_enricher import ProductEnricher


class ProductExtractor:
    """Extrage nume produse și categorii din wish-uri"""
    
    def __init__(self):
        self.nlp_models = {}
        try:
            self.nlp_models["ro"] = spacy.load("ro_core_news_sm")
        except OSError:
            print("[WARNING] Romanian spaCy model not found")
        try:
            self.nlp_models["en"] = spacy.load("en_core_web_sm")
        except OSError:
            print("[WARNING] English spaCy model not found")
        
        # Product Enricher pentru informații bogate
        self.product_enricher = ProductEnricher()
        
        # Keywords produse fizice (EXTINS)
        self.product_keywords = {
            "ro": [
                # Electronice
                "laptop", "notebook", "computer", "pc", "calculator", "desktop",
                "telefon", "smartphone", "iphone", "samsung", "xiaomi", "huawei", "oppo", "oneplus",
                "căști", "headphones", "headset", "casti", "earbuds", "airpods",
                "smartwatch", "ceas", "watch", "fitness tracker", "bandă fitness",
                "tabletă", "tablet", "ipad", "kindle",
                "monitor", "ecran", "display", "screen",
                "tastatură", "keyboard", "mouse", "trackpad",
                "boxe", "speakers", "difuzor", "soundbar", "subwoofer",
                "cameră", "camera", "foto", "video", "webcam", "action camera",
                "router", "switch", "nas", "server",
                # Accesorii
                "powerbank", "baterie", "battery", "charger", "încărcător",
                "car case", "husă", "stand", "suport",
                # Haine și accesorii
                "haine", "tricou", "pantaloni", "adidasi", "incaltaminte", "geaca", "jacheta",
                "ceas", "ochelari", "solar", "ghiozdan", "rucsac",
                # Jucării și hobby
                "jucărie", "toy", "joc", "game", "console", "playstation", "xbox", "nintendo",
                "drone", "rc", "robot", "lego",
                # Casa și bucătărie
                "aspirator", "robot", "masina de spalat", "frigider", "cuptor", "microunde",
                "mixer", "blender", "cafetiera", "fierbator",
                # Sport și fitness
                "bicicleta", "treadmill", "bike", "trotineta", "skateboard",
                # Auto
                "masina", "auto", "car", "accesorii auto", "gps", "dashcam"
            ],
            "en": [
                # Electronics
                "laptop", "notebook", "computer", "pc", "desktop",
                "phone", "smartphone", "iphone", "samsung", "xiaomi", "huawei", "oppo", "oneplus",
                "headphones", "headset", "earbuds", "airpods",
                "smartwatch", "watch", "fitness tracker", "fitness band",
                "tablet", "ipad", "kindle",
                "monitor", "screen", "display",
                "keyboard", "mouse", "trackpad",
                "speakers", "soundbar", "subwoofer",
                "camera", "photo", "video", "webcam", "action camera",
                "router", "switch", "nas", "server",
                # Accessories
                "powerbank", "battery", "charger",
                "case", "stand", "mount",
                # Clothing
                "clothes", "shirt", "pants", "shoes", "jacket", "backpack",
                "watch", "glasses", "sunglasses",
                # Toys and hobby
                "toy", "game", "console", "playstation", "xbox", "nintendo",
                "drone", "rc", "robot", "lego",
                # Home and kitchen
                "vacuum", "robot", "washing machine", "refrigerator", "oven", "microwave",
                "mixer", "blender", "coffee maker", "kettle",
                # Sports and fitness
                "bike", "bicycle", "treadmill", "scooter", "skateboard",
                # Auto
                "car", "auto", "car accessories", "gps", "dashcam"
            ]
        }
        
        # Pattern-uri pentru identificare produse fizice (EXTINS)
        self.physical_product_patterns = {
            "ro": [
                # Pattern-uri directe
                r"nu se găsește pe eMAG", r"nu se găsește pe emag",
                r"comand de pe Amazon", r"comand de pe amazon",
                r"lipsește de pe eMAG", r"lipsește de pe emag",
                r"prea scump pe eMAG", r"prea scump pe emag",
                r"alternativă la.*de pe Amazon",
                r"unde pot cumpăra.*în România",
                r"nu există.*pe eMAG", r"nu există.*pe emag",
                # Pattern-uri indirecte
                r"vreau să cumpăr", r"vreau sa cumpar",
                r"as vrea sa cumpar", r"aș vrea să cumpăr",
                r"caut.*produs", r"caut.*produse",
                r"recomandare.*produs", r"recomandare.*produse",
                r"ce.*să cumpăr", r"ce.*sa cumpar",
                r"unde.*găsesc", r"unde.*gasesti",
                r"nu găsesc.*în românia", r"nu gasesc.*in romania",
                r"prea scump.*românia", r"prea scump.*romania",
                r"mai ieftin.*amazon", r"mai ieftin.*amazon",
                r"comand.*din.*străinătate", r"comand.*din.*strainatate",
                # Pattern-uri brand-uri
                r"(iphone|samsung|xiaomi|huawei|sony|lg|dell|hp|lenovo|asus|acer).*\d+",
                r"(airpods|galaxy|pixel|oneplus).*\d+",
            ],
            "en": [
                # Direct patterns
                r"not available on.*emag", r"can't find on.*emag",
                r"order from.*amazon", r"missing from.*emag",
                r"too expensive on.*emag",
                r"alternative to.*on amazon",
                r"where can i buy.*in romania",
                # Indirect patterns
                r"want to buy", r"looking for.*product",
                r"recommend.*product", r"what.*should i buy",
                r"where.*can i find", r"can't find.*in romania",
                r"too expensive.*romania", r"cheaper.*amazon",
                r"order.*from.*abroad",
                # Brand patterns
                r"(iphone|samsung|xiaomi|huawei|sony|lg|dell|hp|lenovo|asus|acer).*\d+",
                r"(airpods|galaxy|pixel|oneplus).*\d+",
            ]
        }
        
        # Brand-uri cunoscute (pentru identificare mai bună)
        self.brand_keywords = {
            "ro": ["apple", "samsung", "xiaomi", "huawei", "sony", "lg", "dell", "hp", "lenovo", "asus", "acer", "msi", "razer", "logitech"],
            "en": ["apple", "samsung", "xiaomi", "huawei", "sony", "lg", "dell", "hp", "lenovo", "asus", "acer", "msi", "razer", "logitech"]
        }
    
    def is_physical_product(self, text: str, language: str = "ro", context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verifică dacă wish-ul este despre un produs fizic (RELAXAT)
        
        Args:
            text: Textul wish-ului
            language: Limba textului
            context: Context suplimentar (opțional)
            
        Returns:
            True dacă e produs fizic, False altfel
        """
        # Folosește context complet dacă e disponibil
        full_text = text
        if context:
            # Adaugă text din context dacă există
            if isinstance(context, dict):
                context_text = context.get("post_text", "") or context.get("text", "") or ""
                if context_text and context_text != text:
                    full_text = f"{text} {context_text}"
        
        text_lower = full_text.lower()
        
        # Verifică pattern-uri specifice (prioritate mare)
        patterns = self.physical_product_patterns.get(language, [])
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Verifică keywords produse fizice (RELAXAT: doar 1 keyword e suficient)
        keywords = self.product_keywords.get(language, [])
        keyword_count = sum(1 for kw in keywords if kw in text_lower)
        
        # RELAXAT: Dacă are cel puțin 1 keyword de produse fizice, e probabil produs fizic
        if keyword_count >= 1:
            return True
        
        # Verifică brand-uri
        brands = self.brand_keywords.get(language, [])
        if any(brand in text_lower for brand in brands):
            return True
        
        # Verifică cu NLP (entități)
        nlp = self.nlp_models.get(language)
        if nlp:
            try:
                doc = nlp(full_text)
                # Verifică dacă are entități de tip PRODUS sau ORGANIZAȚIE (brand-uri)
                for ent in doc.ents:
                    if ent.label_ in ["PRODUCT", "ORG", "MISC"]:
                        return True
            except:
                pass
        
        return False
    
    def extract_product_name(self, text: str, language: str = "ro", context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Extrage numele produsului din text (ÎMBUNĂTĂȚIT)
        
        Args:
            text: Textul wish-ului
            language: Limba textului
            context: Context suplimentar (opțional)
            
        Returns:
            Numele produsului extras sau None
        """
        # Folosește context complet dacă e disponibil
        full_text = text
        if context:
            if isinstance(context, dict):
                context_text = context.get("post_text", "") or context.get("text", "") or ""
                if context_text and context_text != text:
                    full_text = f"{text} {context_text}"
        
        # Pattern matching pentru nume produse comune (EXTINS)
        product_patterns = {
            "ro": [
                # Pattern-uri cu brand-uri
                r"((?:iphone|samsung|xiaomi|huawei|sony|lg|dell|hp|lenovo|asus|acer|msi|razer|logitech)\s+\w+(?:\s+\w+)*)",
                # Pattern-uri produse
                r"(laptop|notebook|computer|pc|calculator)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(telefon|smartphone|iphone|samsung)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(căști|headphones|headset|airpods)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(smartwatch|ceas|watch|fitness tracker)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(tabletă|tablet|ipad|kindle)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(monitor|ecran|display)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(tastatură|keyboard|mouse|trackpad)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(boxe|speakers|difuzor|soundbar)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
                r"(cameră|camera|webcam)\s+([a-zăâîșț0-9]+(?:\s+[a-zăâîșț0-9]+)*)?",
            ],
            "en": [
                # Brand patterns
                r"((?:iphone|samsung|xiaomi|huawei|sony|lg|dell|hp|lenovo|asus|acer|msi|razer|logitech)\s+\w+(?:\s+\w+)*)",
                # Product patterns
                r"(laptop|notebook|computer|pc)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(phone|smartphone|iphone|samsung)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(headphones|headset|earbuds|airpods)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(smartwatch|watch|fitness tracker)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(tablet|ipad|kindle)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(monitor|screen|display)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(keyboard|mouse|trackpad)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(speakers|soundbar)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
                r"(camera|webcam)\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)?",
            ]
        }
        
        patterns = product_patterns.get(language, [])
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                # Dacă pattern-ul are un singur grup (brand pattern), folosește-l direct
                if len(match.groups()) == 1:
                    return match.group(1).strip()
                # Altfel, combină tipul produsului cu specificațiile
                product_type = match.group(1)
                product_spec = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                if product_spec:
                    return f"{product_type} {product_spec}".strip()
                return product_type
        
        # NLP extraction (îmbunătățit)
        nlp = self.nlp_models.get(language)
        if nlp:
            try:
                doc = nlp(full_text)
                # Extrage entități de tip PRODUS sau ORGANIZAȚIE (brand-uri)
                for ent in doc.ents:
                    if ent.label_ in ["PRODUCT", "ORG", "MISC"]:
                        # Verifică dacă entitatea conține keywords de produse
                        ent_lower = ent.text.lower()
                        keywords = self.product_keywords.get(language, [])
                        brands = self.brand_keywords.get(language, [])
                        if any(kw in ent_lower for kw in keywords) or any(brand in ent_lower for brand in brands):
                            return ent.text
                
                # Extrage noun phrases care conțin keywords
                keywords = self.product_keywords.get(language, [])
                brands = self.brand_keywords.get(language, [])
                for chunk in doc.noun_chunks:
                    chunk_text = chunk.text.lower()
                    if any(kw in chunk_text for kw in keywords) or any(brand in chunk_text for brand in brands):
                        return chunk.text
            except Exception as e:
                print(f"[ProductExtractor] NLP error: {e}")
                pass
        
        # Fallback îmbunătățit: extrage cuvinte în jurul keywords
        words = full_text.split()
        keywords = self.product_keywords.get(language, [])
        brands = self.brand_keywords.get(language, [])
        product_words = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            # Verifică keywords sau brand-uri
            if any(kw in word_lower for kw in keywords) or any(brand in word_lower for brand in brands):
                # Ia 3-4 cuvinte înainte și după pentru context mai bun
                start = max(0, i - 3)
                end = min(len(words), i + 4)
                product_words = words[start:end]
                break
        
        if product_words:
            return " ".join(product_words)
        
        return None
    
    def extract_category(self, text: str, language: str = "ro") -> Optional[str]:
        """
        Extrage categoria produsului din text
        
        Args:
            text: Textul wish-ului
            language: Limba textului
            
        Returns:
            Categoria produsului sau None
        """
        text_lower = text.lower()
        
        categories = {
            "electronics": ["laptop", "notebook", "computer", "pc", "calculator", "telefon", "smartphone", "tabletă", "tablet"],
            "audio": ["căști", "headphones", "headset", "boxe", "speakers", "difuzor"],
            "wearables": ["smartwatch", "ceas", "watch", "fitness tracker"],
            "accessories": ["tastatură", "keyboard", "mouse", "monitor", "ecran"],
            "clothing": ["haine", "tricou", "pantaloni", "adidasi", "incaltaminte", "clothes", "shirt", "pants", "shoes"],
            "toys": ["jucărie", "toy", "joc", "game"]
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return "other"
    
    def extract_products_from_wish(self, wish_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrage produse din un wish (ÎMBUNĂTĂȚIT - folosește context complet)
        
        Args:
            wish_data: Datele wish-ului (WishData)
            
        Returns:
            Lista de produse extrase
        """
        products = []
        
        intent = wish_data.get("intent", "")
        language = wish_data.get("language", "ro")
        
        # Obține context complet (din wish_data sau din trigger_analysis)
        context = None
        if isinstance(wish_data, dict):
            # Încearcă să obțină context din diferite surse
            context = wish_data.get("context") or wish_data.get("full_context")
            if not context and wish_data.get("trigger_analysis"):
                trigger = wish_data.get("trigger_analysis", {})
                if isinstance(trigger, dict):
                    trigger_text = trigger.get("trigger", {}).get("text", "") if isinstance(trigger.get("trigger"), dict) else ""
                    if trigger_text:
                        context = {"text": trigger_text}
        
        # Verifică dacă e produs fizic (folosește context)
        if not self.is_physical_product(intent, language, context):
            return products
        
        # Extrage nume produs (folosește context)
        product_name = self.extract_product_name(intent, language, context)
        if not product_name:
            # Încearcă din context dacă nu găsește în intent
            if context:
                context_text = context.get("post_text", "") or context.get("text", "") or ""
                if context_text:
                    product_name = self.extract_product_name(context_text, language, None)
        
        if not product_name:
            return products
        
        # Extrage categorie
        category = self.extract_category(intent, language)
        
        # Calculează confidence bazat pe cât de clar e produsul
        confidence = 0.6  # Default
        if any(pattern in intent.lower() for pattern in ["nu se găsește", "lipsește", "not available", "missing"]):
            confidence = 0.9  # Foarte clar că e despre un produs lipsă
        elif any(kw in intent.lower() for kw in self.product_keywords.get(language, [])):
            confidence = 0.8  # Are keywords clare
        elif any(brand in intent.lower() for brand in self.brand_keywords.get(language, [])):
            confidence = 0.7  # Are brand-uri
        
        # Îmbogățește informațiile despre produs
        enriched = self.product_enricher.enrich_product(
            product_name=product_name,
            wish_data=wish_data,
            language=language
        )
        
        products.append({
            "product_name": product_name,
            "category": category,
            "source_wish_id": wish_data.get("id"),
            "source_wish_intent": intent,
            "language": language,
            "confidence": confidence,
            # Informații îmbogățite
            **enriched
        })
        
        return products
