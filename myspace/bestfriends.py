#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides load_best, to load best friends of a MySpace profile.

load_best retrieves all the friends of a seed MySpace profile, and 
returns those that have some friend in common with the seed profile, ordered
by decreasing number of common friends, increasing number of total friends.
"""

import sys
import getopt
import os
import logging
import threading
import time
import webbrowser
import random

from cache import *
from threads import *
from utils import *
from friends import *

__author__ = "Claudio Baccigalupo"
           
def scrape_best(profile, page_limits=[None, None], only_artists=True, cache=None):
    '''Count the friends of each friend of profileID and the ones in common.'''
    ###### 1. Load friends of id (from web is cache is empty) #####
    friends = load_friends(profile, page_limits, only_artists, cache)
    if friends is None and cache is not None:
        logging.debug("No friends in cache for %s, trying web" % profile)
        friends = scrape_friends(profile, page_limits, only_artists)
    if friends is None:
        logging.debug("No friends found for %s" % profile)
        return
    ###### 2. Load friends of each friend (threaded) #####
    logging.debug("Parsed %d friends of %s" % (len(friends), profile))
    params = {"page_limits": page_limits, "only_artists": only_artists}
    params["cache"] = cache
    ffriends = call_threaded(load_friends, friends, queueSize=5, params=params)
    logging.debug("Retrieved %d friends of %s" % (len(friends), profile))
    ###### 3. Count friends and friends in common with id #####
    friends_id = map_id(friends)
    count_common = [intersect_size(friends_id, map_id(f)) for f in ffriends]
    best = [{"profile": friend, "friends": len(ffriends[i]), "common": count_common[i]} \
            for i, friend in enumerate(friends) if count_common[i] > 0]
    ###### 4. Return friends ordered by max common friends, min friends #####
    best.sort(key = lambda x:(-x["common"], x["friends"]))
    return best

def load_best(profile, page_limits=[None, None], only_artists=True, cache=None):
    '''Retrieve best friends of id either from cache or the web.'''
    ###### 1. Load from cache if available #####
    cache_ext = "c" # Save best_friends files as "<ID>c.txt"
    best = from_cache(profile["id"], cache, ext=cache_ext)
    if best is not False:
        logging.debug("Loaded %d best friends of %s (from cache)" % 
            (len(best) if best is not None else 0, profile))
        return best
    ###### 2. Load from web and store in cache otherwise #####
    best = scrape_best(profile, page_limits, only_artists, cache)
    if cache is not None:
        to_cache(profile["id"], cache, best, ext=cache_ext)
    return best

def recommend(profile, beta=0.75, size=5, page_limits=[None, None], only_artists=True, cache=None):
    '''Recommend a friend of profile to another friend of profile.'''
    ###### 1. Load best friends of profile #####
    best = load_best(profile, page_limits, only_artists, cache_path)

    rank = [{"profile": b["profile"], "weight": \
        b["common"]*1.0/pow(b["friends"], beta)} for b in best]
    rank.sort(key = lambda x:(-x["weight"]))
    return rank[:size]
    
    ## CONTINUA DA QUA!! IN REALTA' QUESTO MODULO DEVE RITORNARE
    ## QUELLA CHE ORA SI CHIAMA RECOMMEND, CHE SI DOVRA' CHIAMARE BEST
    ## MENTRE LA SCRAPE_BEST E LOAD_BEST SARANNO QUALCOSA TIPO
    ## DETAILED_FRIENDS O CONNECTED O NON LO SO!!
    ## POI CAMBIA ANCHE IL TEST E LA CHIAMATA NELLA MAIN!


# ###########################
# Test functions
# ###########################

class TestBest(unittest.TestCase):

    def testBest(self):
        # Test that neurain has 7 friends, 0 in common with goremix
        self.assertTrue([270977337, 7, 0] in load_best({"id": 395541002}))
        # Change with more meaningful test


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

    min_pages      = 2    # min 80 friends
    max_pages      = 30   # max 1200 friends
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
        page_limits = [min_pages, max_pages]
        profile = {"id": profile_id}
        best = load_best(profile, page_limits, only_artists, cache_path)
        return best
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())


