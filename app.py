# Make sure reactor selection happens before any other imports
import os
# Set environment variable to use the correct reactor
os.environ["SCRAPY_REACTOR"] = "twisted.internet.selectreactor.SelectReactor"

# Standard library imports
import time
import logging
import threading
import uuid
import traceback
from pathlib import Path

# Set up crochet correctly - MUST BE BEFORE OTHER IMPORTS!
import crochet
crochet.setup()

# Then import Flask and other libraries
from flask import Flask, send_file, render_template, send_from_directory, jsonify, request
import scrapy
from scrapy.crawler import CrawlerRunner
from alternative_scraper import AlternativeScraper
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create global state management
class NewsManager:
    def __init__(self):
        self.news = []
        self.scrape_in_progress = False
        self.scrape_complete = False
        self.crawl_runner = CrawlerRunner()
        self.last_update_time = None
    
    def clear_news(self):
        self.news = []
        
    def is_empty(self):
        return len(self.news) == 0
        
    def reset_state(self):
        self.scrape_in_progress = False
        self.scrape_complete = False

    def add_dummy_news(self):
        """Add dummy news item for testing"""
        self.news.append({
            'title': 'Test News Article',
            'lead': 'This is a test article to verify the display functionality',
            'datetime': 'January 1, 2023',
            'paragraphs': ['<p>This is a test paragraph 1.</p>', '<p>This is a test paragraph 2.</p>'],
            'image_url': 'https://www.zhaw.ch/storage/hochschule/medien/news/2023/230511-ki-regulierung-campus-week.jpg',
            'url': 'https://www.zhaw.ch/en/about-us/news/news/detail/event-news/how-should-ai-be-regulated/'
        })
        self.scrape_complete = True
        self.scrape_in_progress = False
        self.last_update_time = time.time()
        logger.info("Added dummy news item")

# Initialize news manager and app AFTER crochet setup
news_manager = NewsManager()
app = Flask(__name__)
app.secret_key = "HU71GHjh87zggjh7H867DF564d"

# Create a crawler runner with specific settings to avoid reactor issues
crawl_runner = CrawlerRunner({
    'TWISTED_REACTOR': 'twisted.internet.selectreactor.SelectReactor',
    'DOWNLOAD_TIMEOUT': 15,  # Set a reasonable timeout
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})
news_manager.crawl_runner = crawl_runner

class NewsSpider(scrapy.Spider):
    name = "zhaw-news-spider"
    base_url = "https://www.zhaw.ch/"

    def start_requests(self):
        logger.info(f"Starting NewsSpider requests")
        # Try the direct news listing URL instead
        urls = [
            f'{self.base_url}en/engineering/institutes-centres/cai/',  # Main CAI page
        ]
        for url in urls:
            logger.info(f"Requesting page: {url}")
            yield scrapy.Request(url=url, callback=self.parse_main, errback=self.handle_error)

    def handle_error(self, failure):
        logger.error(f"Request failed: {failure}")
        return None

    def parse_main(self, response):
        logger.info(f"Parsing main page: {response.url}")
        
        # Look for news items in the zhaw-newswall
        news_links = []
        
        # Find all tiles with class "tile image news News"
        news_tiles = response.css('div.zhaw-newswall div.tile.image.news')
        logger.info(f"Found {len(news_tiles)} news tiles in newswall")
        
        for tile in news_tiles:
            # Check if the tile has "newswall-label news" (not "newswall-label social")
            label_type = tile.css('div.newswall-label::attr(class)').get()
            if label_type and 'social' not in label_type:
                # Extract the href from the anchor tag
                href = tile.css('a::attr(href)').get()
                if href:
                    news_links.append(href)
                    logger.info(f"Found news link: {href}")
        
        if not news_links:
            logger.warning(f"No news links found on {response.url}. Check CSS selector.")
            # Fallback selector in case the structure has changed
            alt_news_links = response.css('a[href*="news"]').getall()
            logger.info(f"Alternative selector found {len(alt_news_links)} links")
            
        for url in news_links:
            full_url = f'{self.base_url}{url.lstrip("/")}' if not url.startswith('http') else url
            logger.info(f"Requesting news page: {full_url}")
            yield scrapy.Request(url=full_url, callback=self.parse)

    def parse(self, response):
        try:
            logger.info(f"Parsing news page: {response.url}")
            
            title = response.css("#main-page-title::text").get()
            if not title:
                title = response.css("h1::text").get()  # Fallback selector
                
            lead = response.css(".lead::text").get()
            if not lead:
                lead = response.css("strong::text").get()  # Fallback selector
                
            datetime = response.css(".datetime>time::text").get()
            if not datetime:
                datetime = "No date available"  # Default value
                
            # Updated selector based on the actual HTML structure
            paragraphs = response.css(".news.news-single .article .frame-type-text p").getall()
            if not paragraphs:
                # Try the old selectors as fallbacks
                paragraphs = response.css(".news .clearfix>p, .news .clearfix>ul").getall()
                
            img_tag = response.css(".news-img-wrap img").get()
            image_url = "https://www.zhaw.ch/static/images/default.jpg"  # Default image
            
            if img_tag:
                try:
                    image_url = "https://www.zhaw.ch" + img_tag.split('src=')[1].split('\"')[1]
                except IndexError:
                    logger.warning(f"Could not parse image URL from: {img_tag}")
            
            if title:  # As long as we have a title, create a news item
                result = {
                    'title': ' '.join((title or "").replace("\n", "").split()),
                    'lead': ' '.join((lead or "News from ZHAW CAI").replace("\n", "").split()),
                    'datetime': ' '.join((datetime or "").replace("\n", "").split()),
                    'paragraphs': paragraphs or ["<p>No content available</p>"],
                    'image_url': image_url,
                    'url': response.url
                }
                self.news_.append(result)
                logger.info(f"Successfully parsed news item: {result['title']}")
            else:
                logger.warning(f"Missing title in page: {response.url}")
        except Exception as e:
            logger.error(f"Error parsing {response.url}: {str(e)}", exc_info=True)


def merge_paragraphs(paragraphs):
    result = ' '.join(paragraphs)
    return result


@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json', mimetype='application/manifest+json')


@app.route('/service-worker.js')
def serve_service_worker():
    return send_file('service-worker.js', mimetype='application/javascript')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(Path('static') / "images", "favicon.ico", mimetype='image/vnd.microsoft.icon')


@app.route('/crawl')
def crawl_for_quotes():
    if news_manager.scrape_in_progress:
        return jsonify(status='SCRAPE IN PROGRESS')
    
    if news_manager.scrape_complete and not news_manager.is_empty():
        return jsonify(status='SCRAPE COMPLETE', news_count=len(news_manager.news))
    
    # Start a new scrape
    news_manager.scrape_in_progress = True
    news_manager.scrape_complete = False
    news_manager.clear_news()
    
    try:
        # Use crochet to run the spider in the background
        scrape_with_crochet(news_manager.news)
        return jsonify(status='SCRAPING STARTED')
    except Exception as e:
        news_manager.reset_state()
        logger.error(f"Error starting scrape: {str(e)}")
        return jsonify(status='ERROR', message=str(e)), 500


@app.route('/status')
def status():
    """Debug endpoint to check the status of news fetching"""
    return jsonify({
        'scrape_in_progress': news_manager.scrape_in_progress,
        'scrape_complete': news_manager.scrape_complete,
        'news_count': len(news_manager.news),
        'last_update': news_manager.last_update_time
    })


@app.route('/force_reset')
def force_reset():
    """Force reset the scraping state and trigger a new scrape"""
    news_manager.reset_state()
    news_manager.clear_news()
    
    # Start a new scrape
    news_manager.scrape_in_progress = True
    scrape_with_crochet(news_manager.news)
    
    return jsonify({
        'status': 'Reset triggered, new scrape started',
        'time': time.time()
    })


@app.route('/test_dummy_news')
def add_test_news():
    """Add dummy news for testing"""
    news_manager.add_dummy_news()
    return jsonify({
        'status': 'Added dummy news',
        'news_count': len(news_manager.news),
    })


@app.route('/direct_scrape')
def direct_scrape():
    """Directly run the spider without using crochet for debugging"""
    try:
        logger.info("Direct scrape attempt")
        news_manager.clear_news()
        news_manager.scrape_in_progress = True
        
        # Use a unique job ID
        job_id = str(uuid.uuid4())
        
        try:
            @crochet.wait_for(timeout=60.0)
            def run_spider():
                logger.info("Running spider directly")
                return crawl_runner.crawl(NewsSpider, news_=news_manager.news)
                
            run_spider()
            
            # Check if we got any news
            if len(news_manager.news) == 0:
                logger.warning("Direct scrape completed but no news found!")
                # Add a dummy news item as fallback
                news_manager.add_dummy_news()
                return jsonify(status="Scrape completed but no news found, added dummy news")
            else:
                news_manager.scrape_complete = True
                news_manager.scrape_in_progress = False
                news_manager.last_update_time = time.time()
                return jsonify(status="Scrape completed successfully", news_count=len(news_manager.news))
        except crochet.TimeoutError:
            logger.error("Scrape timed out")
            news_manager.reset_state()
            news_manager.add_dummy_news()
            return jsonify(status="Scrape timed out, added dummy news"), 500
            
    except Exception as e:
        logger.error(f"Error in direct scrape: {str(e)}")
        logger.error(traceback.format_exc())
        news_manager.reset_state()
        # Add a dummy news item so the site is usable
        news_manager.add_dummy_news()
        return jsonify(status="Error, added dummy news", error=str(e)), 500


@crochet.run_in_reactor
def scrape_with_crochet(_list):
    try:
        logger.info("Starting spider with crochet")
        # This returns a Deferred, which we attach a callback to
        deferred = crawl_runner.crawl(NewsSpider, news_=_list)
        deferred.addCallback(finished_scrape)
        deferred.addErrback(handle_scrape_error)
        return deferred
    except Exception as e:
        logger.error(f"Error in scrape_with_crochet: {str(e)}", exc_info=True)
        news_manager.reset_state()
        # Add a dummy news item so the site is usable
        news_manager.add_dummy_news()


def finished_scrape(result):
    logger.info(f"Scraping completed, found {len(news_manager.news)} news items")
    if len(news_manager.news) == 0:
        logger.warning("No news items were found during scraping!")
    news_manager.scrape_complete = True
    news_manager.scrape_in_progress = False
    news_manager.last_update_time = time.time()
    return result


def handle_scrape_error(failure):
    logger.error(f"Scraping error: {failure}")
    news_manager.reset_state()
    return failure


@app.route('/')
def main():
    # Check if meeting rooms should be displayed via URL parameter
    show_rooms = request.args.get('rooms', 'false').lower() == 'true'
    
    if news_manager.is_empty():
        if not news_manager.scrape_in_progress:
            # Start a scrape if none is in progress and we have no news
            logger.info("Starting scrape from main route handler")
            news_manager.scrape_in_progress = True
            try:
                scrape_with_crochet(news_manager.news)
            except Exception as e:
                logger.error(f"Error starting scrape from main route: {str(e)}")
                # Add a dummy news item so there's something to display
                news_manager.add_dummy_news()
                return render_template('index.html',
                                      title=news_manager.news[0]['title'],
                                      paragraphs=merge_paragraphs(news_manager.news[0]['paragraphs']),
                                      datetime=news_manager.news[0]['datetime'],
                                      lead=news_manager.news[0]['lead'],
                                      image_url=news_manager.news[0]['image_url'],
                                      news_id=0,
                                      total_news=1,
                                      show_rooms=show_rooms,
                                      room1_name=os.environ.get('ROOM1_NAME', 'Meeting Room 1'),
                                      room2_name=os.environ.get('ROOM2_NAME', 'Meeting Room 2'))
        return render_template('loading.html', message="Loading news, please wait...")
    
    # Display the first news item
    selected_news = news_manager.news[0]
    logger.info(f"Rendering index with news item: {selected_news['title']}")
    return render_template('index.html', 
                          title=selected_news['title'],
                          paragraphs=merge_paragraphs(selected_news['paragraphs']),
                          datetime=selected_news['datetime'],
                          lead=selected_news['lead'],
                          image_url=selected_news['image_url'],
                          news_id=0,
                          total_news=len(news_manager.news),
                          show_rooms=show_rooms,
                          room1_name=os.environ.get('ROOM1_NAME', 'Meeting Room 1'),
                          room2_name=os.environ.get('ROOM2_NAME', 'Meeting Room 2'))


@app.route('/next_news/<int:news_id>')
def get_next(news_id):
    if news_manager.is_empty():
        return jsonify(error="No news available"), 404
    
    selected_news = news_manager.news[news_id % len(news_manager.news)]
    return jsonify(title=selected_news['title'],
                   paragraphs=merge_paragraphs(selected_news['paragraphs']),
                   datetime=selected_news['datetime'],
                   lead=selected_news['lead'],
                   image_url=selected_news['image_url'],
                   news_id=news_id % len(news_manager.news),
                   total_news=len(news_manager.news))


@app.route('/alternative_scrape')
def alternative_scrape():
    """Use the alternative scraper instead of Scrapy"""
    try:
        logger.info("Starting alternative scrape")
        news_manager.clear_news()
        
        # Create and use the alternative scraper
        alt_scraper = AlternativeScraper()
        fetched_news = alt_scraper.fetch_news()
        
        if fetched_news:
            news_manager.news = fetched_news
            news_manager.scrape_complete = True
            news_manager.scrape_in_progress = False
            news_manager.last_update_time = time.time()
            logger.info(f"Alternative scrape completed successfully with {len(fetched_news)} items")
            return jsonify(status="Alternative scrape completed", news_count=len(fetched_news))
        else:
            logger.warning("Alternative scrape returned no results")
            news_manager.add_dummy_news()
            return jsonify(status="Alternative scrape found no news, added dummy news")
    except Exception as e:
        logger.error(f"Error in alternative scrape: {str(e)}")
        news_manager.reset_state()
        news_manager.add_dummy_news()
        return jsonify(status="Error in alternative scrape, added dummy news", error=str(e))


# Microsoft Graph API configuration
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
# These should be stored in environment variables in production
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# Meeting room email addresses
MEETING_ROOMS = {
    'room1': os.environ.get('ROOM1_EMAIL', 'meetingroom1@yourdomain.com'),
    'room2': os.environ.get('ROOM2_EMAIL', 'meetingroom2@yourdomain.com')
}

def get_access_token():
    """Get access token for Microsoft Graph API"""
    token_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}")
        return None

def get_room_calendar(room_email, access_token):
    """Fetch calendar events for a specific room for today"""
    if not access_token:
        return []
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Get today's date range
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Format dates for Graph API
    start_datetime = today_start.strftime('%Y-%m-%dT%H:%M:%S')
    end_datetime = today_end.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Query calendar view
    calendar_url = f"{GRAPH_API_ENDPOINT}/users/{room_email}/calendarView"
    params = {
        'startDateTime': start_datetime,
        'endDateTime': end_datetime,
        '$select': 'subject,start,end,organizer,isAllDay',
        '$orderby': 'start/dateTime'
    }
    
    try:
        response = requests.get(calendar_url, headers=headers, params=params)
        response.raise_for_status()
        events = response.json().get('value', [])
        
        # Process events to simplify data
        processed_events = []
        for event in events:
            processed_events.append({
                'subject': event.get('subject', 'No Subject'),
                'start': event['start']['dateTime'],
                'end': event['end']['dateTime'],
                'organizer': event.get('organizer', {}).get('emailAddress', {}).get('name', 'Unknown'),
                'isAllDay': event.get('isAllDay', False)
            })
        
        return processed_events
    except Exception as e:
        logger.error(f"Error fetching calendar for {room_email}: {str(e)}")
        return []

@app.route('/api/room-calendar/<room_id>')
def get_room_calendar_api(room_id):
    """API endpoint to fetch room calendar data"""
    if room_id not in MEETING_ROOMS:
        return jsonify(error="Invalid room ID"), 404
    
    room_email = MEETING_ROOMS[room_id]
    access_token = get_access_token()
    
    if not access_token:
        return jsonify(error="Failed to authenticate with Microsoft Graph API"), 500
    
    events = get_room_calendar(room_email, access_token)
    return jsonify(events=events, room_email=room_email)


def periodic_update():
    """Schedule periodic updates of the news data"""
    try:
        # Only start a new scrape if we're not currently scraping
        if not news_manager.scrape_in_progress:
            logger.info("Starting scheduled update")
            news_manager.clear_news()
            news_manager.scrape_in_progress = True
            scrape_with_crochet(news_manager.news)
    except Exception as e:
        logger.error(f"Error in periodic update: {str(e)}")
        news_manager.reset_state()
    finally:
        # Schedule the next update
        threading.Timer(3600, periodic_update).start()  # update content every hour


def initialize_app():
    """Initialize the application by starting the scraper"""
    logger.info("Initializing app and starting first scrape")
    try:
        # First add a dummy news item to ensure the site works
        news_manager.add_dummy_news()
        
        # Then try to scrape real news
        news_manager.scrape_in_progress = True
        scrape_with_crochet(news_manager.news)
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        news_manager.reset_state()


if __name__ == '__main__':
    # Initialize the app
    initialize_app()
    
    # Start the periodic update timer
    threading.Timer(3600, periodic_update).start()  # update content every hour
    
    # Run the Flask app
    app.run('0.0.0.0', 5000, debug=True)  # Enable debug mode for better error reporting
