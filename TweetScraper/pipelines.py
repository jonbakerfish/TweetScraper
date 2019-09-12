# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
import logging
import pymongo
import json
import os

# for mysql
import mysql.connector
from mysql.connector import errorcode

from TweetScraper.items import Tweet, User
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
        self.cnx = mysql.connector.connect(
            user=SETTINGS["MYSQL_USER"],
            password=SETTINGS["MYSQL_PWD"],
            host=SETTINGS["MYSQL_SERVER"],
            database=SETTINGS["MYSQL_DB"],
            buffered=True)
        self.cursor = self.cnx.cursor()
        self.table_name = SETTINGS["MYSQL_TABLE"]
        create_table_query =   "CREATE TABLE `" + self.table_name + "` (\
                `ID` CHAR(20) NOT NULL,\
                `url` VARCHAR(140) NOT NULL,\
                `datetime` VARCHAR(22),\
                `text` VARCHAR(280),\
                `user_id` CHAR(20) NOT NULL,\
                `usernameTweet` VARCHAR(20) NOT NULL\
                )"

        try:
            self.cursor.execute(create_table_query)
        except mysql.connector.Error as err:
            logger.info(err.msg)
        else:
            self.cnx.commit()

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

        insert_query =  'INSERT INTO ' + self.table_name + ' (ID, url, datetime, text, user_id, usernameTweet )'
        insert_query += ' VALUES ( %s, %s, %s, %s, %s, %s)'
        insert_query += ' ON DUPLICATE KEY UPDATE'
        insert_query += ' url = %s, datetime = %s, text= %s, user_id = %s, usernameTweet = %s'

        try:
            self.cursor.execute(insert_query, (
                ID,
                url,
                datetime,
                text,
                user_id,
                username,
                url,
                datetime,
                text,
                user_id,
                username
                ))
        except mysql.connector.Error as err:
            logger.info(err.msg)
        else:
            self.cnx.commit()

    def process_item(self, item, spider):
        if isinstance(item, Tweet):
           self.insert_one(dict(item))  # Item is inserted or updated.
           logger.debug("Add tweet:%s" %item['url'])


class SaveToFilePipeline(object):
    ''' pipeline that save data to disk '''
    def __init__(self):
        self.saveTweetPath = SETTINGS['SAVE_TWEET_PATH']
        self.saveUserPath = SETTINGS['SAVE_USER_PATH']
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
        with open(fname,'w', encoding='utf-8') as f:
            json.dump(dict(item), f, ensure_ascii=False)
