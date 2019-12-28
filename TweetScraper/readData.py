from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
import logging
import pymongo
import json
import os

# for mysql



SETTINGS = get_project_settings()
connection = pymongo.MongoClient(SETTINGS['MONGODB_SERVER'], SETTINGS['MONGODB_PORT'])
db = connection[SETTINGS['MONGODB_DB']]

conversaCollection = db[SETTINGS['MONGODB_CONVERSA_COLLECTION']]
out = []
for conver in conversaCollection.find():
    context = conver['context']
    if len(context) > 3:
        for  i in context[3::-1]:
            if i['emoji']:
                out.append(context)
                break

print(len(out))
