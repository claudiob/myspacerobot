#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import sys
import getopt
import os
import logging
from Queue import Queue
import threading
import time

from urltry import *
from myspace import *
from cache import *
from threads import *
from utils import *

# ###########################
# Cache-related functions
# ###########################

def store_friends(profileID, data):
    '''Store friends of profileID into cache.'''
    return to_cache('cache/%d.txt' % profileID, data)

def load_friends(profileID):
    '''Returns friends of profileID from cache, False if not cached.'''
    return from_cache('cache/%d.txt' % profileID)

def store_artist(profileID, data):
    '''Store data of profileID into cache.'''
    return to_cache('cache/m%d.txt' % profileID, data)

def load_artist(profileID):
    '''Returns data of profileID from cache, False if not cached.'''
    return from_cache('cache/m%d.txt' % profileID)

def store_closest(profileID, data):
    '''Store closest friends of profileID into cache.'''
    return to_cache('cache/c%d.txt' % profileID, data)

def load_closest(profileID):
    '''Returns closest friends of profileID from cache, False if not cached.'''
    return from_cache('cache/c%d.txt' % profileID)


# ###########################
# Friends-related functions
# ###########################

def get_friends_pages(profileID, count_pages):
    URLs = [get_friends_URL(profileID, page) for page in range(1, count_pages)]
    friends_list = call_threaded(parse_friends, URLs, 20)
    return flatten(friends_list)

def parse_friends(url, complete=False):
#    parse_page(url)[0]
    '''Return list of friends and, if complete, page count and is musician.'''
    resp = get_page(url)
    friends = count = is_musician = None
    if resp is None:
        logging.debug("URL error on: %s" % url)
    else:
        friends = parse_friends_list(resp)
        if complete:
            count = parse_friends_page_count(resp)
            is_musician = parse_friends_is_musician(resp)
    return [friends, count, is_musician] if complete else friends


# ###########################
# Friends-related functions
# ###########################

def get_friends_friends(profileIDs):
    return call_threaded(get_friends, profileIDs, 5)

def get_friends(seed=284314184, maxPages=30, isSeed=False):
    '''Return friends of profileID with no more than maxPages friend pages.'''

    # Return from cache if exists and (in case of seed) if not None
    friends = load_friends(seed)
    if friends is not False and not (isSeed and friends is None):
        # Check why len(friends) is often 40 when cached
        logging.debug("Loaded %d friends of %d (cache)" % 
            (len(friends) if friends is not None else 0, seed))
        return friends

    friends = []
    friends, pages, is_musician = parse_friends(get_friends_URL(seed), True)
    if pages is None:
        logging.debug("Error retrieving friends of %d" % seed)
        friends = None
    if pages > maxPages and maxPages is not None and not isSeed:
        # print "Profile %d has too many pages (%d)" % (seed, pages)
        logging.debug("Skipped friends of %d (%d pages)" % (seed, pages))
        friends = None
    # Break if profile does not belong to an artist
    elif not is_musician:
        # print "Profile %d is not a musician" % seed
        logging.debug("Skipped friends of %d (not musician)" % seed)
        friends = None
    else:
        # print "Artist %d has %d pages" % (seed, pages)
        friends.extend(get_friends_pages(seed, pages))
        # print "Artist %d has %d total friends" % (seed, len(friends))
        logging.debug("Loaded %d friends of %d (web)" % (len(friends), seed))
 
    # Store from Web to local cache
    store_friends(seed, friends)
    return friends


# ###########################
# Main function
# ###########################

def get_closest(currentID):

    # Return from cache if exists
    closest = load_closest(currentID)
    if closest is not False:
        return closest
     
    size = 20

    friends = get_friends(currentID, isSeed=True)
    if friends is None:
        print "Seed profile has no friends"
        return
    logging.debug("Parsed %d friends of %d" % (len(friends), currentID))    
    ffriends = get_friends_friends(friends)
    logging.debug("Retrieved %d friends of %d" % (len(friends), currentID))

    closest = [None] * len(friends)
    for f, friendID in enumerate(friends):
        if ffriends[f] is None:
            found = shared = 0
        else:
            found = len(ffriends[f])
            shared = len(intersect(ffriends[f], friends))
        closest[f] = [friendID, found, shared]

    # Store closest to local cache
    store_closest(currentID, closest)
    return closest

def print_closest(seed):
    rank = [None] * len(friends)
    rank = [[shared[f]*1.0/found[f] if found[f] > 0 else 0, friendID] 
        for f, friendID in enumerate(friends)]
    rank.sort()
    rank.reverse()
    print "Top %d friends of %d: %s" % (size, currentID, [i[1] for i in rank[:size] if i[0] > 0 ])


def usage():
    print ("Usage: friends.py <options>")
    print ("   options:")
    print ("   -h [--help]    print this usage statement")
    print ("   -v [--verbose] more info to standard out")
    print ("   -a [--artist]  <mySpaceUID> specify the starting artist ID")
    print ("   -c [--cache]   <cache path> set the path to the cache folder")
    print ("   -l [--log]     <log file path> set the path to the log file")
    return


# piratas (179485614) 1937 friends
# go ape (284314184)
# danger (213036694)
# 17442338 placebo
# 115476392 sux
# 64481548 subsonica
# 48154667 amaral



def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    currentID = 284314184 # By default use Go Ape
    friends = []
    grabList = []
    cachePath = os.path.expanduser("cache")
    flag_verbose = skip = 0

    # Add as parameters maxPages and size
    
    loggingConfig = {"format":'%(asctime)s %(levelname)-8s %(message)s',
                     "datefmt":'%Y/%M/%D %H:%M:%S', "level": logging.INFO}

    try:
        opts, args = getopt.getopt(argv, "hva:l:c:", 
            ["help", "verbose", "artist=", "log=", "cache="])
    except getopt.GetoptError, err:
        print >> sys.stderr, "Poorly specified options..." + str(err)
        usage()
        sys.exit(2)
    if len(opts) < 1:
        print ("not enough args specified, try again")
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-l", "--log"):
            logPath = os.path.expanduser(arg)
            if not os.path.exists(logPath):
                try:
                    os.mkdir(logPath)
                except:
                    print "Could not create log directory"
                    usage()
                    return 183
            # Should add a log rotator here
            loggingConfig ={"format":'%(asctime)s %(levelname)-8s %(message)s',
                             "datefmt":'%Y/%M/%D %H:%M:%S',
                             "filename":os.path.join(logPath ,"friends.log"),
                             "filemode":"w", "level": logging.INFO}        
        elif opt in ("-v", "--verbose"):
            flag_verbose = True
            loggingConfig["level"] = logging.DEBUG
        elif opt in ("-a", "--artist"):
            currentID = int(arg)
        elif opt in ("-c", "--cache"):
             cachePath = os.path.expanduser(arg)
        else:
            print "Poorly specified options..."
            usage()
            return 4

    if not os.path.exists(cachePath):
        try:
            os.mkdir(cachePath)
        except:
            print "Could not create cache directory"
            usage()
            return 183

    logging.basicConfig(**loggingConfig)
    
    logging.info("Estimating closest artist of %d" % currentID)
    start = time.time()    
    get_closest(currentID)
    logging.info("Elapsed time: %s" % (time.time() - start))

if __name__ == "__main__":
    sys.exit(main())

# def getRecommendation(seedID, size=5):
#     pass

