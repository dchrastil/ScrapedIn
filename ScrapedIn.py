#!/usr/bin/python

__title__ = "ScrapeIn - Tool to Scrape LinkedIn"
__author__ = '(disk0nn3ct) Danny Chrastil'
__email__ = 'danny.chrastil@gmail.com'
__description__ = "A recon tool that allows you to scrape profile search results from LinkedIn"
__disclaimer__ = "This tool violates TOS of LinkedIn.com. For educational purposes only. Use at your own risk"
__version__ = '4.0'

import os
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
from thready import threaded
from termcolor import colored

""" Setup Argument Parameters """
parser = argparse.ArgumentParser(description='Discovery LinkedIn')
args = parser.parse_args()

def get_search():
    # Fetch the initial page to get results/page counts
    url = "https://www.linkedin.com/voyager/api/graphql?variables=(start:0,origin:FACETED_SEARCH,query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List(%s)),(key:resultType,value:List(PEOPLE)),(key:title,value:List(%s))),includeFiltersInResponse:false))&queryId=voyagerSearchDashClusters.994bf4e7d2173b92ccdb5935710c3c5d" % (company, search)
    headers = {'Csrf-Token':'ajax:3972979001005769271'}
    headers['X-RestLi-Protocol-Version'] = '2.0.0' 
    cookies['JSESSIONID'] = 'ajax:3972979001005769271'
    
    r = requests.get(url, cookies=cookies, headers=headers)
    content = json.loads(r.text)
    data_total = content['data']['searchDashClustersByAll']['metadata']['totalResultCount']
    
    # Calculate pages off final results at 40 results/page
    pages = math.ceil(data_total / 50)
    if data_total % 50 == 0:
        pages = pages - 1 
    if pages == 0: 
        pages = 1
    
    print(colored("[Info] ","green"), colored("%i Results Found" % data_total,"white"))
    if data_total > 1000:
        pages = 19
        print(colored("[Notice]","yellow"), colored("LinkedIn only allows 1000 results. Refine keywords to capture all data","white"))
    
    print(colored("[Info] ","green"), colored("Fetching %i Pages" % pages,"white"))
   
    # Set record position for XLSX
    recordpos = 1

    for p in range(pages):
        # Request results for each page using the start offset
        url = "https://www.linkedin.com/voyager/api/graphql?variables=(start:%s,count:50,origin:FACETED_SEARCH,query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List(%s)),(key:resultType,value:List(PEOPLE)),(key:title,value:List(%s))),includeFiltersInResponse:false))&queryId=voyagerSearchDashClusters.994bf4e7d2173b92ccdb5935710c3c5d" % (str(p*50), company, search)
        r = requests.get(url, cookies=cookies, headers=headers)
        content = r.text.encode('UTF-8')
        content = json.loads(content)
        try:
            content = content['data']['searchDashClustersByAll']['elements'][1]['items']
        except:
            content = content['data']['searchDashClustersByAll']['elements'][0]['items']

        print(colored("[Info] ","green"), colored("Fetching page %s/%s with %s results" % (p+1,pages,len(content)),"white"))
        
        for c in content:
            cc = c['item']['entityResult']
            if cc['entityCustomTrackingInfo']['memberDistance'] != 'OUT_OF_NETWORK':
                data_memberid = cc['trackingUrn']
                data_title = cc['title']['text'].split(" ")
                data_firstname = data_title[0]
                try:
                    data_lastname = data_title[1]
                except:
                    data_lastname = ""
                data_slug = cc['navigationUrl']
                try:
                    data_occupation = cc['primarySubtitle']['text']
                except:
                    data_occupation = ""
                try:
                    data_location = cc['secondarySubtitle']['text']
                except:
                    data_location = ""
                try:
                    data_picture = cc['image']['attributes'][0]['detailData']['nonEntityProfilePicture']['vectorImage']['artifacts'][0]['fileIdentifyingUrlPathSegment']
                except:
                    data_picture = ""
                    #print("[Notice] No picture found for %s %s, %s" % (data_firstname, data_lastname, data_occupation))
               
                # Formulate Email Address    
                if email != None:
                    emailaddress = email.replace("{first}",data_firstname)
                    emailaddress = emailaddress.replace("{last}",data_lastname)
                    emailaddress = emailaddress.replace("{f}",data_firstname[0:1])
                    emailaddress = emailaddress.replace("{l}",data_lastname[0:1])
                    emailaddress = emailaddress.lower()
                    data_email = emailaddress
                    
               #     url = "https://www.linkedin.com/sales/gmail/profile/viewByEmail/%s" % emailaddress    
               #     r = requests.get(url, cookies=cookies, headers=headers)
               #     emailresp = r.text.encode('UTF-8')
               #     regex = data_memberid
               #     m = re.findall(regex, emailresp, re.MULTILINE)
               #     if m:
               #         data_email = emailaddress
               #         print(colored("[Update] ", "blue"), colored("Matched email: %s" % emailaddress, "white"))

                # Write data to XLSX file
                worksheet1.write('A%i' % recordpos, data_firstname)          
                worksheet1.write('B%i' % recordpos, data_lastname)          
                worksheet1.write('C%i' % recordpos, data_occupation)          
                worksheet1.write('D%i' % recordpos, data_location)          
                worksheet1.write('E%i' % recordpos, data_email)          
                worksheet1.write('F%i' % recordpos, data_slug)
                worksheet1.write('G%i' % recordpos, data_picture)          
                worksheet2.write('A%i' % recordpos, '=IMAGE(dataset!G%i)' % recordpos)
                worksheet2.write('B%i' % recordpos, '=dataset!A%i&" "&dataset!B%i&"\n"&dataset!C%i&"\n"&dataset!D%i&"\n"&dataset!E%i&"\n"&HYPERLINK(dataset!F%i)' % (recordpos, recordpos,recordpos,recordpos,recordpos,recordpos))
                worksheet2.set_row(recordpos-1,125)        
                # Increment Record Position
                recordpos = recordpos + 1
            else:
                try:
                    data_occupation = cc['primarySubtitle']['text']
                except:
                    data_occupation = ""
                print(colored("[Notice] ","yellow"), colored("Profile outside your network (%s). Skipping" % data_occupation,"white"))
            
            #print("[Notice] Profile error. Skipping")
        
        if config.timeout > 0:
            time.sleep(config.timeout)

    print(colored("[Info] ","green"), colored("Scan complete!","white"))

def companyLookup(company):
    url = "https://www.linkedin.com/voyager/api/graphql?variables=(start:0,origin:GLOBAL_SEARCH_HEADER,query:(keywords:%s,flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:resultType,value:List(COMPANIES))),includeFiltersInResponse:false))&queryId=voyagerSearchDashClusters.1f5ea36a42fc3319f534af1022b6dd64" % company
    headers = {'Csrf-Token':'ajax:3972979001005769271'}
    headers['X-RestLi-Protocol-Version'] = '2.0.0' 
    cookies['JSESSIONID'] = 'ajax:3972979001005769271'
    r = requests.get(url, cookies=cookies, headers=headers)
    content = r.text.encode('UTF-8')
    content = r.text
    content = json.loads(content)
    print(colored("\n[Info] ","green"), colored("Found the following companies:","white")) 
    count = 0
    for c in content['data']['searchDashClustersByAll']['elements'][1]['items']:
        if c['item']['entityResult']['title']['text']:
            c = c['item']['entityResult']
            count = count + 1
            print("  %s (#%s)" % ("- " + c['title']['text'], colored(c['trackingUrn'].replace('urn:li:company:',''),"yellow")))

def profileLookupID(userslug):
    url = "https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity=%s&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-35" % userslug
    headers = {'Csrf-Token':'ajax:3972979001005769271'}
    headers['X-RestLi-Protocol-Version'] = '2.0.0' 
    cookies['JSESSIONID'] = 'ajax:3972979001005769271'
    r = requests.get(url, cookies=cookies, headers=headers)
    profresp = r.text.encode('UTF-8')
    profresp = json.loads(profresp)
    
    # Extract Basic Profile Info
    print(colored("\n[Info] ","green"), colored("Gathering Basic Profile Information...","white")) 
    data_companies = []
    data_skills = []
    data_schools = []
    data_network = []
    data_connections = []
    data_urn = profresp['elements'][0]['objectUrn']
    data_fname = profresp['elements'][0]['firstName']
    data_lname = profresp['elements'][0]['lastName']
    data_location = profresp['elements'][0]['locationName']
    data_industry = profresp['elements'][0]['industry']['name']
    data_headline = profresp['elements'][0]['headline']
    for d in profresp['elements'][0]['profilePositionGroups']['elements']:
        data_companies.append("%s" % d['companyName'])
    for d in profresp['elements'][0]['profileEducations']['elements']:
        data_schools.append("%s" % d['schoolName'])
    
    # Guess Profile Email Address
    print(colored("[Info] ","green"), colored("Attempting to Extract Profile Email Address...","white")) 
    emails = []
    emails.append("%s.%s@gmail.com" % (data_fname,data_lname))
    emails.append("%s%s@gmail.com" % (data_fname[:1],data_lname))
    for eg in emails:
        data_email = profileValidateEmail(data_urn,eg.lower())
        if data_email:
            print(colored("[Update] ", "blue"), colored("Matched email: %s" % data_email, "white"))
            break
    
    # Collect ALL profile skills
    print(colored("[Info] ","green"), colored("Gathering Relevant Profile's Network...","white")) 
    url = "https://www.linkedin.com/voyager/api/identity/profiles/%s/skillCategory?includeHiddenEndorsers=true" % userslug
    headers = {'Csrf-Token':'ajax:3972979001005769271'}
    headers['X-RestLi-Protocol-Version'] = '2.0.0' 
    cookies['JSESSIONID'] = 'ajax:3972979001005769271'
    r = requests.get(url, cookies=cookies, headers=headers)
    skillresp = r.text.encode('UTF-8')
    skillresp = json.loads(skillresp)
    for e in skillresp['elements']:
        for s in e['endorsedSkills']:
            data_skills.append("%s (%s)" % (s['skill']['name'], s['endorsementCount']))
            sguid = s['skill']['entityUrn'].split(',')[0].replace('urn:li:fs_skill:(','')
            sid = s['skill']['entityUrn'].split(',')[1][:-1]
            url = "https://www.linkedin.com/voyager/api/identity/profiles/%s/endorsements?count=100&includeHidden=true&pagingStart=0&q=findEndorsementsBySkillId&skillId=%s" % (sguid,sid)
            headers = {'Csrf-Token':'ajax:3972979001005769271'}
            headers['X-RestLi-Protocol-Version'] = '2.0.0' 
            cookies['JSESSIONID'] = 'ajax:3972979001005769271'
            r = requests.get(url, cookies=cookies, headers=headers)
            endresp = r.text.encode('UTF-8')
            endresp = json.loads(endresp)
            for p in endresp['elements']:
                data_network.append("%s %s (%s)" % (p['endorser']['miniProfile']['firstName'],p['endorser']['miniProfile']['lastName'],p['endorser']['miniProfile']['occupation']))
            # Remove Duplicate Connections
            for p in data_network:
                if p not in data_connections:
                    data_connections.append(p)

    # Write Profile Report
    pout = "\n====================================================================\n"
    pout = pout + "%s %s (%s)\n" % (data_fname, data_lname, data_headline) 
    pout = pout + "====================================================================\n"
    pout = pout + "\n"
    pout = pout + "Location: %s\n" % data_location
    pout = pout + "Industry: %s\n" % data_industry
    pout = pout + "Email: %s\n" % data_email
    pout = pout + "\n"
    pout = pout + "EDUCATION:\n---------------------\n"
    for s in data_schools:
        pout = pout + "%s\n" % s
    pout = pout + "\nCOMPANIES:\n---------------------\n"
    for c in data_companies:
        pout = pout + "%s\n" % c
    pout = pout + "\nSKILLS:\n---------------------\n"
    for sk in data_skills:
        pout = pout + "%s\n" % sk
    pout = pout + "\nRELEVANT NETWORK CONNECTIONS:\n---------------------\n"
    for n in data_connections:
        pout = pout + "%s\n" % n
    print(pout) 
    return pout


def profileValidateEmail(urn, email):
    url = "https://www.linkedin.com/sales/gmail/profile/viewByEmail/%s" % email    
    headers = {'Csrf-Token':'ajax:3972979001005769271'}
    headers['X-RestLi-Protocol-Version'] = '2.0.0' 
    cookies['JSESSIONID'] = 'ajax:3972979001005769271'
    r = requests.get(url, cookies=cookies, headers=headers)
    emailresp = r.text.encode('UTF-8')
    regex = urn
    m = re.findall(regex, emailresp, re.MULTILINE)
    if m:
        return email 

def profileLookupEmail(recordpos, email):
    try:
        url = "https://www.linkedin.com/sales/gmail/profile/viewByEmail/%s" % email    
        headers = {'Csrf-Token':'ajax:3972979001005769271'}
        headers['X-RestLi-Protocol-Version'] = '2.0.0' 
        cookies['JSESSIONID'] = 'ajax:3972979001005769271'
        r = requests.get(url, cookies=cookies, headers=headers)
        emailresp = r.text.encode('UTF-8')
        regex = "urn:li:member:"
        m = re.findall(regex, emailresp, re.MULTILINE)
        if m:
            dfn = re.search('\-fname="(.*?)" data\-',emailresp, re.IGNORECASE)
            data_firstname = dfn.group(1)
            dln = re.search('\-lname="(.*?)">',emailresp, re.IGNORECASE)
            data_lastname = dln.group(1)
            print(colored("[Update] ", "blue"), colored("Matched email: %s" % email, "white"))

            # Write data to XLSX file
            worksheet1.write('A%i' % recordpos, data_firstname)          
            worksheet1.write('B%i' % recordpos, data_lastname)          
            worksheet1.write('C%i' % recordpos, email)          
            worksheet1.write('D%i' % recordpos, "https://www.linkedin.com/sales/gmail/profile/proxy/%s" % email) 
            
            # Increment Record Position
            recordpos = recordpos + 1
            
        return recordpos
    except:
        print(colored("[Error] ","red"), colored("Could not load data from the provided list","white"))


def authenticate():
    print(colored("[Info] ","green"), colored("Initiating...", "white"))
    
    # Grab these from config or env variables
    username = os.environ.get("LI_USERNAME", "")
    password = os.environ.get("LI_PASSWORD", "")

    # Build request data
    url = "https://www.linkedin.com/checkpoint/lg/login-submit"
    csrf = "00000000-8a9a-474e-8bc1-6f10272b5fe6"
    postdata = {
            'session_key': username,
            'session_password': password,
            'loginCsrfParam': csrf,
            }
    cookies = {'bcookie': 'v=2&%s' % csrf}

    # Login Request
    r = requests.post(url, postdata, cookies=cookies, allow_redirects=False)

    # LinkedIn Session Key
    try:
        session = r.cookies['li_at']
        if(session):
            print(colored("[Info] ","green"), colored("Obtained new session: %s...\n" % session[0:25],"white"))
            cookie = {'li_at': session}
            return cookie
        else:
            sys.exit("[Fatal] Could not authenticate to linkedin. Set credentials in your environment variables.")
    except:
        sys.exit("[Fatal] Could not authenticate to linkedin. Set credentials in your environment variables.")



if __name__ == '__main__':
    title = """
 __                               _  _____       
/ _\ ___ _ __ __ _ _ __   ___  __| | \_   \_ __  
\ \ / __| '__/ _` | '_ \ / _ \/ _` |  / /\/ '_ \ 
_\ \ (__| | | (_| | |_) |  __/ (_| /\/ /_ | | | |
\__/\___|_|  \__,_| .__/ \___|\__,_\____/ |_| |_|
                  |_|                            
A tool to scrape LinkedIn v3.0
"""
    print(colored(title,"blue"))
   
    # Authenticate
    cookies = authenticate()
    
    # Prompt user for ScrapedIn functions
    #sifunc = input("What function do you want to perform?\n\n" + colored("1. ","yellow") + "Single Profile Scrape\n" + colored("2. ","yellow") + "Full Company Employee Scrape\n" + colored("3. ","yellow") + "Profile Match via Email List\n\n" + colored("> ","yellow"))
    sifunc = "2"

    if sifunc == "1":
        # Prompt user for data variable
        userslug= input("\nEnter the User's Slug (found in the profile URL)\n" + colored("> ","yellow"))
        outfile = input("\nEnter filename for output (exclude file extension)\n" + colored("> ","yellow"))
        results = profileLookupID(userslug)

        #Write Results to File
        f = open("results/%s.txt" % outfile,"w")
        f.write(results)
        f.close

    if sifunc == "2":
        # Prompt user for data variables
        companyName = input("\nEnter a Company Name\n" + colored("> ","yellow"))
        companyResults = companyLookup(companyName)
        company = input("\nEnter LinkedIn Company ID\n" + colored("> ","yellow"))
        search = input("\nEnter Job Title Keywords (use quotes for more percise results)\n" + colored("> ","yellow"))
        email = input("\nEmail format for guessing (i.e. {f}{last}@gmail.com)\n" + colored("> ", "yellow"))
        outfile = input("\nEnter filename for output (exclude file extension)\n" + colored("> ","yellow"))
        print()
        
        # URL Encode for the querystring
        search = urllib.parse.quote_plus(search)
        
        # Initiate XLSX File
        workbook = xlsxwriter.Workbook('results/%s.xlsx' % outfile)
        worksheet1 = workbook.add_worksheet('dataset')
        worksheet2 = workbook.add_worksheet('report')
        worksheet2.set_column(0,0, 25)
        worksheet2.set_column(1,2, 75)
        
        # Initialize Scraping
        get_search()

        # Close XLSD File
        workbook.close()

    if sifunc == "3":
        # Prompt user for data variables
        filename = input("\nEnter the file name to import (must be in the relative directory)\n" + colored("> ","yellow"))
        outfile = input("\nEnter filename for output (exclude file extension)\n" + colored("> ","yellow"))
        
        # Initiate XLSX File
        workbook = xlsxwriter.Workbook('results/%s.xlsx' % outfile)
        worksheet1 = workbook.add_worksheet('dataset')
        
        # Match email addresses to profiles
        edata = open(filename,"r")
        recordpos = 1
        for e in edata:
            email = e.strip()
            recordpos = profileLookupEmail(recordpos, email)
        
        # Close XLSD File
        workbook.close()
