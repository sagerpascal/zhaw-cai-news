import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy import signals
import crochet

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
            'paragraphs': response.css(".clearfix>p").getall(),
        }
        yield result


@crochet.run_in_reactor
def scrap_news():
    results = []
    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    process = CrawlerProcess(settings={
        "FEEDS": {
            "items.json": {"format": "json"},
        },
    })
    process.crawl(NewsSpider)
    process.start()

    return results

if __name__ == '__main__':
    print(scrap_news())
