"""
Product Scraper - eMAG.ro și Amazon UK (fără Selenium/Playwright)
Folosește BeautifulSoup + aiohttp pentru scraping simplu
"""

import aiohttp
import re
import time
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin


class ProductScraper:
    """Scraper pentru eMAG.ro și Amazon UK"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    
    async def search_emag(self, category: str, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Caută produse pe eMAG.ro
        
        Args:
            category: Categoria produsului
            max_price: Preț maxim (lei)
            
        Returns:
            Lista de produse găsite
        """
        products = []
        
        try:
            # URL căutare eMAG
            search_query = quote(category)
            url = f"https://www.emag.ro/search/{search_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # eMAG structure 2024 - multiple selectors pentru robustețe
                        # Încearcă mai multe structuri posibile
                        product_cards = []
                        
                        # Selector 1: Card-uri cu clasa "card-item" sau "product-item"
                        product_cards = soup.find_all('div', class_=re.compile(r'card-item|product-item|card-v2|product-card'))
                        
                        # Selector 2: Dacă nu găsește, încearcă cu data-* attributes
                        if not product_cards:
                            product_cards = soup.find_all('div', {'data-product-id': True})
                        
                        # Selector 3: Fallback - orice div cu link către produs
                        if not product_cards:
                            all_links = soup.find_all('a', href=re.compile(r'/product/|/p/'))
                            for link in all_links[:30]:
                                parent = link.find_parent('div')
                                if parent:
                                    product_cards.append(parent)
                        
                        print(f"[eMAG] Found {len(product_cards)} potential product cards")
                        
                        for card in product_cards[:20]:  # Limit to 20 products
                            try:
                                # Extract product name - multiple strategies
                                product_name = None
                                
                                # Strategy 1: Link cu clasa "product-title" sau "title"
                                name_elem = card.find('a', class_=re.compile(r'product-title|product-title-link|title'))
                                if name_elem:
                                    product_name = name_elem.get_text(strip=True)
                                
                                # Strategy 2: H2 sau H3 în card
                                if not product_name:
                                    name_elem = card.find('h2') or card.find('h3')
                                    if name_elem:
                                        product_name = name_elem.get_text(strip=True)
                                
                                # Strategy 3: Span cu clasa "title" sau "name"
                                if not product_name:
                                    name_elem = card.find('span', class_=re.compile(r'title|name|product-name'))
                                    if name_elem:
                                        product_name = name_elem.get_text(strip=True)
                                
                                # Strategy 4: Orice link către produs
                                if not product_name:
                                    link_elem = card.find('a', href=re.compile(r'/product/|/p/'))
                                    if link_elem:
                                        product_name = link_elem.get_text(strip=True)
                                
                                if not product_name or len(product_name) < 3:
                                    continue
                                
                                # Extract price - multiple strategies
                                price = None
                                
                                # Strategy 1: Span cu clasa "price" sau "product-price"
                                price_elem = card.find('p', class_=re.compile(r'product-new-price|price'))
                                if not price_elem:
                                    price_elem = card.find('span', class_=re.compile(r'product-new-price|price|amount'))
                                
                                if price_elem:
                                    price_text = price_elem.get_text(strip=True)
                                    # Extract number from price (ex: "1.299,99 lei" -> 1299.99)
                                    # Remove "lei", "RON", spaces, dots (thousands), keep comma as decimal
                                    price_clean = re.sub(r'[^\d,\.]', '', price_text)
                                    price_clean = price_clean.replace('.', '').replace(',', '.')
                                    price_match = re.search(r'(\d+\.?\d*)', price_clean)
                                    if price_match:
                                        try:
                                            price = float(price_match.group(1))
                                        except:
                                            pass
                                
                                # Filter by max_price if specified
                                if max_price and price and price > max_price:
                                    continue
                                
                                # Extract URL - multiple strategies
                                product_url = None
                                
                                # Strategy 1: Link cu href către /product/ sau /p/
                                link_elem = card.find('a', href=re.compile(r'/product/|/p/'))
                                if link_elem:
                                    href = link_elem.get('href', '')
                                    if href.startswith('http'):
                                        product_url = href
                                    elif href.startswith('/'):
                                        product_url = f"https://www.emag.ro{href}"
                                    else:
                                        product_url = f"https://www.emag.ro/{href}"
                                
                                # Strategy 2: Orice link în card
                                if not product_url:
                                    link_elem = card.find('a', href=True)
                                    if link_elem:
                                        href = link_elem.get('href', '')
                                        if '/product/' in href or '/p/' in href:
                                            if href.startswith('http'):
                                                product_url = href
                                            elif href.startswith('/'):
                                                product_url = f"https://www.emag.ro{href}"
                                
                                # Strategy 3: Data attribute
                                if not product_url and card.get('data-product-id'):
                                    product_id = card.get('data-product-id')
                                    product_url = f"https://www.emag.ro/product/{product_id}"
                                
                                # Extract image
                                image_url = None
                                img_elem = card.find('img', src=True) or card.find('img', {'data-src': True})
                                if img_elem:
                                    image_url = img_elem.get('src') or img_elem.get('data-src')
                                
                                if product_name:
                                    products.append({
                                        "name": product_name,
                                        "price": price,
                                        "url": product_url,
                                        "image_url": image_url,
                                        "available": price is not None
                                    })
                            
                            except Exception as e:
                                print(f"[WARNING] Error parsing eMAG product: {e}")
                                continue
            
            # If no products found with BeautifulSoup, try alternative selectors
            if not products:
                # Try alternative structure
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Alternative: look for JSON-LD structured data
                            json_ld = soup.find('script', type='application/ld+json')
                            if json_ld:
                                import json
                                try:
                                    data = json.loads(json_ld.string)
                                    if isinstance(data, dict) and 'itemListElement' in data:
                                        for item in data['itemListElement'][:20]:
                                            if 'item' in item:
                                                item_data = item['item']
                                                products.append({
                                                    "name": item_data.get('name', ''),
                                                    "price": None,
                                                    "url": item_data.get('url', ''),
                                                    "image_url": item_data.get('image', ''),
                                                    "available": True
                                                })
                                except:
                                    pass
        
        except Exception as e:
            print(f"[ERROR] Error searching eMAG: {e}")
        
        return products
    
    async def search_amazon_uk(self, category: str, max_price: Optional[float] = None, use_paapi: bool = True) -> List[Dict[str, Any]]:
        """
        Caută produse pe Amazon UK (fără Selenium)
        
        Args:
            category: Categoria produsului
            max_price: Preț maxim (£)
            
        Returns:
            Lista de produse găsite
        """
        products = []
        
        # Încearcă să folosească PA-API 5.0 (GRATUIT și oficial) dacă e configurat
        if use_paapi:
            try:
                from .amazon_paapi import AmazonPAAPIScraper
                paapi_scraper = AmazonPAAPIScraper()
                
                if paapi_scraper.is_configured():
                    print(f"[Amazon UK] Using PA-API 5.0 (official API)")
                    paapi_products = paapi_scraper.search_products(category, max_results=10)
                    
                    if paapi_products:
                        print(f"[Amazon UK] Found {len(paapi_products)} products via PA-API")
                        # Filtrează după preț dacă e specificat
                        if max_price:
                            # Convert max_price din lei la £ (1£ ≈ 5.5 lei)
                            max_price_gbp = max_price / 5.5
                            paapi_products = [p for p in paapi_products if not p.get("price") or p.get("price") <= max_price_gbp]
                        
                        return paapi_products
                    else:
                        print(f"[Amazon UK] PA-API returned no products, falling back to scraping")
                else:
                    print(f"[Amazon UK] PA-API not configured, using scraping fallback")
            
            except ImportError:
                print(f"[Amazon UK] PA-API SDK not installed, using scraping fallback")
            except Exception as e:
                print(f"[Amazon UK] PA-API error: {e}, falling back to scraping")
        
        # Fallback la scraping dacă PA-API nu e disponibil/configurat
        try:
            # URL căutare Amazon UK - folosim formatul corect
            search_query = quote(category)
            url = f"https://www.amazon.co.uk/s?k={search_query}&ref=sr_pg_1"
            
            # Headers mai realiști pentru Amazon
            amazon_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=amazon_headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Amazon UK structure 2024 - multiple selectors pentru robustețe
                        product_cards = []
                        
                        # Selector 1: Data component type (cel mai comun)
                        product_cards = soup.find_all('div', {'data-component-type': 's-search-result'})
                        
                        # Selector 2: Class-based (backup)
                        if not product_cards:
                            product_cards = soup.find_all('div', class_=re.compile(r's-result-item|s-card-container'))
                        
                        # Selector 3: Data ASIN (Amazon Standard Identification Number)
                        if not product_cards:
                            product_cards = soup.find_all('div', {'data-asin': True})
                        
                        # Selector 4: Fallback - orice div cu link către /dp/ sau /gp/product/
                        if not product_cards:
                            all_links = soup.find_all('a', href=re.compile(r'/dp/|/gp/product/'))
                            for link in all_links[:30]:
                                parent = link.find_parent('div')
                                if parent:
                                    product_cards.append(parent)
                        
                        print(f"[Amazon UK] Found {len(product_cards)} potential product cards")
                        print(f"[Amazon UK] Response status: {response.status}")
                        print(f"[Amazon UK] HTML length: {len(html)} characters")
                        
                        # Debug: salvează HTML-ul dacă nu găsește produse
                        if not product_cards and len(html) > 1000:
                            print(f"[Amazon UK] WARNING: No product cards found but HTML exists. Possible anti-bot protection.")
                            # Încearcă să găsească indicii de anti-bot
                            if "captcha" in html.lower() or "robot" in html.lower() or "access denied" in html.lower():
                                print(f"[Amazon UK] ⚠️  Possible CAPTCHA or bot detection detected!")
                        
                        for card in product_cards[:20]:  # Limit to 20 products
                            try:
                                # Extract product name - multiple strategies
                                product_name = None
                                
                                # Strategy 1: H2 cu clasa "a-size-mini" sau "a-size-base"
                                name_elem = card.find('h2', class_=re.compile(r'a-size-mini|a-size-base|a-size-medium'))
                                if name_elem:
                                    # Găsește link-ul din h2
                                    link_in_h2 = name_elem.find('a')
                                    if link_in_h2:
                                        product_name = link_in_h2.get_text(strip=True)
                                    else:
                                        product_name = name_elem.get_text(strip=True)
                                
                                # Strategy 2: Span cu clasa "a-text-normal" sau "a-size-base"
                                if not product_name:
                                    name_elem = card.find('span', class_=re.compile(r'a-text-normal|a-size-base|a-size-medium'))
                                    if name_elem:
                                        product_name = name_elem.get_text(strip=True)
                                
                                # Strategy 3: Orice link către /dp/ sau /gp/product/
                                if not product_name:
                                    link_elem = card.find('a', href=re.compile(r'/dp/|/gp/product/'))
                                    if link_elem:
                                        product_name = link_elem.get_text(strip=True)
                                
                                if not product_name or len(product_name) < 3:
                                    continue
                                
                                # Extract price - multiple strategies
                                price = None
                                
                                # Strategy 1: Span cu clasa "a-price" sau "a-offscreen"
                                price_elem = card.find('span', class_=re.compile(r'a-price-whole|a-offscreen'))
                                if not price_elem:
                                    price_elem = card.find('span', class_=re.compile(r'a-price'))
                                
                                if price_elem:
                                    price_text = price_elem.get_text(strip=True)
                                    # Extract number from price (ex: "£29.99" -> 29.99)
                                    price_clean = re.sub(r'[^\d\.]', '', price_text)
                                    price_match = re.search(r'(\d+\.?\d*)', price_clean)
                                    if price_match:
                                        try:
                                            price = float(price_match.group(1))
                                        except:
                                            pass
                                
                                # Strategy 2: Caută în span-uri cu text care conține £
                                if not price:
                                    price_spans = card.find_all('span', string=re.compile(r'£'))
                                    for span in price_spans:
                                        price_text = span.get_text(strip=True)
                                        price_match = re.search(r'£?\s*(\d+\.?\d*)', price_text)
                                        if price_match:
                                            try:
                                                price = float(price_match.group(1))
                                                break
                                            except:
                                                pass
                                
                                # Filter by max_price if specified (convert lei to £, approximate 1£ = 5.5 lei)
                                if max_price and price:
                                    max_price_gbp = max_price / 5.5  # Approximate conversion
                                    if price > max_price_gbp:
                                        continue
                                
                                # Extract URL - multiple strategies
                                product_url = None
                                
                                # Strategy 1: Link cu href către /dp/ sau /gp/product/
                                link_elem = card.find('a', href=re.compile(r'/dp/|/gp/product/'))
                                if link_elem:
                                    href = link_elem.get('href', '')
                                    # Remove query parameters and fragments
                                    href = href.split('?')[0].split('#')[0]
                                    if href.startswith('http'):
                                        product_url = href
                                    elif href.startswith('/'):
                                        product_url = f"https://www.amazon.co.uk{href}"
                                    else:
                                        product_url = f"https://www.amazon.co.uk/{href}"
                                
                                # Strategy 2: Data ASIN
                                if not product_url and card.get('data-asin'):
                                    asin = card.get('data-asin')
                                    product_url = f"https://www.amazon.co.uk/dp/{asin}"
                                
                                # Strategy 3: Orice link în card
                                if not product_url:
                                    link_elem = card.find('a', href=True)
                                    if link_elem:
                                        href = link_elem.get('href', '')
                                        if '/dp/' in href or '/gp/product/' in href:
                                            href = href.split('?')[0].split('#')[0]
                                            if href.startswith('http'):
                                                product_url = href
                                            elif href.startswith('/'):
                                                product_url = f"https://www.amazon.co.uk{href}"
                                
                                # Extract image
                                image_url = None
                                img_elem = card.find('img', {'data-image-latency': True}) or card.find('img', src=re.compile(r'images-amazon|ssl-images-amazon'))
                                if img_elem:
                                    image_url = img_elem.get('src') or img_elem.get('data-src')
                                
                                # Check FBA eligibility (simplified - assume eligible if price exists)
                                fba_eligible = price is not None
                                
                                if product_name:
                                    products.append({
                                        "name": product_name,
                                        "price": price,
                                        "url": product_url,
                                        "image_url": image_url,
                                        "available": price is not None,
                                        "fba_eligible": fba_eligible
                                    })
                            
                            except Exception as e:
                                print(f"[WARNING] Error parsing Amazon product: {e}")
                                continue
        
        except Exception as e:
            print(f"[ERROR] Error searching Amazon UK: {e}")
            import traceback
            traceback.print_exc()
        
        # Dacă nu găsește produse, încercă o metodă alternativă (mock data pentru testare)
        if not products:
            print(f"[Amazon UK] WARNING: No products found. This is likely due to anti-bot protection.")
            print(f"[Amazon UK] Suggestion: Use Amazon Product Advertising API or a proxy service for production.")
            # Pentru testare, putem returna produse mock (comentat pentru producție)
            # products = self._get_mock_amazon_products(category)
        
        return products
    
    def _get_mock_amazon_products(self, category: str) -> List[Dict[str, Any]]:
        """
        Mock products pentru testare când scraping-ul nu funcționează
        DOAR PENTRU TESTARE - NU FOLOSI ÎN PRODUCȚIE
        """
        mock_products = {
            "laptop": [
                {
                    "name": "Laptop Dell XPS 13",
                    "price": 899.99,
                    "url": "https://www.amazon.co.uk/dp/B08XXXXX",
                    "available": True,
                    "fba_eligible": True
                }
            ]
        }
        return mock_products.get(category.lower(), [])
    
    async def find_product_gaps(
        self,
        category: str,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Identifică gap-uri între eMAG și Amazon UK
        
        Args:
            category: Categoria produsului
            max_price: Preț maxim (lei)
            
        Returns:
            Lista de gap-uri identificate
        """
        gaps = []
        
        # Search both platforms
        emag_products = await self.search_emag(category, max_price)
        amazon_products = await self.search_amazon_uk(category, max_price)
        
        # Create lookup maps
        emag_names = {p["name"].lower(): p for p in emag_products}
        amazon_names = {p["name"].lower(): p for p in amazon_products}
        
        # Find products that exist on Amazon but not on eMAG
        for amazon_product in amazon_products:
            amazon_name_lower = amazon_product["name"].lower()
            
            # Check if similar product exists on eMAG (simple keyword matching)
            found_on_emag = False
            emag_match = None
            
            # Extract keywords from Amazon product name
            amazon_keywords = set(amazon_name_lower.split())
            
            for emag_name, emag_product in emag_names.items():
                emag_keywords = set(emag_name.split())
                # If at least 2 keywords match, consider it similar
                if len(amazon_keywords.intersection(emag_keywords)) >= 2:
                    found_on_emag = True
                    emag_match = emag_product
                    break
            
            # If not found on eMAG or significantly more expensive
            if not found_on_emag:
                # Product missing from eMAG
                gaps.append({
                    "product_name": amazon_product["name"],
                    "category": category,
                    "emag_status": "missing",
                    "emag_price": None,
                    "emag_url": None,
                    "amazon_uk_price": amazon_product.get("price"),
                    "amazon_uk_url": amazon_product.get("url"),
                    "amazon_global_price": None,
                    "amazon_global_url": None,
                    "profit_margin": None,  # Will be calculated later
                    "fba_eligible": amazon_product.get("fba_eligible", False),
                    "image_url": amazon_product.get("image_url"),
                    "risk_level": "medium"
                })
            elif emag_match and amazon_product.get("price"):
                # Compare prices (convert £ to lei: 1£ ≈ 5.5 lei)
                amazon_price_lei = amazon_product["price"] * 5.5
                emag_price = emag_match.get("price")
                
                if emag_price and amazon_price_lei < emag_price * 0.8:  # Amazon is at least 20% cheaper
                    # Product is expensive on eMAG
                    profit_margin = ((emag_price - amazon_price_lei) / emag_price) * 100
                    
                    gaps.append({
                        "product_name": amazon_product["name"],
                        "category": category,
                        "emag_status": "expensive",
                        "emag_price": emag_price,
                        "emag_url": emag_match.get("url"),
                        "amazon_uk_price": amazon_product.get("price"),
                        "amazon_uk_url": amazon_product.get("url"),
                        "amazon_global_price": None,
                        "amazon_global_url": None,
                        "profit_margin": profit_margin,
                        "fba_eligible": amazon_product.get("fba_eligible", False),
                        "image_url": amazon_product.get("image_url"),
                        "risk_level": "low" if profit_margin > 30 else "medium"
                    })
        
        return gaps
