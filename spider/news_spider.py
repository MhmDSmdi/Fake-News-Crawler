import json
import random
import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from datetime import timedelta

class NewsHolder(scrapy.Item):
    title = scrapy.Field()
    body = scrapy.Field()
    snippet = scrapy.Field()
    link = scrapy.Field()
    date = scrapy.Field()
    agency = scrapy.Field()


class FreeText(scrapy.Item):
    texts = scrapy.Field()
    url = scrapy.Field()


class NewsSpider(scrapy.Spider):
    name = 'news-spider'
    custom_settings = {
        'FEED_URI': './news.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_FIELDS': None,
        'ITEM_PIPELINES': {
            'spider.pipelines.TextProcessingPipeline': 300,
            # 'spider.pipelines.MongoPipeline': 400,
        }
    }
    config = json.loads(open('./archive_news_agency_structure.json', 'r').read())

    def __init__(self, agency, page=None, date_from=None, date_to=None, format='%Y%m%d', *args, **kwargs):
        self.custom_settings['FEED_URI'] = './{}.csv'.format(agency)
        super(NewsSpider, self).__init__(*args, **kwargs)
        self.agency = self.config[agency]
        self.agency_name = agency
        self.page = page
        self.date_from = datetime.strptime(date_from, format)
        self.date_to = datetime.strptime(date_to, format)

    def start_requests(self):
        url_placeholder = self.agency['base_url'] + self.agency['attributes']
        start_date = self.date_from
        while start_date < self.date_to:
            # TODO Day interval
            start_date += timedelta(days=10)
            yield scrapy.Request(url=url_placeholder.format(page_index=1, year=start_date.year, month=start_date.month,
                                                            day=start_date.day), callback=self.parse)

    def parse(self, response, **kwargs):
        LINK_SELECTOR = self.agency['archive']['links']
        link_list = response.xpath(LINK_SELECTOR).extract()
        # TODO global size of news per day
        link_list = random.sample(link_list, 5)
        for link in link_list:
            url = self.agency['base_url'] + link
            yield scrapy.Request(url, callback=self.parse_article, meta={"news_url": url})

        # NEXT_PAGE_SELECTOR = self.agency['archive']['next-page']
        # next_page = response.xpath(NEXT_PAGE_SELECTOR).extract_first()
        # if next_page:
        #     yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    # Load articles details from main page
    def parse_article(self, response, **kwargs):
        TITLE_SELECTOR = self.agency['article']['title']
        SNIPPET_SELECTOR = self.agency['article']['snippet']
        BODY_SELECTOR = self.agency['article']['body']
        DATE_SELECTOR = self.agency['article']['date']
        news = NewsHolder()
        news['title'] = ' '.join(response.xpath(TITLE_SELECTOR).extract())
        news['body'] = ' '.join(response.xpath(BODY_SELECTOR).extract())
        news['snippet'] = ' '.join(response.xpath(SNIPPET_SELECTOR).extract())
        news['link'] = response.meta.get("news_url")
        news['date'] = ' '.join(response.xpath(DATE_SELECTOR).extract())
        news['agency'] = self.agency_name
        yield news


class ParagraphSpider(scrapy.Spider):
    name = 'paragraph-spider'
    custom_settings = {
        'FEED_URI': './texts.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_FIELDS': None,
        'ITEM_PIPELINES': {
            'spider.pipelines.ParagraphProcessingPipeline': 300,
        }
    }
    start_urls = []

    def __init__(self, start_links, *args, **kwargs):
        super(ParagraphSpider, self).__init__(*args, **kwargs)
        self.start_urls = start_links

    def parse(self, response, **kwargs):
        extracted_texts = FreeText()
        p_selectors = response.xpath("//*[self::span or self::p]")
        text = ''
        for selector in p_selectors:
            p = selector.xpath('string(./text())').extract()
            for item in p:
                text += item
        extracted_texts['texts'] = text
        extracted_texts['url'] = str(response.request.url)
        yield extracted_texts


def do_crawl(spider_name, agency_name=None, links=None, start_date='13990101', end_date='13990112'):
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })
    if spider_name == 'news-spider':
        process.crawl(NewsSpider, agency=agency_name, date_from=start_date, date_to=end_date)
    elif spider_name == 'paragraph-spider':
        process.crawl(ParagraphSpider, links)
    process.start()


if __name__ == '__main__':
    config = json.loads(open('./archive_news_agency_structure.json', 'r').read())
    link = ['https://www.isna.ir/news/99100603625/%D8%AC%D9%86%D8%AC%D8%A7%D9%84%DB%8C-%D8%AA%D8%B1%DB%8C%D9%86-%D8%AA%D8%BA%DB%8C%DB%8C%D8%B1%D8%A7%D8%AA-%DA%A9%D8%AA%D8%A7%D8%A8-%D9%87%D8%A7%DB%8C-%D8%AF%D8%B1%D8%B3%DB%8C']
    # do_crawl(spider_name='news-spider', agency_name=list(config.keys())[3], start_date='13880701', end_date='13990615')
    do_crawl(spider_name='paragraph-spider', links=link)