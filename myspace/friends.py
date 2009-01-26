#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import sys
import getopt
import os
import logging
from Queue import Queue
import threading
import time
import operator

from urltry import *
from myspace import *
from cache import *

# ###########################
# Cache-related functions
# ###########################

def store_friends(profileID, data):
    '''Store friends of profileID into local cache.'''
    return to_cache('cache/%d.txt' % profileID, data)

def load_friends(profileID):
    '''Returns friends of profileID from local cache, False if not cached.'''
    return from_cache('cache/%d.txt' % profileID)

def store_artist(profileID):
    '''Store data of profileID into local cache.'''
    return to_cache('cache/m%d.txt' % profileID, data)

def load_artist(profileID):
    '''Returns data of profileID from local cache, False if not cached.'''
    return from_cache('cache/m%d.txt' % profileID)

# ###########################
# Auxiliary functions
# ###########################

def intersect(a, b):
    '''Return the intersection of two lists'''
    return list(set(a) & set(b))

def is_digit(char): 
    '''Return true if char is a digit.'''
    return ord(char) in range(ord('0'),ord('9')+1)

def flatten(l):
    l = filter(None, l)
    # TEST THIS: return reduce(operator.add, l) if len(l) > 0 else l
    if len(l) > 0:
        l = reduce(operator.add, l)
    return l

# ###########################
# Thread-related functions
# ###########################

class FunctionThreader(threading.Thread):
    def __init__(self, function, parameter):
        threading.Thread.__init__(self) # init from parent
        self.function = function
        self.parameter = parameter
        self.result = None
 
    def get_result(self):
        return self.result
 
    def run(self):
        self.result = eval(self.function)(self.parameter)
     
def get_friends_list(artistID, pages):
    def producer(q, files):
        for URL in URLs:
            thread = FunctionThreader("parse_page", URL)
            thread.start()
            q.put(thread, True)

    finished = []
    def consumer(q, total_URLs):
        while len(finished) < total_URLs:
            thread = q.get(True)
            thread.join()
            # Remove this [0], instead swap "parse_page" with the right
            # "parse_friends" (although as is, it does not work)
            finished.append(thread.get_result()[0])

    q = Queue(5)
    URLs = [get_friends_page_URL(artistID, page) for page in range(1, pages)]
    prod_thread = threading.Thread(target=producer, args=(q, URLs))
    cons_thread = threading.Thread(target=consumer, args=(q, len(URLs)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return flatten(finished)
 
## From here on, change with the previous class
 
class FileGetter(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self) # init from parent
        self.url = url
        self.result = None
 
    def get_result(self):
        return self.result
 
    def run(self):
        self.result = parse_page(self.url)[0]

class FriendGetter(threading.Thread):
    def __init__(self, artistID):
        threading.Thread.__init__(self)
        self.artistID = artistID
        self.result = None

    def get_result(self):
        return self.result

    def run(self):
        self.result = get_friends(self.artistID)
 
def get_files(artistID, pages):
    def producer(q, files):
        # print "Producing"
        for file in files:
            # print "Scraping URL: %s" % file
            thread = FileGetter(file)
            thread.start()
            q.put(thread, True)
 
    finished = []
    def consumer(q, total_files):
        while len(finished) < total_files:
            thread = q.get(True)
            thread.join()
            # print "(read page " + str(len(finished)) + ") "
            finished.append(thread.get_result())
 
    q = Queue(5)
    files = [get_friends_page_URL(artistID, page) for page in range(1,pages)]
    prod_thread = threading.Thread(target=producer, args=(q, files))
    cons_thread = threading.Thread(target=consumer, args=(q, len(files)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    friends = flatten(finished)
    # print "Artist %d has %d friends" % (artistID, len(friends))
    return friends

def get_friends_files(artistIDs):
    def producer(q, artistIDs):
        for artistID in artistIDs:
            thread = FriendGetter(artistID)
            thread.start()
            q.put(thread, True)

    finished = []
    def consumer(q, total_artists):
        missing = total_artists - len(finished)
        while missing > 0:
            thread = q.get(True)
            thread.join()
            finished.append(thread.get_result())
            if missing % 25 == 0:
                logging.info("[%d more friends to load]" % missing)
            missing = total_artists - len(finished)
            
    q = Queue(20)
    prod_thread = threading.Thread(target=producer, args=(q, artistIDs))
    cons_thread = threading.Thread(target=consumer, args=(q, len(artistIDs)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return finished


def get_friends_page_URL(artistID, page=0):
    return viewFriendsURL + "%d&p=1&j=%d" % (artistID, page)

def get_other_pages(artistID, pages):
    #return get_files(artistID, pages)
    return get_friends_list(artistID, pages)
    
def get_ffriends(artistIDs):
    return get_friends_files(artistIDs)

def parse_page(url):
    '''Return first friends, page count, is musician'''
    resp = get_page(url)
    if resp is None:
        logging.debug("URL error on: %s" % url)
        return [None, None, None]
    # Parse list of friends
    friendPattern = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"'
    friends = map(int, re.findall(friendPattern, resp))
    # Parse page count
    pagesPattern = '&raquo;</a>.*?<a .*? class="pagingLink">(.*?)</a> </span><span class="nav_right">'
    try:
        count = int(filter(is_digit, re.search(pagesPattern, resp).group(1)))
    except:
        count = 1
    # Parse is musician or simple profile
    is_musician = resp.find("MySpace.Ads.Account = {\"Type\":\"7\"") > 0
    return [friends, count, is_musician]
    

# Not working within FunctionThreader
def parse_friends(url):
    parse_page(url)[0]


def get_friends(seed=284314184, maxPages=30, isSeed=False):
    '''Return friends of profileID with no more than maxPages friend pages.'''

    # Return from cache if exists and (in case of seed) if not None
    friends = load_friends(seed)
    if friends is not False and not (isSeed and friends is None):
        # Check why len(friends) is often 40 when cached
        logging.debug("Loaded %d friends of %d (cache)" % 
            (len(friends) if friends is not None else 0, seed))
        return friends

    logging.debug("Loading friends of %d from web" % seed)
    friends = []
    friends, pages, is_musician = parse_page(get_friends_page_URL(seed))
    if pages is None:
        logging.debug("Error retrieving friends of %d" % seed)
        friends = None
    if pages > maxPages and maxPages is not None and not isSeed:
        # print "Profile %d has too many pages (%d)" % (seed, pages)
        logging.debug("Skipped friends of %d (too many)" % seed)
        friends = None
    # Break if profile does not belong to an artist
    elif not is_musician:
        # print "Profile %d is not a musician" % seed
        logging.debug("Skipped friends of %d (not musician)" % seed)
        friends = None
    else:
        # print "Artist %d has %d pages" % (seed, pages)
        friends.extend(get_other_pages(seed, pages))
        # print "Artist %d has %d total friends" % (seed, len(friends))
        logging.debug("Loaded %d friends of %d (web)" % (len(friends), seed))
 
    # Store from Web to local cache
    store_friends(seed, friends)
    return friends


# ###########################
# Main function
# ###########################

def get_closest(currentID):    
    size = 20

    friends = get_friends(currentID, isSeed=True)
    if friends is None:
        print "Seed profile has no friends"
        return
    logging.debug("Parsed %d friends of %d" % (len(friends), currentID))    
    ffriends = get_ffriends(friends)
    logging.debug("Retrieved %d friends of %d" % (len(friends), currentID))

    found = shared = rank = [None] * len(friends)
    for f, friendID in enumerate(friends):
        if ffriends[f] is None:
            found[f] = shared[f] = 0
        else:
            found[f] = len(ffriends[f])
            shared[f] = len(intersect(ffriends[f], friends))

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

