import scrapy
from scrapy.crawler import CrawlerProcess


class FacultiesAcademicsSourceSpider(scrapy.Spider):
    """crawl possible news sources from faculties & academics"""
    name = 'faculties-academics'
    start_urls = [
        'https://uwaterloo.ca/faculties-academics/',
    ]
    categories = {}

    def parse(self, response):
        for group in response.css('div.filterable-group'):
            sources = {}
            self.categories[group.css('h2.black::text').get()] = sources
            for source_item in group.css('ul li'):
                url = source_item.css('span.blocklinks a::attr(href)').get()
                if url[-1] == '/':
                    url += 'news'
                else:
                    url += '/news'
                sources[source_item.css('span.blocklinks a::text').get()] = url
        filename = './news_app/crawlers/%s' % self.name
        with open(filename, 'w') as f:
            f.write(str(self.categories))
            f.flush()


class OfficesServicesSourceSpider(scrapy.Spider):
    """crawl possible news sources from offices & services"""
    name = 'offices-services'
    start_urls = [
        'https://uwaterloo.ca/offices-services/',
    ]
    categories = {}

    def parse(self, response):
        sources = {}
        self.categories[response.css('div.uw-site--header h1::text').get()] = sources
        for source_item in response.css('li.filterable-link'):
            url = source_item.css('a::attr(href)').get()
            if url[-1] == '/':
                url += 'news'
            else:
                url += '/news'
            sources[source_item.css('a::text').get()] = url
        filename = './news_app/crawlers/%s' % self.name
        with open(filename, 'w') as f:
            f.write(str(self.categories))
            f.flush()


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(FacultiesAcademicsSourceSpider)
    process.crawl(OfficesServicesSourceSpider)
    process.start()
