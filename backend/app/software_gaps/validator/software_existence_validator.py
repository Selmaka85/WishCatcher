"""
Software Existence Validator - Verifică dacă un software/serviciu există deja
Validează pe GitHub, App Store, Google Play, Product Hunt, AlternativeTo
"""

import aiohttp
import os
from typing import Dict, List, Optional, Any
import json
import re


class SoftwareExistenceValidator:
    """Validează existența software-ului pe multiple platforme"""
    
    def __init__(self):
        # API Keys (opțional - pentru rate limits mai mari)
        self.github_token = os.getenv("GITHUB_TOKEN")  # Opțional, pentru rate limit mai mare
        self.product_hunt_token = os.getenv("PRODUCT_HUNT_TOKEN")  # Opțional
        
        # Headers
        self.headers = {
            "User-Agent": "WishCatcher/1.0",
            "Accept": "application/json"
        }
        
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    async def validate_software(
        self,
        software_name: str,
        functionality: Optional[str] = None,
        language: str = "ro"
    ) -> Dict[str, Any]:
        """
        Validează dacă software-ul există pe multiple platforme
        
        Args:
            software_name: Numele software-ului
            functionality: Funcționalitatea specifică (opțional)
            language: Limba (pentru căutare localizată)
            
        Returns:
            {
                "exists": bool,  # Dacă există pe cel puțin o platformă
                "platforms": {
                    "github": {...},
                    "app_store": {...},
                    "google_play": {...},
                    "product_hunt": {...},
                    "alternativeto": {...}
                },
                "existence_score": float,  # 0-1 (0 = nu există, 1 = există peste tot)
                "quality_score": float,  # 0-1 (calitatea alternativelor existente)
                "gap_type": str  # "missing", "low_quality", "exists"
            }
        """
        results = {
            "exists": False,
            "platforms": {},
            "existence_score": 0.0,
            "quality_score": 0.0,
            "gap_type": "unknown"
        }
        
        # Caută pe toate platformele în paralel
        search_query = self._build_search_query(software_name, functionality, language)
        
        # 1. GitHub
        github_result = await self._check_github(search_query)
        results["platforms"]["github"] = github_result
        
        # 2. Product Hunt
        product_hunt_result = await self._check_product_hunt(search_query)
        results["platforms"]["product_hunt"] = product_hunt_result
        
        # 3. App Store (iOS)
        app_store_result = await self._check_app_store(search_query, language)
        results["platforms"]["app_store"] = app_store_result
        
        # 4. Google Play
        google_play_result = await self._check_google_play(search_query, language)
        results["platforms"]["google_play"] = google_play_result
        
        # 5. AlternativeTo
        alternativeto_result = await self._check_alternativeto(search_query)
        results["platforms"]["alternativeto"] = alternativeto_result
        
        # Calculează scoruri
        results["existence_score"] = self._calculate_existence_score(results["platforms"])
        results["quality_score"] = self._calculate_quality_score(results["platforms"])
        results["exists"] = results["existence_score"] > 0.3
        
        # Determină tipul gap-ului
        results["gap_type"] = self._determine_gap_type(results)
        
        return results
    
    def _build_search_query(
        self,
        software_name: str,
        functionality: Optional[str],
        language: str
    ) -> str:
        """Construiește query-ul de căutare"""
        query_parts = [software_name]
        
        if functionality:
            # Extrage keywords din funcționalitate
            func_keywords = functionality.split()[:3]  # Primele 3 cuvinte
            query_parts.extend(func_keywords)
        
        return " ".join(query_parts)
    
    async def _check_github(self, query: str) -> Dict[str, Any]:
        """Verifică dacă există pe GitHub"""
        try:
            # GitHub Search API
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": f"{query} language:python language:javascript language:typescript",
                "sort": "stars",
                "order": "desc",
                "per_page": 5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        
                        if items:
                            # Găsește cel mai relevant (cel mai multe stars)
                            top_repo = items[0]
                            
                            return {
                                "exists": True,
                                "count": len(items),
                                "top_repository": {
                                    "name": top_repo.get("name"),
                                    "full_name": top_repo.get("full_name"),
                                    "url": top_repo.get("html_url"),
                                    "stars": top_repo.get("stargazers_count", 0),
                                    "forks": top_repo.get("forks_count", 0),
                                    "description": top_repo.get("description", ""),
                                    "updated_at": top_repo.get("updated_at"),
                                    "language": top_repo.get("language")
                                },
                                "is_active": self._is_repo_active(top_repo.get("updated_at", "")),
                                "quality_score": self._calculate_github_quality(top_repo)
                            }
                        else:
                            return {
                                "exists": False,
                                "count": 0,
                                "top_repository": None,
                                "is_active": False,
                                "quality_score": 0.0
                            }
                    elif response.status == 403:
                        # Rate limit exceeded
                        print(f"[WARNING] GitHub API rate limit exceeded")
                        return {"exists": False, "error": "rate_limit"}
                    else:
                        return {"exists": False, "error": f"status_{response.status}"}
        
        except Exception as e:
            print(f"[ERROR] GitHub API error: {e}")
            return {"exists": False, "error": str(e)}
    
    async def _check_product_hunt(self, query: str) -> Dict[str, Any]:
        """Verifică dacă există pe Product Hunt"""
        try:
            # Product Hunt GraphQL API (necesită token pentru producție)
            # Pentru acum, folosim scraping simplu sau skip
            # TODO: Implementează Product Hunt API dacă ai token
            
            # Fallback: returnează că nu există (necesită implementare completă)
            return {
                "exists": False,
                "count": 0,
                "error": "not_implemented"
            }
        
        except Exception as e:
            print(f"[ERROR] Product Hunt API error: {e}")
            return {"exists": False, "error": str(e)}
    
    async def _check_app_store(self, query: str, language: str) -> Dict[str, Any]:
        """Verifică dacă există pe App Store (iOS)"""
        try:
            # iTunes Search API (neoficial, dar funcționează)
            url = "https://itunes.apple.com/search"
            params = {
                "term": query,
                "media": "software",
                "limit": 5,
                "country": "RO" if language == "ro" else "GB"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        
                        if results:
                            top_app = results[0]
                            
                            return {
                                "exists": True,
                                "count": len(results),
                                "top_app": {
                                    "name": top_app.get("trackName"),
                                    "bundle_id": top_app.get("bundleId"),
                                    "url": top_app.get("trackViewUrl"),
                                    "price": top_app.get("price", 0),
                                    "rating": top_app.get("averageUserRating", 0),
                                    "rating_count": top_app.get("userRatingCount", 0),
                                    "description": top_app.get("description", "")[:200]
                                },
                                "quality_score": self._calculate_app_store_quality(top_app)
                            }
                        else:
                            return {
                                "exists": False,
                                "count": 0,
                                "quality_score": 0.0
                            }
                    else:
                        return {"exists": False, "error": f"status_{response.status}"}
        
        except Exception as e:
            print(f"[ERROR] App Store API error: {e}")
            return {"exists": False, "error": str(e)}
    
    async def _check_google_play(self, query: str, language: str) -> Dict[str, Any]:
        """Verifică dacă există pe Google Play"""
        try:
            # Google Play nu are API oficial gratuit
            # Pentru acum, returnează că nu există (necesită scraping)
            # TODO: Implementează scraping Google Play dacă e necesar
            
            return {
                "exists": False,
                "count": 0,
                "error": "not_implemented"
            }
        
        except Exception as e:
            print(f"[ERROR] Google Play API error: {e}")
            return {"exists": False, "error": str(e)}
    
    async def _check_alternativeto(self, query: str) -> Dict[str, Any]:
        """Verifică alternative pe AlternativeTo"""
        try:
            # AlternativeTo nu are API oficial
            # Pentru acum, returnează că nu există (necesită scraping)
            # TODO: Implementează scraping AlternativeTo dacă e necesar
            
            return {
                "exists": False,
                "count": 0,
                "error": "not_implemented"
            }
        
        except Exception as e:
            print(f"[ERROR] AlternativeTo API error: {e}")
            return {"exists": False, "error": str(e)}
    
    def _is_repo_active(self, updated_at: str) -> bool:
        """Verifică dacă repository-ul e activ (actualizat în ultimele 6 luni)"""
        if not updated_at:
            return False
        
        from datetime import datetime, timedelta
        try:
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            six_months_ago = datetime.now(updated.tzinfo) - timedelta(days=180)
            return updated > six_months_ago
        except:
            return False
    
    def _calculate_github_quality(self, repo: Dict) -> float:
        """Calculează calitatea repository-ului GitHub"""
        score = 0.0
        
        # Stars (0.4)
        stars = repo.get("stargazers_count", 0)
        if stars > 1000:
            score += 0.4
        elif stars > 100:
            score += 0.3
        elif stars > 10:
            score += 0.2
        elif stars > 0:
            score += 0.1
        
        # Forks (0.2)
        forks = repo.get("forks_count", 0)
        if forks > 100:
            score += 0.2
        elif forks > 10:
            score += 0.15
        elif forks > 0:
            score += 0.1
        
        # Active (0.2)
        if self._is_repo_active(repo.get("updated_at", "")):
            score += 0.2
        
        # Has description (0.1)
        if repo.get("description"):
            score += 0.1
        
        # Has language (0.1)
        if repo.get("language"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_app_store_quality(self, app: Dict) -> float:
        """Calculează calitatea aplicației App Store"""
        score = 0.0
        
        # Rating (0.5)
        rating = app.get("averageUserRating", 0)
        if rating >= 4.5:
            score += 0.5
        elif rating >= 4.0:
            score += 0.4
        elif rating >= 3.5:
            score += 0.3
        elif rating >= 3.0:
            score += 0.2
        elif rating > 0:
            score += 0.1
        
        # Rating count (0.3)
        rating_count = app.get("userRatingCount", 0)
        if rating_count > 1000:
            score += 0.3
        elif rating_count > 100:
            score += 0.2
        elif rating_count > 10:
            score += 0.1
        
        # Has description (0.2)
        if app.get("description"):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_existence_score(self, platforms: Dict) -> float:
        """Calculează scorul de existență (0-1)"""
        scores = []
        
        for platform, result in platforms.items():
            if result.get("exists"):
                # GitHub e cel mai important (0.4)
                if platform == "github":
                    scores.append(0.4)
                # App Store și Google Play (0.2 fiecare)
                elif platform in ["app_store", "google_play"]:
                    scores.append(0.2)
                # Product Hunt și AlternativeTo (0.1 fiecare)
                elif platform in ["product_hunt", "alternativeto"]:
                    scores.append(0.1)
        
        return min(sum(scores), 1.0)
    
    def _calculate_quality_score(self, platforms: Dict) -> float:
        """Calculează scorul de calitate (0-1)"""
        quality_scores = []
        
        for platform, result in platforms.items():
            if result.get("exists"):
                quality = result.get("quality_score", 0.0)
                # Weights diferite pentru fiecare platformă
                if platform == "github":
                    quality_scores.append(quality * 0.4)
                elif platform in ["app_store", "google_play"]:
                    quality_scores.append(quality * 0.3)
                else:
                    quality_scores.append(quality * 0.1)
        
        if quality_scores:
            return min(sum(quality_scores), 1.0)
        return 0.0
    
    def _determine_gap_type(self, results: Dict) -> str:
        """Determină tipul gap-ului"""
        existence_score = results.get("existence_score", 0.0)
        quality_score = results.get("quality_score", 0.0)
        
        if existence_score < 0.3:
            return "missing"  # Nu există
        elif quality_score < 0.5:
            return "low_quality"  # Există dar e de calitate slabă
        else:
            return "exists"  # Există și e de calitate bună
