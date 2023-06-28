#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 21:42:15 2022

@author: zt237
"""

import numpy as np
import pandas as pd
from tqdm import tqdm
from snscrape.modules import twitter
import json



path = '/Users/zt237/Documents/'

queries = ['nasdaq']

date_from = '2021-07-05'
date_until = '2022-07-10'
lang = 'en'

max_results = 1000
save_thred = 100
col_label = ['date', 'tweetid', 'hashtags', 'content','rendered_content','username',
             'language','like_cnt','quote_cnt','reply_cnt','retweet_cnt','source_label']
tweet_lst=[]
for query in queries:

    query += " since:%s until:%s lang:%s exclude:retweets exclude:replies"%(date_from, date_until, lang)
    scraper = twitter.TwitterHashtagScraper(query)
    i = 0
    for i, tweet in enumerate(tqdm(scraper.get_items()), start = 1):
        tweet_json = json.loads(tweet.json())
        # print (f"\nScraped tweet: {tweet_json['content']}")
        
        save_lst = [tweet_json['date'], tweet_json['id'], tweet_json['hashtags'], tweet_json['content'],
                    tweet_json['renderedContent'], tweet_json['user']['username'], tweet_json['lang'], 
                    tweet_json['likeCount'], tweet_json['quoteCount'], tweet_json['replyCount'], 
                    tweet_json['retweetCount'],tweet_json['sourceLabel']]
        tweet_lst.append(save_lst)
        
        if i % save_thred == 0:
            df_tweet = pd.DataFrame(tweet_lst, columns=col_label)
            df_tweet.to_csv(path+'tweet_nasdaq.csv')
            
        if max_results and i > max_results:
            df_tweet = pd.DataFrame(tweet_lst, columns=col_label)
            df_tweet.to_csv(path+'tweet_nasdaq.csv')
            break








