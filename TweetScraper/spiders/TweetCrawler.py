from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.conf import settings
from scrapy import http
from scrapy.shell import inspect_response  # for debugging
import re
import json
import time
import logging
import urllib
import urlparse

from TweetScraper.items import TweetItem, UserItem


logger = logging.getLogger(__name__)

class TweetScraper(CrawlSpider):
    name = 'TweetScraper'
    allowed_domains = ['twitter.com']

    def __init__(self, queries=''):
        self.queries = queries.split(',')
        self.reScrollCursor = re.compile(r'data-min-position="([^"]+?)"')
        self.reRefreshCursor = re.compile(r'data-refresh-cursor="([^"]+?)"')


    def start_requests(self):
        # generate request: https://twitter.com/search?q=[xxx] for each query
        for query in self.queries:
            url = 'https://twitter.com/search?q=%s' %urllib.quote_plus(query)
            yield http.Request(url, callback=self.parse_search_page)


    def parse_search_page(self, response):
        # handle current page
        for item in self.parse_tweets_block(response.body):
            yield item

        # get next page
        tmp = self.reScrollCursor.search(response.body)
        if tmp:
            query = urlparse.parse_qs(urlparse.urlparse(response.request.url).query)['q'][0]
            scroll_cursor = tmp.group(1)
            url = 'https://twitter.com/i/search/timeline?q=%s&' \
                  'include_available_features=1&include_entities=1&max_position=%s' % \
                  (urllib.quote_plus(query), scroll_cursor)
            yield http.Request(url, callback=self.parse_more_page)

        # TODO: # get refresh page
        # tmp = self.reRefreshCursor.search(response.body)
        # if tmp:
        #     query = urlparse.parse_qs(urlparse.urlparse(response.request.url).query)['q'][0]
        #     refresh_cursor=tmp.group(1)


    def parse_more_page(self, response):
        # inspect_response(response)
        # handle current page
        data = json.loads(response.body)
        for item in self.parse_tweets_block(data['items_html']):
            yield item

        # get next page
        query = urlparse.parse_qs(urlparse.urlparse(response.request.url).query)['q'][0]
        min_position = data['min_position']
        url = 'https://twitter.com/i/search/timeline?q=%s&' \
              'include_available_features=1&include_entities=1&max_position=%s' % \
               (urllib.quote_plus(query), min_position)
        yield http.Request(url, callback=self.parse_more_page)


    def parse_tweets_block(self, html_page):
        page = Selector(text=html_page)

        ### for tweets with media
        items = page.xpath('//li[@data-item-type="tweet"]/ol[@role="presentation"]/li[@role="presentation"]/div')
        for item in self.parse_tweet_item(items):
            yield item

        ### for text only tweets
        items = page.xpath('//li[@data-item-type="tweet"]/div') 
        for item in self.parse_tweet_item(items):
            yield item


    def parse_tweet_item(self, items):
        for item in items:
            logger.debug("Show tweet:\n%s"%item.xpath('.').extract()[0])
            try:
                tweetItem = TweetItem()
                userItem = UserItem()

                ID = item.xpath('.//@data-tweet-id').extract()
                if not ID:
                    continue
                tweetItem['ID'] = ID[0]
                ### get text content
                tweetItem['text'] = '\n'.join(item.xpath('.//div[@class="content"]/p').xpath('.//.').extract())
                if tweetItem['text'] == '':
                    continue #skip no <p> tweet

                ### get meta data
                tweetItem['url'] = item.xpath('.//@data-permalink-path').extract()[0]
                tweetItem['datetime'] = \
                    item.xpath(
                        './/div[@class="content"]/div[@class="stream-item-header"]/small[@class="time"]/a/span/@data-time').extract()[0]

                ### get photo
                has_cards = item.xpath('.//@data-card-type').extract()
                if has_cards and has_cards[0] == 'photo':
                    tweetItem['has_image'] = True
                    tweetItem['images'] = item.xpath('.//*/div/@data-image-url').extract()
                elif has_cards:
                    logger.debug('Not handle "data-card-type":\n%s'%item.xpath('.').extract()[0])

                ### get animated_gif
                has_cards = item.xpath('.//@data-card2-type').extract()
                if has_cards:
                    if has_cards[0] == 'animated_gif':
                        tweetItem['has_video'] = True
                        tweetItem['videos'] = item.xpath('.//*/source/@video-src').extract()
                    elif has_cards[0] == 'player':
                        tweetItem['has_media'] = True
                        tweetItem['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'summary_large_image':
                        tweetItem['has_media'] = True
                        tweetItem['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'amplify':
                        tweetItem['has_media'] = True
                        tweetItem['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'summary':
                        tweetItem['has_media'] = True
                        tweetItem['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == '__entity_video':
                        pass # TODO
                        # tweetItem['has_media'] = True
                        # tweetItem['medias'] = item.xpath('.//*/div/@data-src').extract()
                    else: # there are many other types of card2 !!!!
                        logger.debug('Not handle "data-card2-type":\n%s'%item.xpath('.').extract()[0])

                ### get user info
                tweetItem['user_id'] = item.xpath('.//@data-user-id').extract()[0]
                userItem['ID'] = tweetItem['user_id']
                userItem['name'] = item.xpath('.//@data-name').extract()[0]
                userItem['screen_name'] = item.xpath('.//@data-screen-name').extract()[0]
                userItem['avatar'] = \
                    item.xpath('.//div[@class="content"]/div[@class="stream-item-header"]/a/img/@src').extract()[0]

                yield tweetItem
                yield userItem
            except:
                logger.error("Error tweet:\n%s"%item.xpath('.').extract()[0])
                # raise

    def extract_one(self, selector, xpath, default=None):
        extracted = selector.xpath(xpath).extract()
        if extracted:
            return extracted[0]
        return default
