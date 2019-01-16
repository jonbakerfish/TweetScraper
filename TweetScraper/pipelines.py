# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
from scrapy.conf import settings
import logging
import pymongo
import json
import os

# for mysql
import mysql.connector
from mysql.connector import errorcode

from TweetScraper.items import Tweet, User
from TweetScraper.utils import mkdirs


logger = logging.getLogger(__name__)

class SaveToMongoPipeline(object):

    ''' pipeline that save data to mongodb '''
    def open_spider(self, spider):
        settings = spider.settings
        connection = pymongo.MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        db = connection[settings['MONGODB_DB']]
        self.tweetCollection = db[settings['MONGODB_TWEET_COLLECTION']]
        self.userCollection = db[settings['MONGODB_USER_COLLECTION']]
        self.tweetCollection.ensure_index([('ID', pymongo.ASCENDING)], unique=True, dropDups=True)
        self.userCollection.ensure_index([('ID', pymongo.ASCENDING)], unique=True, dropDups=True)


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

        else:
            logger.info("Item type is not recognized! type = %s" %type(item))


class SavetoMySQLPipeline(object):

    ''' pipeline that save data to mysql '''
    def __init__(self):
        # connect to mysql server
        user = raw_input("MySQL User: ")
        pwd = raw_input("Password: ")
        self.cnx = mysql.connector.connect(user=user, password=pwd,
                                host='localhost',
                                database='tweets', buffered=True)
        self.cursor = self.cnx.cursor()
        self.table_name = raw_input("Table name: ")
        create_table_query =   "CREATE TABLE `" + self.table_name + "` (\
                `ID` CHAR(20) NOT NULL,\
                `url` VARCHAR(140) NOT NULL,\
                `datetime` VARCHAR(22),\
                `text` VARCHAR(280),\
                `user_id` CHAR(20) NOT NULL,\
                `usernameTweet` VARCHAR(20) NOT NULL\
                )"

        try:
            print "Creating table..."
            self.cursor.execute(create_table_query)
        except mysql.connector.Error as err:
            print err.msg
        else:
            self.cnx.commit()
            print "Successfully created table."

    def find_one(self, trait, value):
        select_query =  "SELECT " + trait + " FROM " + self.table_name + " WHERE " + trait + " = " + value + ";"
        try:
            val = self.cursor.execute(select_query)
        except mysql.connector.Error as err:
            return False
        
        if (val == None):
            return False
        else:
            return True

    def check_vals(self, item):
        ID = item['ID']
        url = item['url']
        datetime = item['datetime']
        text = item['text']
        user_id = item['user_id']
        username = item['usernameTweet']

        if (ID is None):
            return False
        elif (user_id is None):
            return False
        elif (url is None):
            return False
        elif (text is None):
            return False
        elif (username is None):
            return False
        elif (datetime is None):
            return False
        else:
            return True


    def insert_one(self, item):
        ret = self.check_vals(item)

        if not ret:
            return None

        ID = item['ID']
        user_id = item['user_id']
        url = item['url']
        text = item['text']
        username = item['usernameTweet']
        datetime = item['datetime']

        insert_query =  "INSERT INTO " + self.table_name + " (ID, url, datetime, text, user_id, usernameTweet )"
        insert_query += " VALUES ( '" + ID + "', '" + url + "', '"
        insert_query += datetime + "', '" + text + "', '" + user_id + "', '" + username + "' )"

        try:
            print "Inserting..."
            self.cursor.execute(insert_query)
        except mysql.connector.Error as err:
            print err.msg
        else:
            print "Successfully inserted."
            self.cnx.commit()


    def process_item(self, item, spider):
        if isinstance(item, Tweet):
            dbItem = self.find_one('user_id', item['ID'])
            if dbItem:
                pass # simply skip existing items
                ### or you can update the tweet, if you don't want to skip:
                # dbItem.update(dict(item))
                # self.tweetCollection.save(dbItem)
                # logger.info("Update tweet:%s"%dbItem['url'])
            else:
                self.insert_one(dict(item))
                logger.debug("Add tweet:%s" %item['url'])


class SaveToFilePipeline(object):
    ''' pipeline that save data to disk '''
    def open_spider(self, spider):
        settings = spider.settings
        self.saveTweetPath = settings['SAVE_TWEET_PATH']
        self.saveUserPath = settings['SAVE_USER_PATH']
        mkdirs(self.saveTweetPath) # ensure the path exists
        mkdirs(self.saveUserPath)


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

        else:
            logger.info("Item type is not recognized! type = %s" %type(item))


    def save_to_file(self, item, fname):
        ''' input: 
                item - a dict like object
                fname - where to save
        '''
        with open(fname,'w') as f:
            json.dump(dict(item), f)
