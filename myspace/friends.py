#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides scrape_friends, for listing the friends of a MySpace profile.

scrape_friends connects to the MySpace Web page, retrieves all the pages
listing the friends of that profile, and returns a list of their MySpace IDs.

Example usage: python friends.py 395541002
"""

import sys
import getopt
import os
import logging
import unittest

from paths import view_friends_URL, parse_friends_URL
from threads import *
from utils import *
from cache import *

__author__ = "Claudio Baccigalupo"

# class Profile(dict):
#     def __init__(self, id=None, name=None):
#         self["id"] = id
#         self["name"] = name
#     def id(self):
#         return self["id"]
#     def name(self):
#         return self["name"]

def scrape_friends(profile, filters):
    '''Retrieve all the friends of id from the web that satisfy filters.'''
    url = view_friends_URL(profile)
    friends, count_pages, is_artist = parse_friends_URL(url, only_id=False)
    if count_pages is None:
        logging.debug("Error retrieving friends of %s" % profile)
        friends = None
    elif filters and filters["min_pages"] and count_pages<filters["min_pages"]:
        logging.debug("Skipped friends of %s (%d<%d pages)" % 
            (profile, count_pages, filters["min_pages"]))
        friends = None
    elif filters and filters["max_pages"] and count_pages>filters["max_pages"]:
        logging.debug("Skipped friends of %s (%d>%d pages)" % 
            (profile, count_pages, filters["max_pages"]))
        friends = None
    elif filters and filters["only_artists"] and not is_artist:
        logging.debug("Skipped friends of %s (not artist)" % profile)
        friends = None
    else:
        pages = range(1, count_pages) # For each page after the first
        URLs = [view_friends_URL(profile, page) for page in pages]
        more_friends = call_threaded(parse_friends_URL, URLs, queueSize=20)
        friends.extend(flatten(more_friends))
        logging.debug("Loaded %d friends of %s (from MySpace)" % 
            (len(friends), profile))
    return friends

def load_friends(profile, filters=None, cache=None):
    '''Retrieve all the friends of id either from cache or the web.'''
    ###### 1. Load from cache if available #####
    # sys.exit()
    friends = from_cache(profile, cache)
    if friends is not False:
        # SLOW! logging.debug("Loaded %d friends of %s (from cache)" % 
        #    (len(friends) if friends is not None else 0, profile))
        return friends
    ###### 2. Load from web and store in cache otherwise #####
    friends = scrape_friends(profile, filters)
    to_cache(profile, cache, friends)
    return friends

# New version: friends only store ID, profile stores the rest
def load_friends(profile, filters=None, cache=None):
    '''Retrieve all the friends of id either from cache or the web.'''
    ###### 1. Load from cache if available #####
    # sys.exit()
    friends = from_cache(profile, cache, ext="f")
    if friends is not False:
        return friends
    ###### 2. Load from web and store in cache otherwise #####
    friends = scrape_friends(profile, filters)
    if friends is not None:
        for f in friends:
            to_cache(f, cache, f, ext="p")
        # To save space, only store the ID
        friends_id = [{'id': f['id']} for f in friends]
        to_cache(profile, cache, friends_id, ext="f")
    return friends

# ###########################
# Test functions
# ###########################

class TestFriends(unittest.TestCase):

    def testFriends(self):
        # Test that goremix is a friend of neurain
        self.assertTrue(270977337 in [p["id"] \
            for p in load_friends({"id": 395541002})])
        # Add more tests if needed

# ###########################
# Main functions
# ###########################

def main(argv=None):

    def usage():
        # Add an interactive version to add parameters one by one
        print ("Usage: %s <options> mySpaceUID" % argv[0])
        print ("   options:")
        print ("   -h [--help]  print this usage statement")
        print ("   -t [--test]  only run test")
        print ("   -d [--debug] set more verbose logging")
        print ("   -a [--all]   include also not musician profiles")
        print ("   -m [--min]   <int> specify the minimum friends' pages")
        print ("   -x [--max]   <int> specify the maximum friends' pages")
        print ("   -c [--cache] <path> set the path to the cache files")
        print ("   -l [--log]   <path> set the path to the log file")
        return

    min_pages      = None
    max_pages      = None
    only_artists   = True
    profile_id     = None
    cache_path     = None
    log_path       = None
    logging_config = {"level": logging.INFO}
    if argv is None:
        argv = sys.argv
    try:
        ###### 1. Retrieve opts and args #####
        try:
            opts, args = getopt.getopt(argv[1:], "htdac:l:m:x:", 
            ["help", "test", "debug", "all", "cache=", "log=", "min=", "max="])
        except getopt.error, msg:
             raise Usage(msg)
        ###### 2. Process opts ###### 
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-t", "--test"):
                suite = unittest.TestSuite()
                suite.addTest(unittest.makeSuite(TestFriends))
                unittest.TextTestRunner(verbosity=2).run(suite)
                sys.exit()
            elif opt in ("-l", "--log"):
                log_path = os.path.expanduser(arg)
                if not os.path.exists(log_path):
                    try:
                        os.mkdir(log_path)
                    except:
                        raise Usage("Could not create log directory")
            elif opt in ("-c", "--cache"):
                cache_path = os.path.expanduser(arg)
                if not os.path.exists(cache_path):
                    try:
                        os.mkdir(cache_path)
                    except:
                        raise Usage("Could not create cache directory")
            elif opt in ("-d", "--debug"):
                logging_config["level"] = logging.DEBUG
            elif opt in ("-a", "--all"):
                only_artists = False
            elif opt in ("-m", "--min"):
                min_pages = read_int(arg)
            elif opt in ("-x", "--max"):
                max_pages = read_int(arg)
        ###### 3. Process args ######
        if len(args) < 1:
            raise Usage("You did not specify a MySpaceUID")
        elif len(args) > 1:
            raise Usage("You specified more than one MySpaceUID")
        else:
            profile_id = read_int(args[0])
        ###### 4. Enable logging ######
        logging_config["format"] = '%(asctime)s %(levelname)-8s %(message)s'
        logging_config["datefmt"] = '%Y/%M/%D %H:%M:%S'
        if log_path is not None:        
            logging_config["filename"] = os.path.join(log_path, "friends.log")
            logging_config["filemode"] = "w"
        logging.basicConfig(**logging_config)
        ###### 5. Retrieve friends ######
        profile = {"id": profile_id}
        filters = {"max_pages": max_pages, "min_pages": min_pages, \
                   "only_artists": only_artists}
        friends = load_friends(profile, filters, cache_path)
        return friends
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())



# 179485614 piratas
# 284314184 go ape
# 213036694 danger
# 17442338 placebo
# 115476392 sux
# 64481548 subsonica
# 48154667 amaral
# 155754525 bon iver
# 395541002 goremix

