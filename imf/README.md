# International Monetary Fund

Website:

https://www.imf.org/en/publications/search?when=After&series=IMF+Staff+Country+Reports#sort=relevancy&f:series=[COUNTRYREPS,ARTICLE4]

This folder contains:
1. Folders (named by report published year) contain IMF Article IV Staff Reports 
2. Python codes for Web scraping

Notes:
- The folder names are reports' published year
- The years within the file names are reports' covered year

- "imf_crawler.py" follows the following steps
	- use Selenium to get the source code for each page (filtered by year)
	- loop through pages to get the pdf download links
	- execute the download links via "get_file" function
- "region_lst" contains a dictionary of country names and their 3-letter abbreviations
