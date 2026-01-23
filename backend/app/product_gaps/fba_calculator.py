"""
FBA Calculator - Calculează profitabilitatea FBA
"""

from typing import Dict, Any


class FBACalculator:
    """Calculator pentru profitabilitate FBA"""
    
    # Costuri fixe estimate (lei)
    IMPORT_TAX_RATE = 0.19  # TVA 19%
    CUSTOMS_DUTY_RATE = 0.05  # 5% (variază după produs)
    SHIPPING_COST_PER_KG = 50  # lei/kg (estimare)
    FBA_STORAGE_COST = 0.5  # lei/unitate/lună (estimare)
    FBA_FULFILLMENT_COST = 10  # lei/unitate (estimare)
    
    def calculate_profitability(
        self,
        amazon_price: float,
        import_costs: float,
        fba_costs: float,
        selling_price: float,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Calculează profitabilitatea FBA
        
        Args:
            amazon_price: Preț Amazon (lei)
            import_costs: Costuri import (lei)
            fba_costs: Costuri FBA (lei)
            selling_price: Preț vânzare estimat (lei)
            quantity: Cantitate
            
        Returns:
            Analiză FBA completă
        """
        # Calculate costs
        total_amazon_cost = amazon_price * quantity
        total_import_costs = import_costs * quantity if import_costs > 0 else self._estimate_import_costs(amazon_price, quantity)
        total_fba_costs = fba_costs * quantity if fba_costs > 0 else self._estimate_fba_costs(quantity)
        
        total_cost = total_amazon_cost + total_import_costs + total_fba_costs
        
        # Calculate revenue
        total_revenue = selling_price * quantity
        
        # Calculate profit
        profit_brut = total_revenue - total_cost
        profit_net = profit_brut * 0.85  # Assume 15% taxe/overhead
        profit_per_unit = profit_net / quantity if quantity > 0 else 0
        
        # Calculate ROI
        roi = (profit_net / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate break-even
        break_even_units = int(total_cost / selling_price) if selling_price > 0 else 0
        
        # Determine risk level
        risk_level = self._calculate_risk_level(profit_margin=(profit_net / total_revenue * 100) if total_revenue > 0 else 0, roi=roi)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(profit_per_unit, roi, risk_level)
        
        return {
            "profit_brut": round(profit_brut, 2),
            "profit_net": round(profit_net, 2),
            "profit_per_unit": round(profit_per_unit, 2),
            "roi": round(roi, 2),
            "break_even_units": break_even_units,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "cost_breakdown": {
                "amazon_cost": round(total_amazon_cost, 2),
                "import_costs": round(total_import_costs, 2),
                "fba_costs": round(total_fba_costs, 2),
                "total_cost": round(total_cost, 2)
            },
            "revenue": round(total_revenue, 2)
        }
    
    def _estimate_import_costs(self, amazon_price: float, quantity: int) -> float:
        """Estimează costurile de import"""
        # TVA
        tva = amazon_price * quantity * self.IMPORT_TAX_RATE
        
        # Customs duty
        customs = amazon_price * quantity * self.CUSTOMS_DUTY_RATE
        
        # Shipping (estimate 1kg per unit)
        shipping = self.SHIPPING_COST_PER_KG * quantity
        
        return tva + customs + shipping
    
    def _estimate_fba_costs(self, quantity: int) -> float:
        """Estimează costurile FBA"""
        # Storage (1 month)
        storage = self.FBA_STORAGE_COST * quantity
        
        # Fulfillment
        fulfillment = self.FBA_FULFILLMENT_COST * quantity
        
        return storage + fulfillment
    
    def _calculate_risk_level(self, profit_margin: float, roi: float) -> str:
        """Calculează nivelul de risc"""
        if profit_margin > 40 and roi > 50:
            return "low"
        elif profit_margin > 20 and roi > 25:
            return "medium"
        else:
            return "high"
    
    def _generate_recommendation(self, profit_per_unit: float, roi: float, risk_level: str) -> str:
        """Generează recomandare"""
        if risk_level == "low" and profit_per_unit > 50:
            return "Recomandat - Profit mare, risc mic. Poți testa cu 10-20 unități."
        elif risk_level == "medium" and profit_per_unit > 30:
            return "Moderat - Profit decent, risc mediu. Testează cu 5-10 unități."
        elif risk_level == "low":
            return "Acceptabil - Risc mic dar profit moderat. Poți testa cu 3-5 unități."
        else:
            return "Riscat - Profit mic sau risc mare. Nu recomandat fără analiză suplimentară."
