"""
Gap Detector - Identifică automat gap-uri între marketplace-uri (ambele direcții)
"""

from typing import List, Dict, Any, Optional


class GapDetector:
    """Detectează gap-uri între marketplace-uri"""
    
    def __init__(self):
        # Threshold pentru "expensive" (20% mai scump)
        self.price_difference_threshold = 0.20
    
    def detect_gaps(self, marketplace_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detectează gap-uri din rezultatele marketplace-urilor
        
        Args:
            marketplace_results: Rezultate de pe toate marketplace-urile
            
        Returns:
            Lista de gap-uri identificate
        """
        gaps = []
        product_name = marketplace_results.get("product_name", "")
        
        # Extract status și prețuri
        emag = marketplace_results.get("emag", {})
        amazon_uk = marketplace_results.get("amazon_uk", {})
        altex = marketplace_results.get("altex", {})
        pcgarage = marketplace_results.get("pcgarage", {})
        
        # Gap-uri eMAG → Amazon UK (import FBA)
        if emag.get("status") == "missing" and amazon_uk.get("status") == "available":
            gaps.append({
                "from_marketplace": "emag",
                "to_marketplace": "amazon_uk",
                "type": "missing",
                "product_name": product_name,
                "from_price": None,
                "to_price": amazon_uk.get("price"),
                "to_url": amazon_uk.get("url"),
                "profit_margin": self._estimate_profit_margin(None, amazon_uk.get("price"), "import"),
                "opportunity_type": "fba_import",
                "risk_level": "medium"
            })
        
        # Gap-uri Amazon UK → eMAG (export)
        if amazon_uk.get("status") == "missing" and emag.get("status") == "available":
            gaps.append({
                "from_marketplace": "amazon_uk",
                "to_marketplace": "emag",
                "type": "missing",
                "product_name": product_name,
                "from_price": None,
                "to_price": emag.get("price"),
                "to_url": emag.get("url"),
                "profit_margin": self._estimate_profit_margin(None, emag.get("price"), "export"),
                "opportunity_type": "export",
                "risk_level": "medium"
            })
        
        # Gap-uri eMAG → Altex (dropshipping/import)
        if emag.get("status") == "missing" and altex.get("status") == "available":
            gaps.append({
                "from_marketplace": "emag",
                "to_marketplace": "altex",
                "type": "missing",
                "product_name": product_name,
                "from_price": None,
                "to_price": altex.get("price"),
                "to_url": altex.get("url"),
                "profit_margin": self._estimate_profit_margin(None, altex.get("price"), "dropshipping"),
                "opportunity_type": "dropshipping",
                "risk_level": "low"
            })
        
        # Gap-uri eMAG → PCGarage (dropshipping/import)
        if emag.get("status") == "missing" and pcgarage.get("status") == "available":
            gaps.append({
                "from_marketplace": "emag",
                "to_marketplace": "pcgarage",
                "type": "missing",
                "product_name": product_name,
                "from_price": None,
                "to_price": pcgarage.get("price"),
                "to_url": pcgarage.get("url"),
                "profit_margin": self._estimate_profit_margin(None, pcgarage.get("price"), "dropshipping"),
                "opportunity_type": "dropshipping",
                "risk_level": "low"
            })
        
        # Gap-uri "expensive" (preț mare pe un marketplace, mic pe altul)
        # eMAG expensive vs Amazon UK
        if (emag.get("status") == "available" and amazon_uk.get("status") == "available" and
            emag.get("price") and amazon_uk.get("price")):
            amazon_price_lei = amazon_uk.get("price") * 5.5  # Convert £ to lei
            price_diff = (emag.get("price") - amazon_price_lei) / emag.get("price")
            
            if price_diff > self.price_difference_threshold:  # eMAG e mai scump cu >20%
                gaps.append({
                    "from_marketplace": "emag",
                    "to_marketplace": "amazon_uk",
                    "type": "expensive",
                    "product_name": product_name,
                    "from_price": emag.get("price"),
                    "to_price": amazon_uk.get("price"),
                    "from_url": emag.get("url"),
                    "to_url": amazon_uk.get("url"),
                    "profit_margin": price_diff * 100,
                    "opportunity_type": "fba_import",
                    "risk_level": "low" if price_diff > 0.3 else "medium"
                })
        
        # Amazon UK expensive vs eMAG
        if (amazon_uk.get("status") == "available" and emag.get("status") == "available" and
            amazon_uk.get("price") and emag.get("price")):
            amazon_price_lei = amazon_uk.get("price") * 5.5
            price_diff = (amazon_price_lei - emag.get("price")) / amazon_price_lei
            
            if price_diff > self.price_difference_threshold:  # Amazon e mai scump cu >20%
                gaps.append({
                    "from_marketplace": "amazon_uk",
                    "to_marketplace": "emag",
                    "type": "expensive",
                    "product_name": product_name,
                    "from_price": amazon_uk.get("price"),
                    "to_price": emag.get("price"),
                    "from_url": amazon_uk.get("url"),
                    "to_url": emag.get("url"),
                    "profit_margin": price_diff * 100,
                    "opportunity_type": "export",
                    "risk_level": "low" if price_diff > 0.3 else "medium"
                })
        
        # Gap-uri multi-marketplace (lipsește pe multiple românești, există pe Amazon)
        romanian_missing = sum(1 for m in [emag, altex, pcgarage] if m.get("status") == "missing")
        if romanian_missing >= 2 and amazon_uk.get("status") == "available":
            gaps.append({
                "from_marketplace": "romanian_marketplaces",
                "to_marketplace": "amazon_uk",
                "type": "missing_multi",
                "product_name": product_name,
                "from_price": None,
                "to_price": amazon_uk.get("price"),
                "to_url": amazon_uk.get("url"),
                "profit_margin": self._estimate_profit_margin(None, amazon_uk.get("price"), "import"),
                "opportunity_type": "fba_import",
                "risk_level": "low",  # Mai puțin riscant dacă lipsește pe multiple
                "missing_on": [m for m in ["emag", "altex", "pcgarage"] 
                              if marketplace_results.get(m, {}).get("status") == "missing"]
            })
        
        return gaps
    
    def _estimate_profit_margin(
        self,
        from_price: Optional[float],
        to_price: Optional[float],
        opportunity_type: str
    ) -> float:
        """
        Estimează marja profit
        
        Args:
            from_price: Preț pe marketplace-ul sursă
            to_price: Preț pe marketplace-ul destinație
            opportunity_type: Tip oportunitate (import, export, dropshipping)
            
        Returns:
            Marja profit estimată (%)
        """
        if not to_price:
            return 0.0
        
        # Estimări bazate pe tipul oportunității
        if opportunity_type == "fba_import":
            # Import FBA: costuri ~30-40% (taxe, transport, FBA)
            # Profit estimat: 30-50%
            return 35.0
        elif opportunity_type == "export":
            # Export: costuri ~20-30% (transport, taxe)
            # Profit estimat: 25-40%
            return 30.0
        elif opportunity_type == "dropshipping":
            # Dropshipping: costuri ~15-25%
            # Profit estimat: 20-35%
            return 25.0
        
        return 0.0
