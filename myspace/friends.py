#!/usr/bin/env python
"""Provides scrape_friends, for listing the friends of a MySpace profile.'''

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

__author__ = "Claudio Baccigalupo"

def scrape_friends(profile_id, max_pages, min_friends, only_artists):
    '''Return IDs of friends of profile_id.'''
    url = view_friends_URL(profile_id)
    friends, count_pages, is_artist = parse_friends_URL(url, only_id=False)
    if count_pages is None:
        logging.debug("Error retrieving friends of %d" % profile_id)
        friends = None
    elif count_pages > max_pages and max_pages is not None: # and not isSeed:
        logging.debug("Skipped friends of %d (%d pages)" % 
            (profile_id, count_pages))
        friends = None
    elif not is_artist and only_artists:
        logging.debug("Skipped friends of %d (not artist)" % profile_id)
        friends = None
    else:
        pages = range(1, count_pages) # For each page after the first
        URLs = [view_friends_URL(profile_id, page) for page in pages]
        more_friends = flatten(call_threaded(parse_friends_URL, URLs, 20))
        friends.extend(more_friends)
        logging.debug("Loaded %d friends of %d (from MySpace)" % 
            (len(friends), profile_id))
    return friends

# ###########################
# Main functions
# ###########################

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):

    def usage():
        # Add an interactive version to add parameters one by one
        print ("Usage: %s <options> mySpaceUID" % argv[0])
        print ("   options:")
        print ("   -h [--help]  print this usage statement")
        print ("   -d [--debug] set more verbose logging")
        print ("   -a [--all]   include also not musician profiles")
        print ("   -m [--min]   <int> specify the minimum number of friends")
        print ("   -x [--max]   <int> specify the maximum number of pages")
        print ("   -l [--log]   <file path> set the path to the log file")
        return

    min_friends    = 100
    max_pages      = 30
    only_artists   = True
    profile_id     = None
    log_path       = None
    logging_config = {"level": logging.INFO}
    if argv is None:
        argv = sys.argv
    try:
        ###### 1. Retrieve opts and args #####
        try:
            opts, args = getopt.getopt(argv[1:], "hdal:m:x:", 
                ["help", "debug", "all", "log=", "min=", "max="])
        except getopt.error, msg:
             raise Usage(msg)
        ###### 2. Process opts ###### 
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-l", "--log"):
                log_path = os.path.expanduser(arg)
                if not os.path.exists(log_path):
                    try:
                        os.mkdir(log_path)
                    except:
                        raise Usage("Could not create log directory")
            elif opt in ("-d", "--debug"):
                logging_config["level"] = logging.DEBUG
            elif opt in ("-a", "--all"):
                only_artists = False
            elif opt in ("-m", "--min"):
                min_friends = read_int(arg)
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
        friends = scrape_friends(profile_id, max_pages, min_friends, only_artists)
        return friends
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())


# ###########################
# Test functions
# ###########################

class TestFriends(unittest.TestCase):

    def testFriends(self):
        # Test that goremix is a friend of neurain
        self.assertTrue(270977337 in scrape_friends(395541002, 10, 0, True))
        # Add more tests if needed

# 179485614 piratas
# 284314184 go ape
# 213036694 danger
# 17442338 placebo
# 115476392 sux
# 64481548 subsonica
# 48154667 amaral
# 155754525 bon iver
# 395541002 goremix

