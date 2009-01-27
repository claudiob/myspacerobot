#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import sys
import getopt
import os
import logging
import threading
import time
import webbrowser

from myspace import *
from cache import *
from threads import *
from utils import *

# ###########################
# Cache-related functions
# ###########################

def path_cached(profileID, cachePath, ext):
    '''Convert 123456789012 into [cachePath]/123/456/789/012[ext].txt.'''
    path = "/".join([str(profileID).zfill(12)[3*i:3*i+3] for i in range(4)])
    if ext is not None:
        path = path + ext
    return os.path.join(cachePath, path + ".txt")

def load_cached(profileID, cachePath, ext=None):
    '''Return profileID data from cache, False if not cached.'''
    return from_cache(path_cached(profileID, cachePath, ext))

def store_cached(profileID, data, cachePath, ext=None):
    '''Store profileID data into cache.'''
    return to_cache(path_cached(profileID, cachePath, ext), data)

# def convert_old_cache(cachePath):
#     for i, oldpath in enumerate(os.listdir(cachePath)):
#         profileID = os.path.split(oldpath)[1][:-4]
#         ext = None if is_digit(profileID[0]) else profileID[0]
#         newpath = path_cached(profileID, "cache", ext)
#         if not os.path.exists(os.path.split(newpath)[0]):
#             os.makedirs(os.path.split(newpath)[0])
#         print "%d) cp %s %s" % (i, os.path.join(cachePath, oldpath), newpath)
#         os.system("cp %s %s" % (os.path.join(cachePath, oldpath), newpath))

# ###########################
# Friends-related functions
# ###########################

def get_friendIDs(seed, cachePath=None, maxPages=None, isSeed=False):
    '''Return friends of profileID with no more than maxPages friend pages.'''

    # Return from cache if exists and (in case of seed) if not None
    if cachePath is not None:
        friends = load_cached(seed, cachePath)
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
    elif pages > maxPages and maxPages is not None and not isSeed:
        logging.debug("Skipped friends of %d (%d pages)" % (seed, pages))
        friends = None
    elif not is_musician:
        logging.debug("Skipped friends of %d (not musician)" % seed)
        friends = None
    else:
        URLs = [get_friends_URL(seed, page) for page in range(1, pages)]
        friends_list = call_threaded(parse_friends, URLs, 20)
        friends.extend(flatten(friends_list))
        logging.debug("Loaded %d friends of %d (web)" % (len(friends), seed))
 
    # Store from Web to local cache
    if cachePath is not None:
        store_cached(seed, friends, cachePath)
    return friends

def get_friend_friends(profileID, maxPages, cachePath=None):
    '''Count the friends of each friend of profileID and the ones in common.'''
    # Return from cache if exists
    if cachePath is not None:
        ffriends = load_cached(profileID, cachePath, "c")
        if ffriends is not False:
            return ffriends
     
    friendIDs = get_friendIDs(profileID, cachePath=cachePath, maxPages=maxPages, isSeed=True)
    if friendIDs is None:
        logging.debug("No friends found for %d" % profileID)
        return
    logging.debug("Parsed %d friends of %d" % (len(friendIDs), profileID))
    params = {"cachePath": cachePath, "isSeed": False, "maxPages": maxPages}    
    ffriendIDs = call_threaded(get_friendIDs, friendIDs, 5, params)
    logging.debug("Retrieved %d friends of %d" % (len(friendIDs), profileID))

    result = [None] * len(friendIDs)
    for f, friendID in enumerate(friendIDs):
        if ffriendIDs[f] is None:
            found = shared = 0
        else:
            found = len(ffriendIDs[f])
            shared = len(intersect(ffriendIDs[f], friendIDs))
        result[f] = [friendID, found, shared]

    # Store ffriends to local cache
    if cachePath is not None:
        store_cached(profileID, result, cachePath, "c")
    return result

def are_friends(profileID, friendID, maxPages, cachePath=None):
    '''Return True if friendID is in the list of friends of profileID.'''
    friendIDs = get_friendIDs(profileID, cachePath=cachePath, maxPages=maxPages)
    return friendID in friendIDs

def get_closest_friends(seed, size, beta, minimum, maxPages, cachePath=None):
    '''Return the friends of seed with most friends in common with seed.'''
    friends = get_friend_friends(seed, maxPages, cachePath)
    rank = [None] * len(friends)
    rank = [[f[2]*1.0/pow(f[1], beta) if f[1] >= minimum else 0, f[0]] for f in friends]
    rank.sort()
    rank.reverse()
    return [r[1] for r in rank[:size] if r[0] > 0 ]

def open_closest_friends(profileIDs):
    '''Open in a web browser the closest friends of profileID.'''
    for profileID in profileIDs:
        webbrowser.open_new_tab(viewProfileURL + str(profileID))

def recommend_friends(profileIDs, maxPages, cachePath=None):
    for i, profileID in enumerate(profileIDs):
        other_friends = profileIDs[0:i] + profileIDs[i+1:len(profileIDs)]
        for friendID in other_friends:
            if not are_friends(profileID, friendID, maxPages, cachePath):
                print "Recommend %d to %d" % (profileID, friendID)

# ###########################
# Main functions
# ###########################

def usage():
    print ("Usage: friends.py <options>")
    print ("   options:")
    print ("   -h [--help]    print this usage statement")
    print ("   -v [--verbose] more info to standard out")
    print ("   -o [--open]    open closest profiles in a web browser")
    print ("   -a [--artist]  <mySpaceUID> specify the starting artist ID")
    print ("   -b [--beta]    <value in [0,1]> specify the popularity bias")
    print ("   -m [--minimum] <integer> specify the minimum number of friends")
    print ("   -x [--maximum] <integer> specify the maximum number of pages")
    print ("   -c [--cache]   <cache path> set the path to the cache folder")
    print ("   -l [--log]     <log file path> set the path to the log file")
    return


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    profileID = 284314184 # By default use Go Ape
    friends = []
    grabList = []
    cachePath = os.path.expanduser("cache")
    flag_verbose = skip = 0
    beta = 1.0
    size = 5
    minimum = 100
    openbrowser = False
    maxPages = 30

    # Add as parameters maxPages and MIN pages!
    
    loggingConfig = {"format":'%(asctime)s %(levelname)-8s %(message)s',
                     "datefmt":'%Y/%M/%D %H:%M:%S', "level": logging.INFO}

    try:
        opts, args = getopt.getopt(argv, "hvoa:l:c:b:s:m:x:", 
            ["help", "verbose", "open", "artist=", "log=", "cache=", 
             "beta=", "size=", "minimum=", "maximum="])
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
        elif opt in ("-m", "--minimum"):
            minimum = int(arg)
        elif opt in ("-x", "--maximum"):
            maxPages = int(arg)
        elif opt in ("-a", "--artist"):
            profileID = int(arg)
        elif opt in ("-b", "--beta"):
            beta = float(arg)
        elif opt in ("-s", "--size"):
            size = int(arg)
        elif opt in ("-c", "--cache"):
             cachePath = os.path.expanduser(arg)
        else:
            print "Poorly specified options..."
            usage()
            return 4

    logging.basicConfig(**loggingConfig)
    
    logging.info("Estimating closest artist of %d" % profileID)
    start = time.time()    
    closest = get_closest_friends(profileID, size, beta, minimum, maxPages, cachePath)
    # if filter min songs or last connected...
    # open viewProfile and remove them!
    logging.info("Elapsed time: %s" % (time.time() - start))
    print "%d closest of %d: %s" % (len(closest), profileID, closest)
    if openbrowser:
        open_closest_friends(closest)
    recommend_friends(closest, maxPages, cachePath)

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

