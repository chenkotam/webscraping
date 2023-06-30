# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 15:43:30 2023

@author: Zhenhao Tan
Notes: 
- It seems like they have an API for data but we want to get the download 
link for the pdf files (they probably don't have this in the API). 
- The json data returned from the request is different from the source we've 
seen on the website. This could because everytime we request from the url, it 
will link to their API and the API may return data in a different order, or 
with different formatting or structure
- This script simply use selenium to sidestep this
"""

import os
import re
import requests
import json
import time
import numpy as np
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from region_lst import *

class IMF_Crawler:
    """
    example:
    instance = IMF_Crawler()
    instance.get_link(datefrom=2015, dateto=2016)
    instance.get_file(path, rename=False, inabbr=False)
    
    """
    def __init__(self):
        self.result_perpage = 50 # selected from 10, 20, 50
        self.url = 'https://www.imf.org/en/publications/search?when=After&series=IMF+Staff+Country+Reports#'
        self.seriesfilter = 'sort=relevancy&numberOfResults=%d&f:series=[COUNTRYREPS]' % (self.result_perpage)
        self.pdflinkclass = 'CoveoResultLink imf-result-item__file-download imf-result-item__file-download--pdf'
        self.blockclass = 'coveo-list-layout CoveoResult'
        self.ctryclass = 'CoveoResultLink'
        self.pagenumclass = 'coveo-pager-list-item coveo-accessible-button'
        self.region_dict = get_region_lst()
        
    def wait_driver(self, driver):
        delay = 60 # seconds
        try:
            myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.coveo-highlight')))
            time.sleep(3)  # Wait for an additional 5 seconds
            print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")
            
    def get_abbr(self, region_name):
        # Look up the abbreviation for a region name
        abbreviation = region_name
        for abbr, name in self.region_dict.items():
            if name in region_name:
                abbreviation = abbr
                break
        return abbreviation


    def get_link(self, datefrom, dateto):
        # Set up Selenium WebDriver
        driver = webdriver.Chrome('chromedriver')
        
        # Get report download links by year
        self.dl_links_all = {}
        self.filenames_all = {}
        self.reportyear_all = {}
        self.hidden_file = []
        self.noyeardetect = []
        for yr in tqdm(range(datefrom,dateto+1)):
            # Find number of pages
            # URL: Basic url + seriesfilter + datefilter
            url_curr = self.url + self.seriesfilter + '&DateTo=12%2F31%2F'+str(yr)+'&DateFrom=1%2F1%2F'+str(yr) 
            driver.get(url_curr)
            self.wait_driver(driver) # Wait for the page to load completely
            soup = BeautifulSoup(driver.page_source, 'html.parser') # Parse the HTML with BeautifulSoup
            # pages = soup.find_all('li', {'class': self.pagenumclass}) # Find total number of page
            pages = int(np.ceil(float(soup.find_all('span', {'class': 'coveo-highlight'})[-1].text) / self.result_perpage))

            # Find the elements to extract (in each page)
            dl_links = []
            filenames = []
            reportyear = []
            for p in range(pages):
                # URL: Basic url + pagefilter + seriesfilter + datefilter
                url_curr = self.url + 'first=%d&'%(p*self.result_perpage) + self.seriesfilter + '&DateTo=12%2F31%2F'+str(yr)+'&DateFrom=1%2F1%2F'+str(yr) # Basic url + seriesfilter + datefilter
                driver.get(url_curr)
                self.wait_driver(driver) # Wait for the page to load completely
                soup = BeautifulSoup(driver.page_source, 'html.parser') # Parse the HTML with BeautifulSoup
                
                # Extract the links and names
                blocks = soup.find_all('div', {'class': self.blockclass})
                for block in blocks:
                    
                    # Get title and filter those contain "Article IV"
                    title = block.find('a', {'class': self.ctryclass, 'data-title-template': "${title}"})['title']
                    subclass = block.find('span', {'class': 'imf-eyebrow'}).text.replace(" ","")
                    if subclass not in ['StaffCountryreports', 'ArticleIVStaffReports']:
                        continue
                    if "article iv" not in str.lower(title): # Only wants Article IV reports
                        continue
                    
                    # Get country names and covered year from titles
                    year_pattern = r'20\d{2}' # regular expression pattern to match the year
                    filename_curr = re.split(year_pattern, title)[0].replace(':','').replace(' ','_')
                    if filename_curr[-1] == '_':
                        filename_curr = filename_curr[:-1]
                    
                    # To handle those titles without year
                    try:
                        reportyear_curr = re.findall(year_pattern, title)[0]
                    except:
                        self.noyeardetect.append(filename_curr)
                        print('Title without year detected -> Published year: %d' % (yr))
                        continue

                    # To handle those blocks without download link in the front page
                    try:
                        dl_links.append(block.find('a', {'class': self.pdflinkclass})['href'])
                        filenames.append(filename_curr)
                        reportyear.append(reportyear_curr)
                    except:
                        self.hidden_file.append([filename_curr, reportyear_curr])
                        print('File Hidden -> Country Name: %s, Published year: %d, Covered year: %s' % (filename_curr, yr, reportyear_curr))
                        continue
                

            # Save the links into a dict by year
            self.dl_links_all[str(yr)] = dl_links
            self.filenames_all[str(yr)] = filenames
            self.reportyear_all[str(yr)] = reportyear # There could be 2 different years' reports, but reported in the same year
        
        # Close the browser
        driver.quit()
    
    
    def get_file(self, path, rename = False, inabbr = False):
        # Loop through all years
        for yr in self.dl_links_all.keys():
            print(yr)
            download_path = path + '\\' + yr
            
            # Create a dictionary of ChromeOptions to specify the download directory
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": download_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })        
            
            # Create a new instance of the Chrome driver with the ChromeOptions
            driver = webdriver.Chrome(options=chrome_options)
        
            # Create the folder if it doesn't exist
            if not os.path.exists(os.path.join(path, yr)):
                os.makedirs(os.path.join(path, yr))
                time.sleep(3) # Give some time to create folder
        
            # Loop through all download links within each key
            filename_last = ''
            for idx, file in enumerate(tqdm(self.dl_links_all[yr])):
                # Navigate to the webpage where the file is located
                driver.get(file)
                
                if rename:
                    # Get the name of the latest downloaded file
                    while True:
                        try:
                            filename_curr = max([download_path + "\\" + f for f in os.listdir(download_path)],key=os.path.getctime)
                        except:
                            continue
                        if len(filename_curr)>0:
                            break

                    # If downloads haven't started, wait and retry
                    while filename_curr==filename_last:
                        time.sleep(3)
                        filename_curr = max([download_path + "\\" + f for f in os.listdir(download_path)],key=os.path.getctime)

                    # If downloads haven't finished (temp file), wait and retry
                    size_last = 0
                    while True:
                        filename_curr = max([download_path + "\\" + f for f in os.listdir(download_path)],key=os.path.getctime)
                        size = os.path.getsize(filename_curr)
                        if size != size_last:
                            size_last = size
                            time.sleep(0.5)
                        elif '.tmp' in filename_curr or '.crdownload' in filename_curr:
                            time.sleep(0.5)
                        else:
                            size_last = 0
                            break


                    # Rename the latest downloaded file
                    if inabbr:
                        filename_new = os.path.join(download_path, r"%s_%s.pdf" % (self.reportyear_all[yr][idx], self.get_abbr(self.filenames_all[yr][idx])))
                    else:
                        filename_new = os.path.join(download_path, r"%s_%s.pdf" % (self.reportyear_all[yr][idx], self.filenames_all[yr][idx]))

                    if os.path.exists(filename_new):
                        os.remove(filename_new)
                        os.rename(filename_curr, filename_new)
                    else:
                        os.rename(filename_curr, filename_new)
                    
                    filename_last = filename_curr
 
            # Close the browser
            time.sleep(5) # provide extra time for file to be downloaded
            driver.quit()

if __name__ == "__main__":
    path = r"C:\Users\zt237\Dropbox\Xuran_Joe\Biodiversity\Datasets\IMF_v2"
    instance = IMF_Crawler()
    instance.get_link(datefrom=2023, dateto=2023)
    instance.get_file(path, rename=True, inabbr=True)
    
    # Check the list of hidden files
    instance.hidden_file
    instance.noyeardetect
    
    
    