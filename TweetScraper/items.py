from scrapy import Item, Field


class Tweet(Item):
    id_ = Field()
    raw_data = Field()

class User(Item):
    id_ = Field()
    raw_data = Field()

class Conversation(Item):
    id_ = Field()
    raw_data = Field()

