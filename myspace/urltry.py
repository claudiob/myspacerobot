#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

"""\

__intro__

urltry.py wraps urllib open/get functions around try statements 

"""

from time import sleep
import urllib
import socket
import logging

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

def try_get(url, path):
	'''Try to get a file from url 3 times, then fail.'''
	try:
		resp = urllib.urlretrieve(url,path)
		return resp
	except:
		logging.warn("URL get error on " + url + ", retry 1")
		sleep(.5)
		try:
			resp = urllib.urlretrieve(url,path)
			return resp
		except:
			logging.warn("URL get error, retry 2")
			sleep(.5)
			try:
				resp = urllib.urlretrieve(url,path)
				return resp
			except:
				logging.error("URL get error after 3 tries, failing")
				return None

def get_page(url):
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

