# -*- coding: utf-8 -*-
""" on Sat Apr  4 11:01:16 2020
https://medium.com/@kevin.a.crystal/scraping-twitter-with-tweetscraper-and-python-ea783b40443b
"""

import json
import os
tweets = []
for file in os.listdir('tweet/'):
    filename = 'tweet/' + str(file)
    if filename[7:10].isdigit():
        with open(filename, encoding='utf-8') as tweetfile:
            pyresponse = json.loads(tweetfile.read())
            tweets.append(pyresponse)
            
import pandas as pd
df = pd.DataFrame(tweets, columns=['ID','datetime','text','user_id','usernameTweet'])

df = df.replace({'\n': ' '}, regex=True) # remove linebreaks in the dataframe
df = df.replace({'\t': ' '}, regex=True) # remove tabs in the dataframe
df = df.replace({'\r': ' '}, regex=True) # remove carriage return in the dataframe

df
# Export to csv
df.to_csv("data.csv")