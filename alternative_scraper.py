import requests
from bs4 import BeautifulSoup
import logging
import time

# Configure logging
logger = logging.getLogger(__name__)

class AlternativeScraper:
    """
    Alternative scraper implementation using requests and BeautifulSoup
    instead of Scrapy. This serves as a backup scraping mechanism.
    """
    
    def __init__(self):
        self.base_url = "https://www.zhaw.ch/"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_news(self):
        """Fetch news from ZHAW CAI website"""
        try:
            logger.info("Starting alternative scrape")
            news_items = []
            
            # Try the main CAI page first
            main_urls = [
                f'{self.base_url}en/engineering/institutes-centres/cai/',
                f'{self.base_url}en/about-us/news/'
            ]
            
            news_links = []
            for url in main_urls:
                try:
                    logger.info(f"Requesting {url}")
                    response = self.session.get(url, headers=self.headers, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all news links
                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            if '/en/about-us/news/' in href and href not in news_links:
                                news_links.append(href)
                        
                        if news_links:
                            logger.info(f"Found {len(news_links)} news links on {url}")
                            break
                    else:
                        logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                except Exception as e:
                    logger.error(f"Error fetching {url}: {str(e)}")
            
            # Process each news link
            for link in news_links[:10]:  # Limit to 10 news items
                try:
                    full_url = f"{self.base_url}{link}" if not link.startswith('http') else link
                    news_item = self._parse_news_page(full_url)
                    if news_item:
                        news_items.append(news_item)
                except Exception as e:
                    logger.error(f"Error processing news link {link}: {str(e)}")
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error in alternative scraper: {str(e)}")
            return []
    
    def _parse_news_page(self, url):
        """Parse a single news page and extract relevant information"""
        try:
            logger.info(f"Fetching news page: {url}")
            response = self.session.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = None
            title_element = soup.select_one('#main-page-title')
            if title_element:
                title = title_element.text.strip()
            else:
                title_element = soup.select_one('h1')
                if title_element:
                    title = title_element.text.strip()
            
            # Extract lead
            lead = None
            lead_element = soup.select_one('.lead')
            if lead_element:
                lead = lead_element.text.strip()
            else:
                lead_element = soup.select_one('strong')
                if lead_element:
                    lead = lead_element.text.strip()
            
            # Extract date
            date = "No date available"
            date_element = soup.select_one('.datetime time')
            if date_element:
                date = date_element.text.strip()
            
            # Extract paragraphs
            paragraphs = []
            content_element = soup.select_one('.news .clearfix')
            if content_element:
                for p in content_element.select('p, ul'):
                    paragraphs.append(str(p))
            else:
                content_element = soup.select_one('div.clearfix')
                if content_element:
                    for p in content_element.select('p'):
                        paragraphs.append(str(p))
            
            # Extract image
            image_url = "https://www.zhaw.ch/static/images/default.jpg"
            img_element = soup.select_one('.news-img-wrap img')
            if img_element and 'src' in img_element.attrs:
                src = img_element['src']
                if src.startswith('/'):
                    image_url = f"https://www.zhaw.ch{src}"
                else:
                    image_url = src
            
            if not title:
                return None
                
            return {
                'title': title,
                'lead': lead or "News from ZHAW CAI",
                'datetime': date,
                'paragraphs': paragraphs or ["<p>No content available</p>"],
                'image_url': image_url,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error parsing news page {url}: {str(e)}")
            return None
