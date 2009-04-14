#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides download_page, for retrieving a Web page with error check.

download_page opens a Web page and check for URL and socket errors, trying
again several times to retrieve the page if an error occurs.

Test usage: python download.py
"""

from time import sleep
import urllib
import socket
import logging
import unittest

__author__ = "Claudio Baccigalupo"

def try_open(url):
	'''Try to open a url 3 times, then fail.'''
	try:
		resp = urllib.urlopen(url)
		return resp
	except:
		logging.warn("URL open error on " + url + ", retry 1")
		sleep(.5)
		try:
			resp = urllib.urlopen(url)
			return resp
		except:
			logging.warn("URL open error, retry 2")
			sleep(.5)
			try:
				resp = urllib.urlopen(url)
				return resp
			except:
				logging.error("URL open error after 3 tries, failing")
				return None

def download_page(url):
    '''Download a Web page checking for URL and socket errors.'''
    resp = try_open(url)
    if resp == None:
        logging.error("URL error on %s (skipping)" % url)
        return None
    try:
        page = resp.read()
    except socket.error, msg:
        logging.error("Socket error on %s: %s" % (url, msg))
        resp = try_open(url)
        if resp == None:
            logging.error("URL error on %s (skipping)" % url)
            return None
        try:
            page = resp.read()
        except socket.error, msg:
            logging.error("Socket error on %s: %s (skipping)" % (url, msg))
            return None
    resp.close()
    return page


class TestDownload(unittest.TestCase):
    def testDownload(self):
        page = download_page("http://www.myspace.com")
        self.assertTrue(page.find("MySpace") > 0)
        # Add more tests if needed

if __name__ == '__main__':
    unittest.main()
