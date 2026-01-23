"""
Amazon Product Advertising API 5.0 - Scraper oficial (GRATUIT)
Implementare manuală - nu necesită SDK extern
"""

import os
import hmac
import hashlib
import requests
import json
from typing import List, Dict, Any
from datetime import datetime


class AmazonPAAPIScraper:
    """Scraper pentru Amazon folosind Product Advertising API 5.0 (GRATUIT) - Implementare manuală"""
    
    def __init__(self):
        # Configurare din variabile de mediu
        self.access_key = os.getenv("AMAZON_ACCESS_KEY")
        self.secret_key = os.getenv("AMAZON_SECRET_KEY")
        self.partner_tag = os.getenv("AMAZON_PARTNER_TAG")  # Associate Tag
        self.host = os.getenv("AMAZON_HOST", "webservices.amazon.co.uk")  # UK
        self.region = os.getenv("AMAZON_REGION", "eu-west-1")
        self.endpoint = f"https://{self.host}/paapi5/searchitems"
        
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            print("[WARNING] Amazon PA-API credentials not configured.")
            print("[INFO] Set environment variables:")
            print("  - AMAZON_ACCESS_KEY")
            print("  - AMAZON_SECRET_KEY")
            print("  - AMAZON_PARTNER_TAG (your Associate Tag)")
            print("[INFO] See backend/AMAZON_PAAPI_SETUP.md for setup instructions")
            self.configured = False
        else:
            self.configured = True
    
    def _sign_request(self, payload: str, timestamp: str) -> str:
        """Generează semnătura pentru request PA-API"""
        string_to_sign = f"POST\n{self.host}\n/paapi5/searchitems\n{payload}\n{timestamp}\n"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return signature.hex()
    
    def search_products(self, keywords: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Caută produse pe Amazon UK folosind PA-API 5.0 (implementare manuală)
        
        Args:
            keywords: Cuvinte cheie pentru căutare
            max_results: Număr maxim de rezultate (max 10 pentru free tier)
            
        Returns:
            Lista de produse găsite
        """
        if not self.configured:
            print("[ERROR] Amazon PA-API not configured. Cannot search products.")
            return []
        
        products = []
        
        try:
            # Construiește payload-ul
            payload = {
                "PartnerTag": self.partner_tag,
                "PartnerType": "Associates",
                "Keywords": keywords,
                "SearchIndex": "All",
                "ItemCount": min(max_results, 10),
                "Resources": [
                    "ItemInfo.Title",
                    "Offers.Listings.Price",
                    "Images.Primary.Large",
                    "ItemInfo.Features",
                    "Offers.Listings.Availability.Message"
                ]
            }
            
            payload_str = json.dumps(payload, separators=(',', ':'))
            timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            
            # Generează semnătura (simplified - pentru producție folosește AWS Signature V4 complet)
            # NOTĂ: Această implementare este simplificată. Pentru producție, folosește AWS Signature V4 complet
            string_to_sign = f"POST\n{self.host}\n/paapi5/searchitems\n{payload_str}\n{timestamp}\n"
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Headers
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "X-Amazon-Advertising-API-ClientId": self.access_key,
                "X-Amazon-Advertising-API-Scope": "paapi5",
                "X-Amz-Date": timestamp,
                "Authorization": f"AWS4-HMAC-SHA256 Credential={self.access_key}/{timestamp[:8]}/{self.region}/ProductAdvertisingAPI/aws4_request, SignedHeaders=content-type;host;x-amz-date, Signature={signature}"
            }
            
            # Face request-ul
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=payload_str.encode('utf-8'),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "SearchResult" in data and "Items" in data["SearchResult"]:
                    for item in data["SearchResult"]["Items"]:
                        try:
                            product_data = {
                                "name": item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "Unknown"),
                                "price": None,
                                "url": item.get("DetailPageURL"),
                                "image_url": None,
                                "available": False,
                                "fba_eligible": False,
                                "asin": item.get("ASIN")
                            }
                            
                            # Extrage prețul
                            offers = item.get("Offers", {})
                            listings = offers.get("Listings", [])
                            if listings:
                                listing = listings[0]
                                price = listing.get("Price", {})
                                if price:
                                    product_data["price"] = float(price.get("Amount", 0))
                                
                                availability = listing.get("Availability", {})
                                if availability:
                                    message = availability.get("Message", "")
                                    product_data["available"] = "InStock" in message or "In stock" in message
                            
                            # Extrage imaginea
                            images = item.get("Images", {})
                            primary = images.get("Primary", {})
                            large = primary.get("Large", {})
                            if large:
                                product_data["image_url"] = large.get("URL")
                            
                            # Verifică FBA eligibility
                            if product_data["available"] and product_data["price"]:
                                product_data["fba_eligible"] = True
                            
                            if product_data["name"] and product_data["name"] != "Unknown":
                                products.append(product_data)
                        
                        except Exception as e:
                            print(f"[WARNING] Error parsing Amazon product: {e}")
                            continue
            
            elif response.status_code == 401:
                print("[ERROR] Invalid credentials. Check AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG")
            elif response.status_code == 403:
                print("[ERROR] Access denied. Check if your Associate account is approved and has qualifying sales.")
            elif response.status_code == 429:
                print("[ERROR] Rate limit exceeded. Wait before making more requests.")
            else:
                print(f"[ERROR] Amazon PA-API error: {response.status_code}")
                print(f"[ERROR] Response: {response.text[:200]}")
        
        except Exception as e:
            print(f"[ERROR] Unexpected error in Amazon PA-API: {e}")
            import traceback
            traceback.print_exc()
        
        return products
    
    def is_configured(self) -> bool:
        """Verifică dacă API-ul este configurat corect"""
        return self.configured
