#!/usr/bin/python

__title__ = "ScrapeIn - Tool to Scrape LinkedIn"
__author__ = 'Danny Chrastil'
__email__ = 'danny.chrastil@gmail.com'
__description__ = "A recon tool that allows you to scrape profile search results from LinkedIn"
__disclaimer__ = "This tool violates TOS of LinkedIn.com. For educational purposes only. Use at your own risk"
__version__ = '2.0'

import sys
import re
import time
import xlsxwriter
import json
import argparse
import requests
import subprocess
import urllib
import math
import config

from bs4 import BeautifulSoup
from thready import threaded

reload(sys)
sys.setdefaultencoding('utf-8')

""" Setup Argument Parameters """
parser = argparse.ArgumentParser(description='Discovery LinkedIn')
parser.add_argument('-u', '--keywords', help='Keywords to search')
parser.add_argument('-o', '--output', help='Output file (do not include extentions)')
args = parser.parse_args()


def linkedIn(proxies=None):
    s = requests.Session()
    html = s.get("https://www.linkedin.com/", proxies=proxies)
    soup = BeautifulSoup(html.text, "html.parser")
    csrf = soup.find(id="loginCsrfParam-login")['value']
    login_data = {
        'session_key': config.linkedin['username'],
        'session_password': config.linkedin['password'],
        'loginCsrfParam': csrf,
    }

    logged_in = s.post("https://www.linkedin.com/uas/login-submit",
                       data=login_data,
                       proxies=proxies)
    soup = BeautifulSoup(logged_in.text, "html.parser")
    cookies = s.cookies
    return cookies

def get_search(search):
    # Fetch the initial page to get results/page counts
    #url = 'https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List()&keywords=%s&origin=GLOBAL_SEARCH_HEADER&q=guided&searchId=1489295486936&start=0' % search
    #url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v-%%3EPEOPLE,facetGeoRegion-%%3Ear%%3A0)&keywords=%s&origin=FACETED_SEARCH&q=guided&start=0" % search
    url = "https://www.linkedin.com/voyager/api/search/cluster"#?count=40&guides=List(v-%%3EPEOPLE,facetGeoRegion-%%3Ear%%3A0)&keywords=%s&origin=FACETED_SEARCH&q=guided&start=0" % search
    #url = 'https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v->PEOPLE,facetCurrentCompany->31752)&origin=GLOBAL_SEARCH_HEADER&q=guided&start=0'
    #url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v->PEOPLE,facetCurrentCompany->31752)&origin=OTHER&q=guided&start=0"
    #url = 'https://www.linkedin.com/search/results/people/?facetCurrentCompany=%5B"75769"%5D'
    params = {
        'count': 40,
        'guides': 'List(v-%>PEOPLE,facetGeoRegion-%>ar%:0)',
        'keywords': search,
        'origin': 'FACETED_SEARCH',
        'q': 'guided',
        'start': 0
    }
    headers = {'Csrf-Token':'ajax:7736867257193100830'}
    cookies['JSESSIONID'] = 'ajax:7736867257193100830'
    cookies['X-RestLi-Protocol-Version'] = '2.0.0' 
    r = requests.get(url, cookies=cookies, headers=headers, params=params)
    content = json.loads(r.text)
    data_total = content['paging']['total']
    
    # Calculate pages off final results at 40 results/page
    pages = data_total / 40
    if data_total % 40 == 0:
        # Becuase we count 0... Subtract a page if there are no left over results on the last page
        pages = pages - 1 
    if pages == 0: 
        pages = 1
    
    print "[Info] %i Results Found" % data_total
    if data_total > 1000:
        pages = 24
        print "[Notice] LinkedIn only allows 1000 results. Refine keywords to capture all data"
    print "[Info] Fetching %i Pages" % pages
    print
   
    # Set record position for XLSX
    recordpos = 1

    for p in range(pages):
        # Request results for each page using the start offset
        params['start'] = p
        r = requests.get(url, cookies=cookies, headers=headers, params=params)
        content = r.text.encode('UTF-8')
        content = json.loads(content)
        print "[Info] Fetching page %i with %i results" % (p+1,len(content['elements'][0]['elements']))
        for c in content['elements'][0]['elements']:
            try:
                if c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['headless'] == False:
                    try:
                        data_industry = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['industry']
                    except:
                        data_industry = ""    
                    data_firstname = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['firstName']
                    data_lastname = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['lastName']
                    data_slug = "https://www.linkedin.com/in/%s" % c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['publicIdentifier']
                    data_occupation = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['occupation']
                    data_location = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['location']
                    try:
                        data_picture = "https://media.licdn.com/mpr/mpr/shrinknp_400_400%s" % c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['picture']['com.linkedin.voyager.common.MediaProcessorImage']['id']
                    except:
                        #print "[Notice] No picture found for %s %s, %s" % (data_firstname, data_lastname, data_occupation)
                        data_picture = ""
                    
                    # Write data to XLSX file
                    worksheet1.write('A%i' % recordpos, data_firstname)          
                    worksheet1.write('B%i' % recordpos, data_lastname)          
                    worksheet1.write('C%i' % recordpos, data_occupation)          
                    worksheet1.write('D%i' % recordpos, data_location)          
                    worksheet1.write('E%i' % recordpos, data_industry)          
                    worksheet1.write('F%i' % recordpos, data_slug)          
                    worksheet1.write('G%i' % recordpos, data_picture)          
                    worksheet2.write('A%i' % recordpos, '=IMAGE(dataset!G%i)' % recordpos)
                    worksheet2.write('B%i' % recordpos, '=dataset!A%i&" "&dataset!B%i&"\n"&dataset!C%i&"\n"&dataset!D%i&"\n"&dataset!E%i' % (recordpos,recordpos,recordpos,recordpos,recordpos))
                    worksheet2.write('C%i' % recordpos, '=HYPERLINK(dataset!F%i)' % recordpos)
                    worksheet2.set_row(recordpos-1,125)        
                    # Increment Record Position
                    recordpos = recordpos + 1
                else:
                    print "[Notice] Headless profile found. Skipping"
            except:
                print "[Notice] Skipping"
                continue
        print

def authenticate():
    try:
        cookies = linkedIn()
        print "[Info] Obtained new session: %s" % cookies['li_at']
        li_cookie = dict(li_at=cookies['li_at'])
    except KeyError as k:
        print k
        sys.exit('[Fatal] li_at cookie value not found')
    except Exception as e:
        print e
        sys.exit("[Fatal] Could not authenticate to linkedin.")
    return li_cookie

if __name__ == '__main__':
    title = """
 __                               _  _____       
/ _\ ___ _ __ __ _ _ __   ___  __| | \_   \_ __  
\ \ / __| '__/ _` | '_ \ / _ \/ _` |  / /\/ '_ \ 
_\ \ (__| | | (_| | |_) |  __/ (_| /\/ /_ | | | |
\__/\___|_|  \__,_| .__/ \___|\__,_\____/ |_| |_|
                  |_|                            
tool to scrape linkedin v2.0
"""
    print title.decode('UTF-8')
    
    # Prompt user for data variables
    search = args.keywords if args.keywords!=None else raw_input("Enter search Keywords (use quotes for more percise results)\n")
    outfile = args.output if args.output!=None else raw_input("Enter filename for output (exclude file extension)\n")
    print 
    
    # URL Encode for the querystring
    #search = urllib.quote_plus(search)
    cookies = authenticate()
    
    # Initiate XLSX File
    workbook = xlsxwriter.Workbook('results/%s.xlsx' % outfile)
    worksheet1 = workbook.add_worksheet('dataset')
    worksheet2 = workbook.add_worksheet('report')
    worksheet2.set_column(0,0, 25)
    worksheet2.set_column(1,2, 75)
    
    # Initialize Scraping
    get_search(search)

    # Close XLSD File
    workbook.close()
