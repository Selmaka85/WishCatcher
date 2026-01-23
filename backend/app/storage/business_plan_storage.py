"""
Business Plan Storage - Stocare persistentă pentru business plan-uri
Cu suport pentru MD, JSON, PDF și versioning
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import markdown
from app.api.models import BusinessPlanResponse


class BusinessPlanStorage:
    """Stocare business plan-uri în multiple formate (JSON, MD, PDF)"""
    
    def __init__(self, base_dir: str = "data/business_plans"):
        """
        Inițializează storage
        
        Args:
            base_dir: Directorul de bază pentru business plan-uri
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Fișier principal pentru toate business plan-urile
        self.main_file = self.base_dir / "business_plans.json"
        
        # Folder pentru business plan-uri individuale
        self.individual_dir = self.base_dir / "individual"
        self.individual_dir.mkdir(parents=True, exist_ok=True)
        
        # Folder pentru exports
        self.exports_dir = self.base_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache pentru business plan-uri
        self.plans_cache: Dict[str, Dict] = self._load_all_plans()
    
    def _load_all_plans(self) -> Dict[str, Dict]:
        """Încarcă toate business plan-urile din fișierul principal"""
        if not self.main_file.exists():
            return {}
        
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['id']: item for item in data}
        except Exception as e:
            print(f"[Storage] Eroare la încărcare business plans: {e}")
            return {}
    
    def _save_all_plans(self):
        """Salvează toate business plan-urile în fișierul principal"""
        with open(self.main_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.plans_cache.values()), f, indent=2, ensure_ascii=False, default=str)
    
    def save_business_plan(self, business_plan: BusinessPlanResponse) -> str:
        """
        Salvează business plan în multiple formate
        
        Args:
            business_plan: Business plan de salvat
        
        Returns:
            ID-ul business plan-ului salvat
        """
        plan_id = business_plan.id
        
        # Convert to dict
        plan_dict = business_plan.model_dump()
        
        # Add version info
        if plan_id in self.plans_cache:
            # Versioning: increment version
            existing_versions = self.plans_cache[plan_id].get('versions', [])
            version = len(existing_versions) + 1
        else:
            version = 1
            existing_versions = []
        
        plan_dict['version'] = version
        plan_dict['versions'] = existing_versions + [{
            'version': version,
            'generated_at': plan_dict['generated_at'],
            'timestamp': datetime.now().isoformat()
        }]
        
        # Update cache
        self.plans_cache[plan_id] = plan_dict
        
        # Save JSON
        self._save_json(plan_id, plan_dict)
        
        # Save Markdown
        self._save_markdown(plan_id, plan_dict)
        
        # Save PDF (markdown to PDF conversion - simplified)
        self._save_pdf(plan_id, plan_dict)
        
        # Save to main file
        self._save_all_plans()
        
        print(f"[Storage] Business plan {plan_id} salvat (v{version})")
        return plan_id
    
    def _save_json(self, plan_id: str, plan_dict: Dict):
        """Salvează business plan în format JSON"""
        json_file = self.individual_dir / f"{plan_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_markdown(self, plan_id: str, plan_dict: Dict):
        """Salvează business plan în format Markdown"""
        md_file = self.individual_dir / f"{plan_id}.md"
        
        md_content = self._generate_markdown(plan_dict)
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _generate_markdown(self, plan_dict: Dict) -> str:
        """Generează conținut Markdown din business plan"""
        md = []
        
        # Header
        md.append("# Business Plan")
        md.append("")
        md.append(f"**ID:** {plan_dict.get('id', 'N/A')}")
        md.append(f"**Wish ID:** {plan_dict.get('wish_id', 'N/A')}")
        md.append(f"**Generated:** {plan_dict.get('generated_at', 'N/A')}")
        md.append(f"**Version:** {plan_dict.get('version', 1)}")
        md.append("")
        md.append("---")
        md.append("")
        
        # Executive Summary
        exec_summary = plan_dict.get('executive_summary', {})
        md.append("## Executive Summary")
        md.append("")
        md.append(f"**Idea:** {exec_summary.get('idea', 'N/A')}")
        md.append("")
        md.append(f"**Value Proposition:** {exec_summary.get('value_proposition', 'N/A')}")
        md.append("")
        md.append(f"**Market Opportunity:** {exec_summary.get('market_opportunity', 'N/A')}")
        md.append("")
        md.append(f"**Target Audience:** {exec_summary.get('target_audience', 'N/A')}")
        md.append("")
        md.append(f"**Revenue Model:** {exec_summary.get('revenue_model', 'N/A')}")
        md.append("")
        
        # Market Analysis
        market = plan_dict.get('market_analysis', {})
        md.append("## Market Analysis")
        md.append("")
        md.append(f"**Market Size:** {market.get('market_size', 'N/A')}")
        md.append("")
        md.append(f"**Target Demographic:** {market.get('target_demographic', 'N/A')}")
        md.append("")
        md.append(f"**Geographic Scope:** {market.get('geographic_scope', 'N/A')}")
        md.append("")
        md.append(f"**Competition Level:** {market.get('competition_level', 'N/A')}")
        md.append("")
        
        # Product Description
        product = plan_dict.get('product_description', {})
        md.append("## Product Description")
        md.append("")
        md.append(f"**Product Name:** {product.get('product_name', 'N/A')}")
        md.append("")
        md.append(f"**Description:** {product.get('description', 'N/A')}")
        md.append("")
        md.append("**Key Features:**")
        for feature in product.get('key_features', []):
            md.append(f"- {feature}")
        md.append("")
        
        # Business Model
        business_model = plan_dict.get('business_model', {})
        md.append("## Business Model")
        md.append("")
        md.append(f"**Revenue Model:** {business_model.get('revenue_model', 'N/A')}")
        md.append("")
        md.append(f"**Pricing Strategy:** {business_model.get('pricing_strategy', 'N/A')}")
        md.append("")
        md.append(f"**Estimated Price:** {business_model.get('estimated_price', 'N/A')}")
        md.append("")
        
        # Go-to-Market
        gtm = plan_dict.get('go_to_market', {})
        md.append("## Go-to-Market Strategy")
        md.append("")
        md.append("**Channels:**")
        for channel in gtm.get('channels', []):
            md.append(f"- {channel}")
        md.append("")
        md.append("**Marketing Strategy:**")
        md.append(gtm.get('marketing_strategy', 'N/A'))
        md.append("")
        
        # Financial Projections
        financial = plan_dict.get('financial_projections', {})
        md.append("## Financial Projections")
        md.append("")
        for year, data in financial.items():
            if isinstance(data, dict):
                md.append(f"### {year.replace('_', ' ').title()}")
                md.append("")
                for key, value in data.items():
                    md.append(f"- **{key.replace('_', ' ').title()}:** {value}")
                md.append("")
        
        # Implementation Plan
        implementation = plan_dict.get('implementation_plan', {})
        md.append("## Implementation Plan")
        md.append("")
        md.append(f"**Timeline:** {implementation.get('timeline', 'N/A')}")
        md.append("")
        md.append("**Phases:**")
        for phase in implementation.get('phases', []):
            md.append(f"- **{phase.get('phase', 'N/A')}:** {phase.get('duration', 'N/A')}")
        md.append("")
        md.append("**Resources Needed:**")
        resources = implementation.get('resources_needed', {})
        for key, value in resources.items():
            md.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        md.append("")
        
        return "\n".join(md)
    
    def _save_pdf(self, plan_id: str, plan_dict: Dict):
        """
        Salvează business plan în format PDF
        Notă: Pentru conversie reală PDF, ar trebui folosit markdown-pdf sau weasyprint
        Pentru acum, salvăm un placeholder
        """
        # Read markdown
        md_file = self.individual_dir / f"{plan_id}.md"
        if md_file.exists():
            # For now, just note that PDF should be generated
            # In production, use: markdown-pdf, weasyprint, or reportlab
            pdf_note_file = self.individual_dir / f"{plan_id}_pdf_note.txt"
            with open(pdf_note_file, 'w', encoding='utf-8') as f:
                f.write(f"PDF export pentru {plan_id}\n")
                f.write("Pentru generare PDF reală, folosește: markdown-pdf sau weasyprint\n")
                f.write(f"Markdown source: {md_file}\n")
    
    def get_business_plan(self, plan_id: str, version: Optional[int] = None) -> Optional[Dict]:
        """
        Obține business plan după ID și versiune
        
        Args:
            plan_id: ID-ul business plan-ului
            version: Versiunea specifică (None = latest)
        
        Returns:
            Business plan sau None
        """
        if plan_id not in self.plans_cache:
            return None
        
        plan = self.plans_cache[plan_id].copy()
        
        if version:
            # Return specific version (if available)
            versions = plan.get('versions', [])
            version_data = next((v for v in versions if v['version'] == version), None)
            if version_data:
                plan['version'] = version
                plan['generated_at'] = version_data['generated_at']
        
        return plan
    
    def list_business_plans(
        self,
        limit: int = 100,
        offset: int = 0,
        wish_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Listează business plan-uri
        
        Args:
            limit: Număr maxim de planuri
            offset: Offset pentru paginare
            wish_id: Filtrare după wish_id
        
        Returns:
            Lista de business plan-uri
        """
        plans = list(self.plans_cache.values())
        
        if wish_id:
            plans = [p for p in plans if p.get('wish_id') == wish_id]
        
        # Sort by generated_at descending
        plans.sort(key=lambda p: p.get('generated_at', ''), reverse=True)
        
        return plans[offset:offset + limit]
    
    def export_business_plan(self, plan_id: str, format: str = "all") -> Dict[str, Path]:
        """
        Exportă business plan în format specificat
        
        Args:
            plan_id: ID-ul business plan-ului
            format: Format de export ("json", "md", "pdf", "all")
        
        Returns:
            Dict cu path-urile fișierelor exportate
        """
        if plan_id not in self.plans_cache:
            raise ValueError(f"Business plan {plan_id} not found")
        
        exported_files = {}
        
        if format in ["json", "all"]:
            json_file = self.individual_dir / f"{plan_id}.json"
            if json_file.exists():
                exported_files['json'] = json_file
        
        if format in ["md", "all"]:
            md_file = self.individual_dir / f"{plan_id}.md"
            if md_file.exists():
                exported_files['markdown'] = md_file
        
        if format in ["pdf", "all"]:
            # PDF would be generated here
            md_file = self.individual_dir / f"{plan_id}.md"
            if md_file.exists():
                exported_files['pdf_note'] = self.individual_dir / f"{plan_id}_pdf_note.txt"
        
        return exported_files
    
    def get_stats(self) -> Dict[str, Any]:
        """Returnează statistici despre business plan-uri"""
        total_plans = len(self.plans_cache)
        
        total_versions = sum(
            len(p.get('versions', [])) for p in self.plans_cache.values()
        )
        
        wish_ids = set(p.get('wish_id') for p in self.plans_cache.values())
        
        return {
            "total_business_plans": total_plans,
            "total_versions": total_versions,
            "unique_wishes": len(wish_ids),
            "average_versions_per_plan": total_versions / total_plans if total_plans > 0 else 0
        }
