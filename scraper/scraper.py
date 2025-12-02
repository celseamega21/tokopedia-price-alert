from typing import NamedTuple, Optional
import requests
from bs4 import BeautifulSoup
from logging import getLogger

logger = getLogger(__name__)

class InitialProduct(NamedTuple):
    name: str
    discount_price: str
    original_price: Optional[str]

class Scraper:
    def __init__(self, url:str):
        self.url = url

    def get_soup(self, url) -> BeautifulSoup:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}

        try: 
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException:
            logger.exception(f'Error fetching page')
            return None
        
    def scrape_product(self) -> None:
        results = []
        print(f"On searching...")

        soup = self.get_soup(self.url)

        if not soup:
            print(f'Failed to fetch data from Tokopedia.')
            return results
        
        name = soup.select_one("div.css-1nylpq2").get_text(strip=True)
        original_price = soup.select_one("div.original-price span:nth-of-type(2)")
        discount_price = soup.select_one("div.price")

        if original_price and discount_price:
            original_price = original_price.get_text(strip=True)
            discount_price = discount_price.get_text(strip=True)
        else:
            discount_price = discount_price.get_text(strip=True)
            original_price = discount_price

        product_result = InitialProduct(
            name=name,
            discount_price=discount_price,
            original_price=original_price,
        )
        results.append(product_result)

        if not results:
            raise Exception('No products found')
        
        return {
            "product_name": name if name else "Unknown",
            "original_price": original_price if original_price else 0,
            "discount_price": discount_price if discount_price else 0
        }