"""
Astra Genesis - Business Plan Generator
Generează planuri de afaceri complete din intenții detectate
CU TRIGGER INTEGRATION
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class BusinessMetrics:
    """Metrici business pentru o idee"""
    market_size: str
    target_demographic: str
    geographic_scope: str
    competition_level: str
    monetization_model: str
    estimated_price: str
    potential_revenue: str
    tech_complexity: str
    cost_estimate: str
    time_estimate: str


class BusinessPlanGenerator:
    """Generator de planuri de afaceri cu trigger integration"""
    
    def __init__(self):
        self.revenue_models = {
            "software": ["subscription", "freemium", "one-time", "usage-based"],
            "service": ["hourly", "project-based", "retainer"],
            "product": ["direct-sale", "marketplace", "wholesale"]
        }
    
    def generate(self, wish_data: Dict) -> Dict:
        """
        Generează business plan complet CU TRIGGER INTEGRATION
        
        Args:
            wish_data: Date din WishCatcher (cu trigger_analysis)
        
        Returns:
            Business plan complet
        """
        metrics = self._calculate_metrics(wish_data)
        trigger_analysis = wish_data.get("trigger_analysis", {})
        
        return {
            "executive_summary": self._generate_executive_summary(wish_data, metrics, trigger_analysis),
            "market_analysis": self._generate_market_analysis(wish_data, metrics, trigger_analysis),
            "product_description": self._generate_product_description(wish_data, trigger_analysis),
            "business_model": self._generate_business_model(wish_data, metrics, trigger_analysis),
            "go_to_market": self._generate_go_to_market(wish_data, metrics, trigger_analysis),
            "financial_projections": self._generate_financial_projections(metrics, trigger_analysis),
            "implementation_plan": self._generate_implementation_plan(wish_data, metrics)
        }
    
    def _calculate_metrics(self, wish_data: Dict) -> BusinessMetrics:
        """Calculează metrici business"""
        market = wish_data.get("market_analysis", {})
        monetization = wish_data.get("monetization", {})
        feasibility = wish_data.get("feasibility", {})
        
        return BusinessMetrics(
            market_size=market.get("market_size", "medium"),
            target_demographic=market.get("target_demographic", "general"),
            geographic_scope=market.get("geographic_scope", "regional"),
            competition_level=market.get("competition", "medium"),
            monetization_model=monetization.get("model", "subscription"),
            estimated_price=monetization.get("estimated_price", "€10-20/mo"),
            potential_revenue=monetization.get("potential_revenue", "€50K-200K/an"),
            tech_complexity=feasibility.get("tech", "medium"),
            cost_estimate=feasibility.get("cost", "€5K-15K"),
            time_estimate=feasibility.get("time", "2-3 months")
        )
    
    def _generate_executive_summary(
        self,
        wish_data: Dict,
        metrics: BusinessMetrics,
        trigger_analysis: Dict
    ) -> Dict:
        """Generează executive summary CU TRIGGER și STRUCTURAT"""
        # Folosește intent_full dacă există, altfel intent
        intent_short = wish_data.get("intent", "")
        intent_full = wish_data.get("intent_full", intent_short)
        structured = wish_data.get("structured", {})
        
        # Value proposition din structured sau trigger
        if structured:
            value_proposition = self._generate_value_proposition_from_structured(structured, trigger_analysis)
        else:
            value_proposition = self._generate_value_proposition_from_trigger(
                intent_short, trigger_analysis
            )
        
        return {
            "idea": intent_short,  # Short pentru titlu
            "idea_full": intent_full,  # Full pentru descriere
            "value_proposition": value_proposition,
            "market_opportunity": f"Market {metrics.market_size} în {metrics.geographic_scope}",
            "target_audience": structured.get("who", metrics.target_demographic) if structured else metrics.target_demographic,
            "revenue_model": metrics.monetization_model,
            "key_metrics": {
                "estimated_price": metrics.estimated_price,
                "potential_revenue": metrics.potential_revenue,
                "time_to_market": metrics.time_estimate,
                "initial_investment": metrics.cost_estimate
            },
            "trigger": trigger_analysis.get("trigger", {}).get("text")
        }
    
    def _generate_value_proposition_from_structured(
        self,
        structured: Dict,
        trigger_analysis: Dict
    ) -> str:
        """Generează value proposition din structured data"""
        problem = structured.get("problem", "")
        what = structured.get("what", "")
        
        if problem and problem != "Problema identificată din context":
            return f"Rezolvă problema: {problem}"
        
        # Dacă avem pain points din trigger
        pain_points = trigger_analysis.get("pain_points", [])
        if pain_points:
            if isinstance(pain_points, list) and len(pain_points) > 0:
                if isinstance(pain_points[0], dict):
                    high_severity = [pp for pp in pain_points if pp.get("severity") == "high"]
                    if high_severity:
                        pain = high_severity[0].get("text", "")
                        return f"Elimină: {pain}"
                else:
                    return f"Rezolvă: {pain_points[0]}"
        
        # Fallback din structured
        if what:
            return f"Soluție pentru {what.lower()}"
        
        return "Soluție pentru nevoile identificate"
    
    def _generate_value_proposition_from_trigger(
        self,
        intent: str,
        trigger_analysis: Dict
    ) -> str:
        """Generează value proposition din trigger analysis (fallback)"""
        # Dacă avem trigger specific
        trigger = trigger_analysis.get("trigger", {})
        if trigger.get("text"):
            return f"Rezolvă problema: {trigger['text']}"
        
        # Dacă avem pain points
        pain_points = trigger_analysis.get("pain_points", [])
        if pain_points:
            if isinstance(pain_points, list) and len(pain_points) > 0:
                if isinstance(pain_points[0], dict):
                    high_severity = [pp for pp in pain_points if pp.get("severity") == "high"]
                    if high_severity:
                        pain = high_severity[0].get("text", "")
                        return f"Elimină: {pain}"
                else:
                    return f"Rezolvă: {pain_points[0]}"
        
        # Fallback generic
        return f"Soluție pentru {intent.lower()}"
    
    def _generate_market_analysis(
        self,
        wish_data: Dict,
        metrics: BusinessMetrics,
        trigger_analysis: Dict
    ) -> Dict:
        """Generează analiză de piață CU PAIN POINTS"""
        pain_points = trigger_analysis.get("pain_points", [])
        
        return {
            "target_market": {
                "size": metrics.market_size,
                "demographic": metrics.target_demographic,
                "geographic": metrics.geographic_scope
            },
            "market_size_estimate": self._estimate_market_size(metrics),
            "competition_analysis": {
                "level": metrics.competition_level,
                "differentiation": "Focus pe simplitate și UX"
            },
            "customer_pain_points": [
                {
                    "type": pp.get("type"),
                    "description": pp.get("text"),
                    "severity": pp.get("severity")
                }
                for pp in pain_points[:5]  # Top 5
            ],
            "emotional_triggers": trigger_analysis.get("frustration", {}).get("expressions", [])
        }
    
    def _generate_product_description(
        self,
        wish_data: Dict,
        trigger_analysis: Dict
    ) -> Dict:
        """Generează descriere produs CU FEATURES PRIORITIZATE și STRUCTURAT"""
        intent_short = wish_data.get("intent", "")
        intent_full = wish_data.get("intent_full", intent_short)
        structured = wish_data.get("structured", {})
        
        # Folosește features din structured dacă există
        if structured:
            key_features = structured.get("key_features", [])
            if not key_features:
                # Fallback la pain points
                pain_points = trigger_analysis.get("pain_points", [])
                key_features = self._prioritize_features_from_pain_points(pain_points)
        else:
            pain_points = trigger_analysis.get("pain_points", [])
            key_features = self._prioritize_features_from_pain_points(pain_points)
        
        # Value proposition din structured
        if structured:
            value_proposition = self._generate_value_proposition_from_structured(structured, trigger_analysis)
        else:
            value_proposition = self._generate_value_proposition_from_trigger(intent_short, trigger_analysis)
        
        return {
            "name": self._suggest_product_name(intent_short),
            "description": intent_full,  # Folosește intent_full pentru descriere completă
            "description_short": intent_short,  # Short pentru titlu
            "key_features": key_features,
            "value_proposition": value_proposition,
            "target_users": structured.get("who", "General public") if structured else "General public",
            "use_case": structured.get("use_case", "") if structured else "",
            "problem_solved": structured.get("problem", "") if structured else "",
            "solution_approach": structured.get("how", "") if structured else "",
            "technology_stack": wish_data.get("technologies", [])
        }
    
    def _prioritize_features_from_pain_points(self, pain_points: List[Dict]) -> List[str]:
        """Prioritizează features din pain points"""
        feature_mapping = {
            "time": ["automation", "quick_setup", "one_click"],
            "cost": ["free_tier", "affordable", "transparent_pricing"],
            "risk": ["security", "backup", "verification", "transparency"],
            "effort": ["simple_ui", "wizard", "templates"]
        }
        
        features = []
        for pp in pain_points:
            pp_type = pp.get("type", "effort")
            severity = pp.get("severity", "low")
            
            if severity in ["high", "medium"]:
                features.extend(feature_mapping.get(pp_type, []))
        
        # Remove duplicates, keep order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)
        
        return unique_features[:10]  # Top 10
    
    def _generate_business_model(
        self,
        wish_data: Dict,
        metrics: BusinessMetrics,
        trigger_analysis: Dict
    ) -> Dict:
        """Generează model de business CU PRICING DIN TRIGGER"""
        # Pricing din emotional intensity
        emotional_intensity = trigger_analysis.get("emotional_intensity", 0.5)
        
        # Adjust price based on urgency
        base_price = metrics.estimated_price
        if emotional_intensity > 0.7:
            # Premium pricing pentru urgență mare
            price_multiplier = 1.5
        else:
            price_multiplier = 1.0
        
        return {
            "revenue_streams": [{
                "type": metrics.monetization_model,
                "description": "Abonament lunar/anual",
                "pricing": base_price,
                "target_customers": metrics.target_demographic
            }],
            "pricing_strategy": {
                "model": metrics.monetization_model,
                "price_range": base_price,
                "rationale": f"Urgență {'mare' if emotional_intensity > 0.7 else 'medie'} + {len(trigger_analysis.get('pain_points', []))} pain points"
            },
            "cost_structure": {
                "development": metrics.cost_estimate,
                "operational": "€500-2000/mo",
                "marketing": "€1000-5000/mo"
            },
            "unit_economics": {
                "cac": "€20-50",
                "ltv": "€200-500",
                "ltv_cac_ratio": "4-10x"
            }
        }
    
    def _generate_go_to_market(
        self,
        wish_data: Dict,
        metrics: BusinessMetrics,
        trigger_analysis: Dict
    ) -> Dict:
        """Generează strategie go-to-market CU MESSAGING DIN TRIGGER"""
        frustration = trigger_analysis.get("frustration", {})
        frustration_exprs = frustration.get("expressions", [])
        
        # Marketing messages din frustration
        messages = []
        if frustration_exprs:
            messages.append(f"Elimină: {frustration_exprs[0]}")
        
        pain_points = trigger_analysis.get("pain_points", [])
        if pain_points:
            high_severity = [pp for pp in pain_points if pp.get("severity") == "high"]
            if high_severity:
                messages.append(f"Rezolvă: {high_severity[0].get('text', '')}")
        
        return {
            "marketing_channels": ["Social Media", "Content Marketing", "SEO", "Paid Ads"],
            "sales_strategy": "Self-service cu suport opțional",
            "marketing_messages": messages if messages else ["Soluție pentru " + wish_data["intent"]],
            "customer_acquisition": {
                "channels": ["social_media", "content_marketing", "partnerships"],
                "cost_per_acquisition": "€20-50",
                "lifetime_value": "€200-500"
            },
            "launch_plan": {
                "phase_1": "MVP launch",
                "phase_2": "Beta testing",
                "phase_3": "Public launch"
            }
        }
    
    def _generate_financial_projections(
        self,
        metrics: BusinessMetrics,
        trigger_analysis: Dict
    ) -> Dict:
        """Generează proiecții financiare"""
        return {
            "year_1": {
                "revenue": metrics.potential_revenue,
                "costs": "€20K-50K",
                "break_even": "6-12 months"
            },
            "year_2": {
                "revenue": "€100K-400K",
                "growth": "50-100%"
            },
            "year_3": {
                "revenue": "€200K-800K",
                "growth": "30-50%"
            },
            "roi_estimate": "200-500% în 3 ani"
        }
    
    def _generate_implementation_plan(
        self,
        wish_data: Dict,
        metrics: BusinessMetrics
    ) -> Dict:
        """Generează plan de implementare"""
        domain = wish_data.get("domain", "software")
        
        plan = {
            "timeline": metrics.time_estimate,
            "phases": [
                {"phase": "Research & Planning", "duration": "2-4 weeks"},
                {"phase": "Development", "duration": metrics.time_estimate},
                {"phase": "Testing & Launch", "duration": "2-4 weeks"}
            ],
            "resources_needed": {
                "team_size": "1-3 people",
                "skills": ["Development", "Design", "Marketing"],
                "budget": metrics.cost_estimate
            },
            "cost_breakdown": {
                "development": metrics.cost_estimate,
                "operational": "€500-2000/mo",
                "marketing": "€1000-5000/mo"
            },
            "milestones": [
                "MVP complet",
                "Beta launch",
                "100 users",
                "Break-even"
            ]
        }
        
        if domain == "software":
            plan["mvp_structure"] = {
                "type": "software",
                "components": wish_data.get("technologies", []),
                "generation_ready": True
            }
        
        return plan
    
    # Helper methods
    def _suggest_product_name(self, intent: str) -> str:
        """Sugerează nume produs"""
        words = intent.split()[:3]
        return "".join(word.capitalize() for word in words)
    
    def _estimate_market_size(self, metrics: BusinessMetrics) -> str:
        """Estimează mărimea pieței"""
        size_map = {
            "small": "€100K-500K",
            "medium": "€500K-2M",
            "large": "€2M-10M+"
        }
        return size_map.get(metrics.market_size, "€500K-2M")
