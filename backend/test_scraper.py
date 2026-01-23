"""
Test script pentru scraper-ul de produse
"""
import asyncio
from app.product_gaps.scraper.product_scraper import ProductScraper

async def test_scraper():
    scraper = ProductScraper()
    
    print("=== Testing eMAG scraper ===")
    emag_results = await scraper.search_emag("laptop")
    print(f"eMAG results: {len(emag_results)} products")
    if emag_results:
        print(f"First product: {emag_results[0]}")
    else:
        print("❌ No products found on eMAG")
    
    print("\n=== Testing Amazon UK scraper ===")
    amazon_results = await scraper.search_amazon_uk("laptop")
    print(f"Amazon UK results: {len(amazon_results)} products")
    if amazon_results:
        print(f"First product: {amazon_results[0]}")
    else:
        print("[ERROR] No products found on Amazon UK")
        print("This might be due to:")
        print("  1. Anti-bot protection (CAPTCHA)")
        print("  2. IP blocking")
        print("  3. Changed HTML structure")
        print("  4. Need for cookies/session")

if __name__ == "__main__":
    asyncio.run(test_scraper())
