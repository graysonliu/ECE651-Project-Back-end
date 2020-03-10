import os
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import logging
import re


class NewsLatestSpider(scrapy.Spider):
    """crawl news from sources"""
    name = 'news_latest'
    start_urls = []
    custom_settings = {
        'DOWNLOAD_DELAY': 60,
        'LOG_ENABLED': False
    }
    url_pref = 'https://uwaterloo.ca'

    # add root directory to sys.path so that we can use models
    abs_path = os.path.abspath(sys.argv[0])
    path_split = abs_path.rsplit('/', 3)
    sys.path.append(path_split[0])
    from news_app.models import NewsSource

    engine = create_engine("mysql+pymysql://root:root@localhost:3306/ece651")
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    sources = session.query(NewsSource).filter_by(uw_style=1)

    url_id_dict = {}
    for source in sources:
        url_id_dict[source.url] = source.id
        start_urls.append(source.url)

    # logging
    logger = logging.getLogger('log')
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler('news_latest.log', mode='w')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def parse(self, response):
        redirect_urls = response.request.meta.get('redirect_urls')  # redirect might happen
        if redirect_urls:
            original_url = redirect_urls[0]
        else:
            original_url = response.url
        self.logger.info(original_url)
        if response.css('div.view-empty'):
            return
        else:
            content_list = response.css('div.content_node')
            for content in content_list:
                try:
                    date = content.css('span.date-display-single::attr(content)').get()[:10]
                    url = self.url_pref + content.css('h2 a::attr(href)').get()
                    title = content.css('h2 a::text').get()
                    image_url = content.css('div.field-type-image div div::attr(resource)').get()
                    abstract = content.css('div.field-type-text-with-summary div div *').get()
                    if abstract:
                        abstract = re.sub(r'<[^<>]*>', '', abstract).strip()  # replace all HTML tag
                        abstract = re.sub(r'(\s)+', ' ', abstract)  # combine whitespace

                    from news_app.models import News
                    news = News(url=url, source_id=self.url_id_dict[original_url], title=title, abstract=abstract,
                                date=date, image_url=image_url)
                    self.session.add(news)
                    self.session.commit()
                except IntegrityError as e:
                    self.session.rollback()
                    sql_message = e.__getattribute__('_sql_message')
                    if 'Duplicate' in sql_message and 'PRIMARY' in sql_message:
                        pass
                    else:
                        self.logger.error(e.__class__.__name__, exc_info=True)
                except Exception as e:
                    self.session.rollback()
                    self.logger.error(e.__class__.__name__, exc_info=True)


if __name__ == '__main__':
    process = CrawlerProcess()


    def _crawl(result, spider):
        deferred = process.crawl(spider)
        deferred.addCallback(_crawl, spider)
        return deferred


    _crawl(None, NewsLatestSpider)
    process.start()
