# -*- coding: utf-8 -*-

# Define here the models for your scraped items
from scrapy import Item, Field


class TweetItem(Item):
    ID = Field()       # tweet id
    url = Field()      # tweet url
    datetime = Field() # post time
    text = Field()     # text content
    user_id = Field()  # user id
    
    has_image = Field() # True/False, whether a tweet contains images
    images = Field()    # a list of image urls, empty if none

    has_video = Field() # True/False, whether a tweet contains videos
    videos = Field()    # a list of video urls

    has_media = Field() # True/False, whether a tweet contains media (e.g. summary)
    medias = Field()    # a list of media


class UserItem(Item):
    ID = Field()            # user id
    name = Field()          # user name
    screen_name = Field()   # user screen name
    avatar = Field()        # avator url
    
