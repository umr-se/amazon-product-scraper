import requests
import random
import time
from bs4 import BeautifulSoup

# List of common user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
]

HEADERS = {
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    'DNT': '1'  # Do Not Track header
}


def save_to_file(products, filename="samsung_products.txt"):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Samsung Wireless Headphones - Price Comparison\n")
        f.write("=============================================\n\n")
        for idx, product in enumerate(products, 1):
            f.write(f"Product {idx}:\n")
            f.write(f"Title: {product['title']}\n")
            f.write(f"Price: ${product['price'] or 'Price not available'}\n")
            f.write("-" * 50 + "\n")
            
def get_page(url, retries=3):
    session = requests.Session()
    for _ in range(retries):
        try:
            # Random user agent rotation
            headers = {**HEADERS, 'User-Agent': random.choice(USER_AGENTS)}
            
            time.sleep(random.uniform(2, 5))
            
            response = session.get(url, headers=headers, timeout=10)
            
            # Check for CAPTCHA or blocking
            if "api-services-support@amazon.com" in response.text:
                print("CAPTCHA encountered. Try again later.")
                return None
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print("Access denied. Consider using proxies.")
                return None
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
    return None

def parse_product_page(html):
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract product data (update selectors as needed)
    product = {
        'title': soup.select_one('#productTitle').get_text(strip=True) if soup.select_one('#productTitle') else None,
        'price': soup.select_one('.a-price-whole').get_text(strip=True) if soup.select_one('.a-price-whole') else None,
        'rating': soup.select_one('.a-icon-star span').get_text(strip=True) if soup.select_one('.a-icon-star span') else None
    }
    return product

if __name__ == "__main__":
    search_query = "wireless+headphones"
    brand_filter = "Samsung"
    products_collected = []
    
    base_url = f"https://www.amazon.com/s?k={search_query}&rh=p_89%3A{brand_filter}"
    
    page = 1
    max_pages = 5  # Limit pages to scrape to avoid detection
    
    while len(products_collected) < 10 and page <= max_pages:
        url = f"{base_url}&page={page}"
        print(f"Scraping: {url}")
        
        html = get_page(url)
        if not html:
            page += 1
            continue
        
        soup = BeautifulSoup(html, 'lxml')
        products = soup.select('div[data-asin][data-component-type="s-search-result"]')
        
        for product in products:
            if len(products_collected) >= 5:
                break
                
            brand_element = product.select_one('h5.s-line-clamp-1')
            if brand_element and brand_filter.lower() not in brand_element.get_text().lower():
                continue
                
            link_tag = product.select_one('a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal')
            if not link_tag or 'href' not in link_tag.attrs:
                continue
                
            product_url = link_tag['href']
            if not product_url.startswith('http'):
                product_url = f"https://www.amazon.com{product_url}"
                
            print(f"Scraping product {len(products_collected)+1}/10: {product_url}")
            product_html = get_page(product_url)
            
            if product_html:
                product_data = parse_product_page(product_html)
                if product_data['title'] and brand_filter.lower() in product_data['title'].lower():
                    # Clean price data
                    if product_data['price']:
                        product_data['price'] = product_data['price'].replace(',', '').split('.')[0]
                    products_collected.append(product_data)
                    print(f"Collected: {product_data['title']}")
                else:
                    print("Skipping non-Samsung product")
                
            time.sleep(random.uniform(5, 10))
        
        page += 1
        time.sleep(random.uniform(10, 15))
    
    save_to_file(products_collected)
    print(f"\nSuccessfully saved {len(products_collected)} products to samsung_products.txt")