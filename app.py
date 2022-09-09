import time

import crochet

crochet.setup()

import threading
from flask import Flask
from flask import render_template
import scrapy
from scrapy.crawler import CrawlerRunner
from flask import send_from_directory
from pathlib import Path

# CODE FROM https://github.com/notoriousno/scrapy-flask


app = Flask(__name__)
app.secret_key = "HU71GHjh87zggjh7H867DF564d"

crawl_runner = CrawlerRunner()
news = []
scrape_in_progress = False
scrape_complete = False


class NewsSpider(scrapy.Spider):
    name = "zhaw-news-spider"
    base_url = "https://www.zhaw.ch/"

    def start_requests(self):
        for url in [f'{self.base_url}en/engineering/institutes-centres/cai/']:
            yield scrapy.Request(url=url, callback=self.parse_main)

    def parse_main(self, response):
        news_links = response.css('a[href*="/en/about-us/news/"]').getall()
        news_links = [l[len("<a href=\""):].split("\">")[0] for l in news_links]
        for url in news_links:
            yield scrapy.Request(url=f'{self.base_url}{url}', callback=self.parse)

    def parse(self, response):
        result = {
            'title': ' '.join(response.css("#main-page-title::text").get().replace("\n", "").split()),
            'lead': ' '.join(response.css(".lead::text").get().replace("\n", "").split()),
            'datetime': ' '.join(response.css(".datetime>time::text").get().replace("\n", "").split()),
            # 'paragraphs': response.css(".clearfix>p").getall(),
            'paragraphs': response.css(".news .clearfix>p, .news .clearfix>ul").getall(),
            'image_url': "https://www.zhaw.ch" + response.css(".news-img-wrap img").get().split('src=')[1].split('\"')[
                1],
        }
        self.news_.append(result)


def merge_paragraphs(paragraphs):
    result = ' '.join(paragraphs)
    return result


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(Path('static') / "images", "favicon.ico", mimetype='image/vnd.microsoft.icon')


@app.route('/crawl')
def crawl_for_quotes():
    global scrape_in_progress
    global scrape_complete

    if not scrape_in_progress:
        scrape_in_progress = True
        global news
        scrape_with_crochet(news)
        return 'SCRAPING'
    elif scrape_complete:
        return 'SCRAPE COMPLETE'
    return 'SCRAPE IN PROGRESS'


@crochet.run_in_reactor
def scrape_with_crochet(_list):
    eventual = crawl_runner.crawl(NewsSpider, news_=_list)
    eventual.addCallback(finished_scrape)


def finished_scrape(null):
    global scrape_complete
    scrape_complete = True


@app.route('/')
def hello_world():
    global scrape_complete
    if scrape_complete:
        selected_news = news[0]

        return render_template('index.html', title=selected_news['title'],
                               paragraphs=merge_paragraphs(selected_news['paragraphs']),
                               datetime=selected_news['datetime'],
                               lead=selected_news['lead'],
                               image_url=selected_news['image_url'])
    return 'Scrape Still Progress -> call with /crawl'


@app.route('/next_news/<int:news_id>')
def get_next(news_id):
    selected_news = news[news_id % len(news)]
    return dict(title=selected_news['title'],
                paragraphs=merge_paragraphs(selected_news['paragraphs']),
                datetime=selected_news['datetime'],
                lead=selected_news['lead'],
                image_url=selected_news['image_url'])


def periodic_update():
    scrape_with_crochet(news)
    threading.Timer(3600, periodic_update).start()  # update content every hour


periodic_update()
while not scrape_complete:
    time.sleep(5)

if __name__ == '__main__':
    app.run('0.0.0.0', 5000)
