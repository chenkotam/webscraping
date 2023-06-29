#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 16:56:33 2022

@author: zt237
"""

import requests
import json
import time
import numpy as np
import pandas as pd
from tqdm import tqdm

class Adviser_Crawler:
    """
    example:
    adviserid_lst = [2894737]
    url_extend = '?hl=true&includePrevious=true&nrows=12&query=john&r=25&sort=bc_lastname_sort+asc,bc_firstname_sort+asc,bc_middlename_sort+asc,score+desc&wt=json'
    instance=Adviser_Crawler()
    instance.get_text(adviserid)
    
    """
    def __init__(self):
        self.headers = {'Origin': "https://adviserinfo.sec.gov",
           'Referer': 'https://adviserinfo.sec.gov/',
           'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
           'Accept':"application/json, text/plain, */*"
}
    
    def get_text(self,adviserid_lst,url_extend=''):
        df = pd.DataFrame()
        for adv_idx, adviserid in enumerate(tqdm(adviserid_lst)):
            url = 'https://api.adviserinfo.sec.gov/search/individual/'+str(adviserid)+url_extend
            response = requests.get(url, headers = self.headers)
            text = response.text
            dict_text = json.loads(text)
            adv_json = json.loads(dict_text['hits']['hits'][0]['_source']['iacontent']) # unpack dict
            
            # format as dataframe
            disc_cnt = len(adv_json['disclosures'])
            data = {'individualid':             disc_cnt*[adv_json['basicInformation']['individualId']],
                    'firstname':                disc_cnt*[adv_json['basicInformation']['firstName']],
                    'middlename':               disc_cnt*[adv_json['basicInformation']['middleName']],
                    'lastname':                 disc_cnt*[adv_json['basicInformation']['lastName']],
                    'disclosure_count':         disc_cnt*[disc_cnt],
                    'event_date':               [adv_json['disclosures'][i]['eventDate'] for i in range(disc_cnt)],
                    'disclosure_type':          [adv_json['disclosures'][i]['disclosureType'] for i in range(disc_cnt)],
                    'disclosure_resolution':    [adv_json['disclosures'][i]['disclosureResolution'] for i in range(disc_cnt)]
                    }
            
            # if allegation exist, record it, if not, leave as blank
            settle_lst = []
            allegation_lst = []
            for i in range(disc_cnt):
                try: settle_lst.append(adv_json['disclosures'][i]['disclosureDetail']['Settlement Amount'])
                except: settle_lst.append('')
                try: allegation_lst.append(adv_json['disclosures'][i]['disclosureDetail']['Allegations'])
                except: allegation_lst.append('')
            data['settle_amount'] = settle_lst
            data['allegations'] = allegation_lst
            

            df_curr = pd.DataFrame(data)
            df = pd.concat((df,df_curr),axis=0)
            
            # to prevent anti-scraping
            if adv_idx%10 == 9:
                time.sleep(5)
                
        return df
 

if __name__ == "__main__":
    adviserid_lst = [2894737,2874074,2874143,2874155]
    # url_extend = '?hl=true&includePrevious=true&nrows=12&query=john&r=25&sort=bc_lastname_sort+asc,bc_firstname_sort+asc,bc_middlename_sort+asc,score+desc&wt=json'
    instance=Adviser_Crawler()
    df=instance.get_text(adviserid_lst)



        
        