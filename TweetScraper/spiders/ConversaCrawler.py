from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy import http
from scrapy.shell import inspect_response  # for debugging
from scrapy.utils.project import get_project_settings
import re
import json
import time
import logging
import pymongo
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import CloseSpider
from functools import partial
import os
from bson.objectid import ObjectId
SETTINGS = get_project_settings()
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from datetime import datetime
import subprocess
from TweetScraper.items import Tweet, User,Conversa

logger = logging.getLogger(__name__)

class ConversaScraper(CrawlSpider):
    name = 'ConversaScraper'
    allowed_domains = ['twitter.com']
    
    def __init__(self):
        self.count =0
        self.i = 0
        self.url = "https://twitter.com%s"
        connection = pymongo.MongoClient(SETTINGS['MONGODB_SERVER'], SETTINGS['MONGODB_PORT'])
        db = connection[SETTINGS['MONGODB_DB']]
        self.tweetCollection = db[SETTINGS['MONGODB_TWEET_COLLECTION']]
        self.conversaCollection = db[SETTINGS['MONGODB_CONVERSA_COLLECTION']]
        '''self.tweetCollection.ensure_index([('_id', pymongo.ASCENDING)], unique=True, dropDups=True)
        self.conversaCollection.ensure_index([('_id', pymongo.ASCENDING)], unique=True, dropDups=True)'''
        start_tweet = list(self.conversaCollection.find().sort('tweet_id',pymongo.DESCENDING).limit(1))
        self.end_tweet_id = list(self.tweetCollection.find().sort('_id',pymongo.DESCENDING).limit(1))[0]['_id']
        self.start_tweet_id = start_tweet[0]['tweet_id'] if start_tweet else list(self.tweetCollection.find().sort('_id',pymongo.ASCENDING).limit(1))[0]['_id']
        if os.path.exists(SETTINGS['SAVE_CONVERSA_FILE']):
            with open(SETTINGS['SAVE_CONVERSA_FILE'],'rt') as f:
                end=self.tail(f,1)
            self.start_tweet_id = max(ObjectId(json.loads(end[0])['tweet_id']),self.start_tweet_id)      
    def parse_page(self,tweet,response):
        def parse_tweet_item(items):
            for item in items:
                
                tweet = Tweet()

                tweet['usernameTweet'] = item.xpath('.//span[@class="username u-dir u-textTruncate"]/b/text()').extract()[0]
                tweet['lang'] = item.xpath('.//@lang').get()
                if tweet['lang'] not in {'en','und'}:
                    raise NameError('not support lang')
                ID = item.xpath('.//@data-tweet-id').extract()
                if not ID:
                    raise NameError('no ID')
                tweet['ID'] = ID[0]

                ### get text content
                tweet['text'] = ' '.join(
                    item.xpath('.//div[@class="js-tweet-text-container"]/p//text()|.//div[@class="js-tweet-text-container"]/p//img/@alt').extract()).replace(' # ',
                                                                                                        '#').replace(
                    ' @ ', '@')
                tweet['emoji'] = ' '.join(
                    item.xpath('.//div[@class="js-tweet-text-container"]/p//img/@alt').extract())
                if tweet['text'] == '':
                    # If there is not text, we ignore the tweet
                    raise NameError('empty text')

                ### get meta data
                tweet['url'] = item.xpath('.//@data-permalink-path').extract()[0]

                '''nbr_retweet = item.css('span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount').xpath(
                    '@data-tweet-stat-count').extract()
                if nbr_retweet:
                    tweet['nbr_retweet'] = int(nbr_retweet[0])
                else:
                    tweet['nbr_retweet'] = 0

                nbr_favorite = item.css('span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount').xpath(
                    '@data-tweet-stat-count').extract()
                if nbr_favorite:
                    tweet['nbr_favorite'] = int(nbr_favorite[0])
                else:
                    tweet['nbr_favorite'] = 0

                nbr_reply = item.css('span.ProfileTweet-action--reply > span.ProfileTweet-actionCount').xpath(
                    '@data-tweet-stat-count').extract()
                if nbr_reply:
                    tweet['nbr_reply'] = int(nbr_reply[0])
                else:
                    tweet['nbr_reply'] = 0'''

                tweet['datetime'] = datetime.fromtimestamp(int(
                    item.xpath('.//small[@class="time"]/a/span/@data-time').extract()[
                        0])).strftime('%Y-%m-%d %H:%M:%S')

                ### get photo
                has_cards = item.xpath('.//@data-card-type').extract()
                if has_cards and has_cards[0] == 'photo':
                    tweet['has_image'] = True
                    tweet['images'] = item.xpath('.//*/div/@data-image-url').extract()
                elif has_cards:
                    logger.debug('Not handle "data-card-type":\n%s' % item.xpath('.').extract()[0])

                ### get animated_gif
                has_cards = item.xpath('.//@data-card2-type').extract()
                if has_cards:
                    if has_cards[0] == 'animated_gif':
                        tweet['has_video'] = True
                        tweet['videos'] = item.xpath('.//*/source/@video-src').extract()
                    elif has_cards[0] == 'player':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'summary_large_image':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'amplify':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'summary':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == '__entity_video':
                        pass  # TODO
                        # tweet['has_media'] = True
                        # tweet['medias'] = item.xpath('.//*/div/@data-src').extract()
                    else:  # there are many other types of card2 !!!!
                        logger.debug('Not handle "data-card2-type":\n%s' % item.xpath('.').extract()[0])

                is_reply = item.xpath('.//div[@class="ReplyingToContextBelowAuthor"]').extract()
                tweet['is_reply'] = is_reply != []
                if  tweet['is_reply']: tweet['reply_to'] = item.xpath('.//div[@class="ReplyingToContextBelowAuthor"]//@href|.//div[@class="ReplyingToContextBelowAuthor"]//@data-user-id').extract() 
                #href uid
                is_retweet = item.xpath('.//span[@class="js-retweet-text"]').extract()
                tweet['is_retweet'] = is_retweet != []

                tweet['user_id'] = item.xpath('.//@data-user-id').extract()[0]
                yield tweet

        
        
        
        html_page = response.body.decode("utf-8")
        page = Selector(text=html_page)

        
        con = Conversa()
        #ids = set(page.xpath('.//div[contains(@class,"js-stream-tweet") and @data-conversation-id]/@data-conversation-id').extract())
        #去掉转推等， 出现两个twitter 文的对话
        ids = set(page.xpath('.//div[@data-conversation-id]/@data-conversation-id').extract())
        if len(ids) != 1:
            return 
        else :
            con['ID'] = ids.pop()
        ancestors = page.xpath('.//div[@id="ancestors"]')
        items = ancestors.xpath('.//div[@data-conversation-id=%s]'%con['ID'])
        #这是被删掉的twitter的数量
        delItiem = len(list(ancestors.xpath('.//div[@class="stream-tombstone-container ThreadedConversation-tweet last"]')))
        #过滤小于3轮的对话
        if len(items) >= 3: 
            self.i+=1
            if delItiem>0:self.count+=1
        if len(items) < 3 and delItiem > 0 :return 
        try:
            con['context'] = list(parse_tweet_item(items))
            originTweet = page.xpath('.//div[@data-tweet-id=%s]'%tweet['ID'])
            originTweet = list(parse_tweet_item(originTweet))[0]
        except:
            return
        con['tweet_id'] = tweet['_id']
        con['context'].append(originTweet)
        
        return con



    def tail(self,f, lines=1, _buffer=4096):
        """Tail a file and get X lines from the end"""
        # place holder for the lines found
        lines_found = []

        # block counter will be multiplied by buffer
        # to get the block size from the end
        block_counter = -1

        # loop until we find X lines
        while len(lines_found) < lines:
            try:
                f.seek(block_counter * _buffer, os.SEEK_END)
            except IOError:  # either file is too small, or too many lines requested
                f.seek(0)
                lines_found = f.readlines()
                break

            lines_found = f.readlines()

            # we found enough lines, get out
            # Removed this line because it was redundant the while will catch
            # it, I left it for history
            # if len(lines_found) > lines:
            #    break

            # decrement the block counter to get the
            # next X bytes
            block_counter -= 1

        return lines_found[-lines:]
    def start_requests(self):
          
        while True: 
            for tweet in self.tweetCollection.find({ '_id':{'$gt':self.start_tweet_id}}).sort('_id',pymongo.ASCENDING).limit(1000):
                url = self.url % tweet['url']
                self.start_tweet_id = tweet['_id']
                parse_page = partial(self.parse_page,tweet)
                yield http.Request(url,callback=parse_page)
        
    def spider_closed(self, spider):
        print('Closing {} spider'.format(spider.name))

        