"""
Multi-Marketplace Scraper - Scraping pentru eMAG, Amazon UK, Altex, PCGarage
"""

import aiohttp
import re
import time
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import quote
from .product_scraper import ProductScraper


class MultiMarketplaceScraper:
    """Scraper pentru multiple marketplace-uri"""
    
    def __init__(self):
        self.base_scraper = ProductScraper()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    
    async def search_all_marketplaces(self, product_name: str) -> Dict[str, Any]:
        """
        Caută produsul pe toate marketplace-urile
        
        Args:
            product_name: Numele produsului
            
        Returns:
            Dict cu rezultate de pe fiecare marketplace
        """
        results = {
            "product_name": product_name,
            "emag": None,
            "amazon_uk": None,
            "altex": None,
            "pcgarage": None
        }
        
        # Search eMAG
        try:
            emag_results = await self.base_scraper.search_emag(product_name)
            if emag_results:
                results["emag"] = {
                    "status": "available" if emag_results[0].get("available") else "missing",
                    "price": emag_results[0].get("price"),
                    "url": emag_results[0].get("url"),
                    "products": emag_results
                }
            else:
                results["emag"] = {"status": "missing", "price": None, "url": None, "products": []}
        except Exception as e:
            print(f"[ERROR] Error searching eMAG: {e}")
            results["emag"] = {"status": "error", "price": None, "url": None, "products": []}
        
        # Search Amazon UK (folosește PA-API dacă e configurat, altfel scraping)
        try:
            amazon_results = await self.base_scraper.search_amazon_uk(product_name, use_paapi=True)
            if amazon_results:
                results["amazon_uk"] = {
                    "status": "available" if amazon_results[0].get("available") else "missing",
                    "price": amazon_results[0].get("price"),
                    "url": amazon_results[0].get("url"),
                    "products": amazon_results
                }
            else:
                results["amazon_uk"] = {"status": "missing", "price": None, "url": None, "products": []}
        except Exception as e:
            print(f"[ERROR] Error searching Amazon UK: {e}")
            results["amazon_uk"] = {"status": "error", "price": None, "url": None, "products": []}
        
        # Search Altex
        try:
            altex_results = await self.search_altex(product_name)
            if altex_results:
                results["altex"] = {
                    "status": "available",
                    "price": altex_results[0].get("price"),
                    "url": altex_results[0].get("url"),
                    "products": altex_results
                }
            else:
                results["altex"] = {"status": "missing", "price": None, "url": None, "products": []}
        except Exception as e:
            print(f"[ERROR] Error searching Altex: {e}")
            results["altex"] = {"status": "error", "price": None, "url": None, "products": []}
        
        # Search PCGarage
        try:
            pcgarage_results = await self.search_pcgarage(product_name)
            if pcgarage_results:
                results["pcgarage"] = {
                    "status": "available",
                    "price": pcgarage_results[0].get("price"),
                    "url": pcgarage_results[0].get("url"),
                    "products": pcgarage_results
                }
            else:
                results["pcgarage"] = {"status": "missing", "price": None, "url": None, "products": []}
        except Exception as e:
            print(f"[ERROR] Error searching PCGarage: {e}")
            results["pcgarage"] = {"status": "error", "price": None, "url": None, "products": []}
        
        return results
    
    async def search_altex(self, product_name: str) -> List[Dict[str, Any]]:
        """Caută produs pe Altex.ro"""
        products = []
        
        try:
            search_query = quote(product_name)
            url = f"https://altex.ro/cauta/?q={search_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Găsește produsele (structura Altex)
                        product_cards = soup.find_all('div', class_=re.compile(r'product|item|card'))
                        
                        for card in product_cards[:10]:
                            try:
                                # Extract product name
                                name_elem = card.find('a', class_=re.compile(r'product-title|title|name'))
                                if not name_elem:
                                    name_elem = card.find('h2') or card.find('h3')
                                
                                if not name_elem:
                                    continue
                                
                                product_name_found = name_elem.get_text(strip=True)
                                
                                # Extract price
                                price_elem = card.find('span', class_=re.compile(r'price|product-price'))
                                if not price_elem:
                                    price_elem = card.find('div', class_=re.compile(r'price'))
                                
                                price = None
                                if price_elem:
                                    price_text = price_elem.get_text(strip=True)
                                    price_match = re.search(r'(\d+[\.,]?\d*)', price_text.replace('.', '').replace(',', '.'))
                                    if price_match:
                                        try:
                                            price = float(price_match.group(1))
                                        except:
                                            pass
                                
                                # Extract URL
                                link_elem = card.find('a', href=True)
                                product_url = None
                                if link_elem:
                                    href = link_elem.get('href', '')
                                    if href.startswith('http'):
                                        product_url = href
                                    else:
                                        product_url = f"https://altex.ro{href}"
                                
                                # Extract image
                                img_elem = card.find('img', src=True)
                                image_url = img_elem.get('src', '') if img_elem else None
                                
                                if product_name_found:
                                    products.append({
                                        "name": product_name_found,
                                        "price": price,
                                        "url": product_url,
                                        "image_url": image_url,
                                        "available": price is not None
                                    })
                            
                            except Exception as e:
                                print(f"[WARNING] Error parsing Altex product: {e}")
                                continue
            
            time.sleep(1)  # Rate limiting
        
        except Exception as e:
            print(f"[ERROR] Error searching Altex: {e}")
        
        return products
    
    async def search_pcgarage(self, product_name: str) -> List[Dict[str, Any]]:
        """Caută produs pe PCGarage.ro"""
        products = []
        
        try:
            search_query = quote(product_name)
            url = f"https://www.pcgarage.ro/cauta/?q={search_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Găsește produsele (structura PCGarage)
                        product_cards = soup.find_all('div', class_=re.compile(r'product|item|card'))
                        
                        for card in product_cards[:10]:
                            try:
                                # Extract product name
                                name_elem = card.find('a', class_=re.compile(r'product-title|title|name'))
                                if not name_elem:
                                    name_elem = card.find('h2') or card.find('h3')
                                
                                if not name_elem:
                                    continue
                                
                                product_name_found = name_elem.get_text(strip=True)
                                
                                # Extract price
                                price_elem = card.find('span', class_=re.compile(r'price|product-price'))
                                if not price_elem:
                                    price_elem = card.find('div', class_=re.compile(r'price'))
                                
                                price = None
                                if price_elem:
                                    price_text = price_elem.get_text(strip=True)
                                    price_match = re.search(r'(\d+[\.,]?\d*)', price_text.replace('.', '').replace(',', '.'))
                                    if price_match:
                                        try:
                                            price = float(price_match.group(1))
                                        except:
                                            pass
                                
                                # Extract URL
                                link_elem = card.find('a', href=True)
                                product_url = None
                                if link_elem:
                                    href = link_elem.get('href', '')
                                    if href.startswith('http'):
                                        product_url = href
                                    else:
                                        product_url = f"https://www.pcgarage.ro{href}"
                                
                                # Extract image
                                img_elem = card.find('img', src=True)
                                image_url = img_elem.get('src', '') if img_elem else None
                                
                                if product_name_found:
                                    products.append({
                                        "name": product_name_found,
                                        "price": price,
                                        "url": product_url,
                                        "image_url": image_url,
                                        "available": price is not None
                                    })
                            
                            except Exception as e:
                                print(f"[WARNING] Error parsing PCGarage product: {e}")
                                continue
            
            time.sleep(1)  # Rate limiting
        
        except Exception as e:
            print(f"[ERROR] Error searching PCGarage: {e}")
        
        return products
