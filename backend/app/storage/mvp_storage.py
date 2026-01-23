"""
MVP Storage - Stocare persistentă pentru MVP-uri generate
Cu suport pentru ZIP archives și structură completă
"""

import json
import os
import zipfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.api.models import MVPResponse


class MVPStorage:
    """Stocare MVP-uri cu structură completă și boilerplate code"""
    
    def __init__(self, base_dir: str = "data/mvps"):
        """
        Inițializează storage
        
        Args:
            base_dir: Directorul de bază pentru MVP-uri
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Fișier principal pentru toate MVP-urile
        self.main_file = self.base_dir / "mvps.json"
        
        # Folder pentru MVP-uri individuale
        self.individual_dir = self.base_dir / "individual"
        self.individual_dir.mkdir(parents=True, exist_ok=True)
        
        # Folder pentru exports
        self.exports_dir = self.base_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache pentru MVP-uri
        self.mvps_cache: Dict[str, Dict] = self._load_all_mvps()
    
    def _load_all_mvps(self) -> Dict[str, Dict]:
        """Încarcă toate MVP-urile din fișierul principal"""
        if not self.main_file.exists():
            return {}
        
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['id']: item for item in data}
        except Exception as e:
            print(f"[Storage] Eroare la încărcare MVPs: {e}")
            return {}
    
    def _save_all_mvps(self):
        """Salvează toate MVP-urile în fișierul principal"""
        with open(self.main_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.mvps_cache.values()), f, indent=2, ensure_ascii=False, default=str)
    
    def save_mvp(self, mvp: MVPResponse) -> str:
        """
        Salvează MVP cu structură completă și ZIP archive
        
        Args:
            mvp: MVP de salvat
        
        Returns:
            ID-ul MVP-ului salvat
        """
        mvp_id = mvp.id
        
        # Convert to dict
        mvp_dict = mvp.model_dump()
        
        # Update cache
        self.mvps_cache[mvp_id] = mvp_dict
        
        # Save JSON metadata
        self._save_json(mvp_id, mvp_dict)
        
        # Create and save ZIP archive
        self._save_zip_archive(mvp_id, mvp_dict)
        
        # Save to main file
        self._save_all_mvps()
        
        print(f"[Storage] MVP {mvp_id} salvat")
        return mvp_id
    
    def _save_json(self, mvp_id: str, mvp_dict: Dict):
        """Salvează metadata MVP în format JSON"""
        json_file = self.individual_dir / f"{mvp_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(mvp_dict, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_zip_archive(self, mvp_id: str, mvp_dict: Dict):
        """
        Creează și salvează ZIP archive cu structura completă MVP
        """
        zip_file = self.individual_dir / f"{mvp_id}.zip"
        
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            structure = mvp_dict.get('structure', {})
            files = mvp_dict.get('files', [])
            
            # Add files from structure
            self._add_structure_to_zip(zipf, structure, "")
            
            # Add files from files list
            for file_info in files:
                file_path = file_info.get('path', '')
                file_content = file_info.get('content', '')
                
                if file_path and file_content:
                    zipf.writestr(file_path, file_content)
    
    def _add_structure_to_zip(self, zipf: zipfile.ZipFile, structure: Dict, base_path: str):
        """Adaugă structura de foldere și fișiere în ZIP"""
        project_name = structure.get('project_name', 'mvp_project')
        
        if base_path == "":
            base_path = project_name
        
        folders = structure.get('folders', {})
        
        for folder_name, folder_content in folders.items():
            folder_path = f"{base_path}/{folder_name}" if base_path else folder_name
            
            if folder_content is None:
                # This is a file
                continue
            elif isinstance(folder_content, dict):
                # This is a folder
                # Add folder structure
                if folder_content:
                    self._add_structure_to_zip(zipf, {'folders': folder_content}, folder_path)
    
    def get_mvp(self, mvp_id: str) -> Optional[Dict]:
        """
        Obține MVP după ID
        
        Args:
            mvp_id: ID-ul MVP-ului
        
        Returns:
            MVP sau None
        """
        return self.mvps_cache.get(mvp_id)
    
    def list_mvps(
        self,
        limit: int = 100,
        offset: int = 0,
        wish_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Listează MVP-uri
        
        Args:
            limit: Număr maxim de MVP-uri
            offset: Offset pentru paginare
            wish_id: Filtrare după wish_id
        
        Returns:
            Lista de MVP-uri
        """
        mvps = list(self.mvps_cache.values())
        
        if wish_id:
            mvps = [m for m in mvps if m.get('wish_id') == wish_id]
        
        # Sort by generated_at descending
        mvps.sort(key=lambda m: m.get('generated_at', ''), reverse=True)
        
        return mvps[offset:offset + limit]
    
    def export_mvp_zip(self, mvp_id: str) -> Optional[Path]:
        """
        Exportă MVP ca ZIP archive
        
        Args:
            mvp_id: ID-ul MVP-ului
        
        Returns:
            Path către fișierul ZIP sau None
        """
        if mvp_id not in self.mvps_cache:
            return None
        
        zip_file = self.individual_dir / f"{mvp_id}.zip"
        
        if zip_file.exists():
            # Copy to exports directory
            export_file = self.exports_dir / f"{mvp_id}_export.zip"
            import shutil
            shutil.copy2(zip_file, export_file)
            return export_file
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Returnează statistici despre MVP-uri"""
        total_mvps = len(self.mvps_cache)
        
        wish_ids = set(m.get('wish_id') for m in self.mvps_cache.values())
        
        return {
            "total_mvps": total_mvps,
            "unique_wishes": len(wish_ids)
        }
