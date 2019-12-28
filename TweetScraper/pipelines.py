# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
import logging
import pymongo
import json
import os


from TweetScraper.items import Tweet, User, Conversa
from TweetScraper.utils import mkdirs

SETTINGS = get_project_settings()

logger = logging.getLogger(__name__)

class SaveToMongoPipeline(object):

    ''' pipeline that save data to mongodb '''
    def __init__(self):
        connection = pymongo.MongoClient(SETTINGS['MONGODB_SERVER'], SETTINGS['MONGODB_PORT'])
        db = connection[SETTINGS['MONGODB_DB']]
        self.tweetCollection = db[SETTINGS['MONGODB_TWEET_COLLECTION']]
        self.userCollection = db[SETTINGS['MONGODB_USER_COLLECTION']]
        self.conversaCollection = db[SETTINGS['MONGODB_CONVERSA_COLLECTION']]
        '''self.tweetCollection.ensure_index([('_id', pymongo.ASCENDING)], unique=True, dropDups=True)
        self.userCollection.ensure_index([('_id', pymongo.ASCENDING)], unique=True, dropDups=True)
        self.conversaCollection.ensure_index([('_id', pymongo.ASCENDING)], unique=True, dropDups=True)'''

    def process_item(self, item, spider):
        if isinstance(item, Tweet):
            dbItem = self.tweetCollection.find_one({'ID': item['ID']})
            if dbItem:
                pass # simply skip existing items
                ### or you can update the tweet, if you don't want to skip:
                # dbItem.update(dict(item))
                # self.tweetCollection.save(dbItem)
                # logger.info("Update tweet:%s"%dbItem['url'])
            else:
                self.tweetCollection.insert_one(dict(item))
                logger.debug("Add tweet:%s" %item['url'])

        elif isinstance(item, User):
            dbItem = self.userCollection.find_one({'ID': item['ID']})
            if dbItem:
                pass # simply skip existing items
                ### or you can update the user, if you don't want to skip:
                # dbItem.update(dict(item))
                # self.userCollection.save(dbItem)
                # logger.info("Update user:%s"%dbItem['screen_name'])
            else:
                self.userCollection.insert_one(dict(item))
                logger.debug("Add user:%s" %item['screen_name'])
        elif isinstance(item,Conversa):
            dbItem = self.conversaCollection.find_one({'ID': item['ID']})
            if dbItem:
                pass
            else:
                self.conversaCollection.insert_one(dict(item))
                logger.debug("Add conversa:%s" %item)
        else:
            logger.info("Item type is not recognized! type = %s" %type(item))



class SaveToFilePipeline(object):
    ''' pipeline that save data to disk '''
    def __init__(self):
        self.saveTweetPath = SETTINGS['SAVE_TWEET_PATH']
        self.saveUserPath = SETTINGS['SAVE_USER_PATH']
        self.saveConversaFile = SETTINGS['SAVE_CONVERSA_FILE']
        mkdirs(self.saveTweetPath) # ensure the path exists
        mkdirs(self.saveUserPath)

    def open_spider(self, spider):
        self.conversafile = open(self.saveConversaFile,'a', encoding='utf-8')
    def close_spider(self, spider):
        self.conversafile.close()
    def process_item(self, item, spider):
        if isinstance(item, Tweet):
            savePath = os.path.join(self.saveTweetPath, item['ID'])
            if os.path.isfile(savePath):
                pass # simply skip existing items
                ### or you can rewrite the file, if you don't want to skip:
                # self.save_to_file(item,savePath)
                # logger.info("Update tweet:%s"%dbItem['url'])
            else:
                self.save_to_file(item,savePath)
                logger.debug("Add tweet:%s" %item['url'])

        elif isinstance(item, User):
            savePath = os.path.join(self.saveUserPath, item['ID'])
            if os.path.isfile(savePath):
                pass # simply skip existing items
                ### or you can rewrite the file, if you don't want to skip:
                # self.save_to_file(item,savePath)
                # logger.info("Update user:%s"%dbItem['screen_name'])
            else:
                self.save_to_file(item, savePath)
                logger.debug("Add user:%s" %item['screen_name'])
        elif isinstance(item,Conversa):
            if  len(item['context'])>3:
                self.save_to_file(item)
            else:
                pass

        else:
            logger.info("Item type is not recognized! type = %s" %type(item))


    def save_to_file(self, item):
        ''' input: 
                item - a dict like object
                fname - where to save
        '''
        
        out = { 'context':[dict(a) for a in item['context']]}
        out['tweet_id'] = str(item['tweet_id'])
        out['ID'] = item['ID']
        self.conversafile.write(json.dumps(out,ensure_ascii=False)+'\n')
            
