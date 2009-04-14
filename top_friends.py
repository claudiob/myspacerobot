#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides load_top_friends, to load top friends of a MySpace profile.

load_ranked_friends retrieves all the friends of a seed MySpace profile, and 
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
from profile import *

__author__ = "Claudio Baccigalupo"
           
def scrape_ranked_friends(profile, filters=None, cache=None):
    '''Count the friends of each friend of profileID and the ones in common.'''
    ###### 1. Load friends of id (from web is cache is empty) #####
    friends = load_friends(profile, filters, cache)
    if friends is None and cache is not None:
        logging.debug("No friends in cache for %s, trying web" % profile)
        friends = scrape_friends(profile, filters)
    if friends is None:
        logging.debug("No friends found for %s" % profile)
        return
    ###### 2. Load friends of each friend (threaded) #####
    logging.debug("Parsed %d friends of %s" % (len(friends), profile))
    params = {"filters": filters, "cache": cache}
    ffriends = call_threaded(load_friends, friends, queueSize=5, params=params)
    logging.debug("Retrieved %d friends of %s" % (len(friends), profile))
    ###### 3. Count friends and friends in common with id #####
    count_common = [intersect_size(friends, f) for f in ffriends]
    ranked = []
    for i, friend in enumerate(friends):
        if count_common[i] > 0:
            friend.update({'friends':len(ffriends[i]), 'common':count_common[i]})
            ranked.append(friend)
    ###### 4. Return friends ordered by max common friends, min friends #####
    logging.debug("Retrieved %d friends %s" % (len(ranked), ranked))
    ranked.sort(key = lambda x:(-x['common'], x['friends']))
    return ranked

def load_ranked_friends(profile, filters=None, cache=None):
    '''Retrieve ranked friends of profile either from cache or the web.'''
    ###### 1. Load from cache if available #####
    cache_ext = "t" # Save ranked_friends files as "<ID>c.txt"
    friends = from_cache(profile, cache, ext=cache_ext)
    if friends is not False:
        logging.debug("Loaded %d ranked friends of %s (from cache)" % 
            (len(friends) if friends is not None else 0, profile))
        return friends
    ###### 2. Load from web and store in cache otherwise #####
    friends = scrape_ranked_friends(profile, filters, cache)
    
    # To save space, only store the ID
    if friends is not None:
        friends_id = [{'id': f['id'], 'friends': f['friends'], 'common': f['common']} for f in friends]
        to_cache(profile, cache, friends_id, ext=cache_ext)
#    to_cache(profile, cache, ranked, ext=cache_ext)
    return friends


def load_top_friends(profile, beta=0, size=1, min_common = 5, filters=None, cache=None):
    '''Return top friends of a profile according to ranking, size and beta.'''
    ###### 1. Load ranked friends of profile #####
    rank = load_ranked_friends(profile, filters, cache)
    if rank is None:
        logging.debug("Profile %s has no top friends" % profile)
        return None
    top_friends = []
    for friend in rank:
        if friend['common'] >= min_common:
            top_friends.append({'id': friend['id'], 'weight': friend['common']*1.0/pow(friend['friends'], beta)})
        # friend.update({'weight': friend['common']*1.0/pow(friend['friends'], beta)})      
    top_friends.sort(key = lambda x:(-x['weight']))
    return top_friends[:size]
    
# ###########################
# Test functions
# ###########################

class TestTopFriends(unittest.TestCase):
    def setUp(self):
        self.profile1 = {"id": 270977337} # goremix
        self.profile2 = {'id': 395541002, 'name': 'g'}
        self.filters  = {"max_pages":30, "only_artists":True, "min_pages":1}    
    def testRankedFriends(self):
        # Test that neurain has 6 friends, 1 in common with goremix
        friends2 = {'profile': self.profile2, 'friends': 6, 'common': 1}
        self.assertTrue(friends2 in \
            load_ranked_friends(self.profile1, filters=self.filters))
    def testTopFriends(self):
        # Test that assertTrue is a top friend of goremix
        self.assertTrue(self.profile2["id"] in [top["profile"]["id"] for \
        top in load_top_friends(self.profile1, filters=self.filters, size=10)])
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
        print ("   -b [--beta]  <float> specify the popularity bias [0-1]")
        print ("   -s [--size]  <int> specify the number of top friends")
        print ("   -q [--common]<int> specify the minimum common friends")
        print ("   -c [--cache] <path> set the path to the cache files")
        print ("   -l [--log]   <path> set the path to the log file")
        return

    min_pages      = 2    # min 80 friends
    max_pages      = 30   # max 1200 friends
    beta           = 0.75
    size           = 10
    min_common     = 5
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
            opts, args = getopt.getopt(argv[1:], "htdac:l:m:x:b:s:q:", 
            ["help", "test", "debug", "all", "cache=", "log=", 
             "min=", "max=", "beta=", "size=", "common=",])
        except getopt.error, msg:
             raise Usage(msg)
        ###### 2. Process opts ###### 
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-t", "--test"):
                suite = unittest.TestSuite()
                suite.addTest(unittest.makeSuite(TestTopFriends))
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
            elif opt in ("-b", "--beta"):
                beta = read_float(arg)
            elif opt in ("-s", "--size"):
                size = read_int(arg)
            elif opt in ("-q", "--common"):
                min_common = read_int(arg)
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
        top = load_top_friends(profile, beta, size, min_common, filters, cache_path)
        if top is not None:
            print "The top friends of %s are:" % print_profile(profile, cache_path)
            for i, friend in enumerate(top):
                print "%2d) %.3f: %s" % (i+1, friend['weight'], print_profile(friend, cache_path))
        # return top
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())


