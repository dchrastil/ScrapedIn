#!/usr/bin/python

__author__ = 'Danny Chrastil'
__email__ = 'danny.chrastil@gmail.com'
__description__ = "Python Requests doesn't handle LinkedIn authentication well. This uses urllib instead"
__version__ = '0.2'

from __future__ import print_function

import config
import cookielib
import os
import re
import string
import sys
import urllib
import urllib2

from bs4 import BeautifulSoup


def linkedIn():
        global opener
        cookie_filename = "cookies.txt"

        # Simulate browser with cookies enabled
        cj = cookielib.MozillaCookieJar(cookie_filename)
        if os.access(cookie_filename, os.F_OK):
            cj.load()

        # Load Proxy settings
        if len(config.proxylist) > 0:
            #print("[Status] Setting up proxy (%s)" % config.proxylist[0])
            proxy_handler = urllib2.ProxyHandler({'https':config.proxylist[0]})
            opener = urllib2.build_opener(
                proxy_handler,
                urllib2.HTTPRedirectHandler(),
                urllib2.HTTPHandler(debuglevel=0),
                urllib2.HTTPSHandler(debuglevel=0),
                urllib2.HTTPCookieProcessor(cj)
            )
        else:
            opener = urllib2.build_opener(
                urllib2.HTTPRedirectHandler(),
                urllib2.HTTPHandler(debuglevel=0),
                urllib2.HTTPSHandler(debuglevel=0),
                urllib2.HTTPCookieProcessor(cj)
            )

        # Get CSRF Token
        #print("[Status] Obtaining a CSRF token")
        html = loadPage("https://www.linkedin.com/")
        soup = BeautifulSoup(html, "html.parser")
        csrf = soup.find(id="loginCsrfParam-login")['value']
        #print(csrf)
        # Authenticate
        login_data = urllib.urlencode({
            'session_key': config.linkedin['username'],
            'session_password': config.linkedin['password'],
            'loginCsrfParam': csrf,
        })
        #print("[Status] Authenticating to Linkedin")
        html = loadPage("https://www.linkedin.com/uas/login-submit", login_data)
        soup = BeautifulSoup(html, "html.parser")
        try:
            print(cj._cookies['.www.linkedin.com']['/']['li_at'].value)
        except as e:
            print("error: {}".format(e))
        cj.save()
        os.remove(cookie_filename)


def loadPage(url, data=None):
        try:
            response = opener.open(url)
        except as e:
            print("\n[Fatal] Your IP may have been temporarily blocked: {}".format(e))

        try:
            if data is not None:
                response = opener.open(url, data)
            else:
                response = opener.open(url)
            #return response.headers.get('Set-Cookie')
            return ''.join(response.readlines())
        except as e:
            # If URL doesn't load for ANY reason, try again...
            # Quick and dirty solution for 404 returns because of network problems
            # However, this could infinite loop if there's an actual problem
            print("[Notice] Exception hit: {}".format(e))
            sys.exit(0)


linkedIn()
