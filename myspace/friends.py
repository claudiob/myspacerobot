#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import urllib
import re
import logging
import pickle

logging.basicConfig()
log = logging.getLogger("MySpace")
log.setLevel(logging.INFO)

viewFriendsURL = "http://friends.myspace.com/index.cfm?fuseaction=user.viewfriends&friendID=%d"

# ###########################
# HTTP-related functions
# ###########################

def get_response(url):
    '''Return HTML code for url.'''
    log.debug("Opening URL: %s" % url)
    while True:
        try:
            return urllib.urlopen(url).read()
        except IOError:
            log.warn("Opening URL failed - trying again: %s" % url)

def parse_artist(resp):
    '''Parse viewFriends code and return whether belongs to an artist.'''
    return resp.find("MySpace.Ads.Account = {\"Type\":\"7\"") > 0

def parse_friends(resp):
    '''Parse viewFriends code and return list of friends ID.'''
    friendPattern = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"'
    return map(int, re.findall(friendPattern, resp))

def parse_more(resp):
    '''Parse viewFriends code and return whether a next page is linked.'''
    return resp.find('class="nextPagingLink"') > 0

def parse_count(resp):
    '''Parse viewFriends code and return the number of friends.'''
    try:
        countPattern = '<option selected="selected" value="all">.*?\\((.*?)\\)</option>'
        return int(filter(is_digit, re.search(countPattern, resp).group(1)))
    except:
        return None

# ###########################
# Cache-related functions
# ###########################

def store_friends(profileID, data):
    '''Store friends of profileID into local cache.'''
    with open('cache/%d.txt' % profileID, 'w') as f:
        pickle.dump(data, f)

def load_friends(profileID):
    '''Returns friends of profileID from local cache, False if not cached.'''
    try:
        with open('cache/%d.txt' % profileID, 'r') as f:
            return pickle.load(f)
    except IOError:
        return False

def store_artist(profileID):
    '''Store data of profileID into local cache.'''
    with open('cache/m%d.txt' % profileID, 'w') as f:
        pickle.dump(True, f)

def load_artist(profileID):
    '''Returns data of profileID from local cache, False if not cached.'''
    try:
        with open('cache/m%d.txt' % profileID, 'r') as f:
            return pickle.load(f)
    except IOError:
        return False


# ###########################
# Auxiliary functions
# ###########################

def is_digit(char): 
    '''Return true if char is a digit.'''
    return ord(char) in range(ord('0'),ord('9')+1)

# ###########################
# Main functions
# ###########################

def get_friends(profileID,limit=1000,useCache=True):
    '''Return friends of profileID with no more than limit friends.'''
    # Return from local file if artist is cached
    if useCache:
        friendIDs = load_friends(profileID)
        if friendIDs is not False:
            return friendIDs
    # Return from the Web otherwise
    friendIDs = []
    page = 0
    while True:
        url = viewFriendsURL % profileID + "&p=1&j=%d" % page
        resp = get_response(url)
        # Break if profile does not belong to an artist
        if not parse_artist(resp):
            friendIDs = None
            break
        # Break if profile has more than limit friends
        if parse_count(resp) > limit and limit is not None:
            friendIDs = None
            break
        friendIDs.extend(parse_friends(resp))
        # Break if there are no more friends pages to parse
        if not parse_more(resp):
            break
        page += 1
        log.info("Scraped %d friends of %s (p.%d)" % (len(friendIDs), profileID, page))
    # Store from Web to local cache
    store_friends(profileID, friendIDs)        
    return friendIDs

def is_artist(profileID):
    '''Return whether profileID belongs to an artist.'''
    # Return from local file if artist is cached
    friendIDs = load_friends(profileID)
    if friendIDs is not False:
        return friendIDs is not None
    # Return from musician file if artist is cached
    if load_artist(profileID) is not False:
        return True
    # Return from the Web otherwise
    url = viewFriendsURL % profileID
    resp = get_response(url)
    artist = parse_artist(resp)
    # If not a musician, store an empty cache file
    if not artist:
        store_friends(profileID, None)
    # If a musician, store in a file
    else:
        store_artist(profileID)
    log.debug("Checked if %d is a musician: %s" % (profileID, artist))
    return artist

def get_closest(profileID=418733388, size=5):
    '''Return the size closest friends of profileID.'''
    friends = get_friends(profileID,limit=None,useCache=False)
    if friends is None:
        log.warn("%d is not a musician" % (profileID))
        return
    log.info("%d has %d friends" % (profileID, len(friends)))
    rank = []
    # Exploring which friends of friends are friends of profileID
    for f, friendID in enumerate(friends):
        fFriendCount = fFriendMutual = 0
        fFriends = get_friends(friendID)
        if fFriends is not None:
            log.info("\t%d/%d) %d has %d friends" % (f+1, len(friends), friendID, len(fFriends)))
            for fF, fFriendID in enumerate(fFriends):
                if fFriendID == profileID:
                    log.info("\t%d/%d)\t%d/%d) %d is seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID))
                else:    
                    fFriendCount += 1
                    if fFriendID in friends:
                        fFriendMutual += 1
                        log.info("\t%d/%d)\t%d/%d) %d friend of %d AND seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID, friendID))
                    else:
                        log.info("\t%d/%d)\t%d/%d) %d not friend of seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID))
        if fFriendCount > 0:
            rank.append([fFriendMutual/float(fFriendCount),friendID,fFriendMutual,fFriendCount])
        log.info("\t%d/%d) %d has %d friends (%d friends of seed)" % 
            (f+1, len(friends), friendID, fFriendCount, fFriendMutual))
    rank.sort()
    rank.reverse()
    topFriends = [i[1] for i in rank[:size] if i[0] > 0]
    log.info("The top friends of %d are: %s" % (profileID, topFriends))
    return rank
     
# This works but takes much longer
# def get_closest_artists(profileID=418733388, size=5):
#     friends = get_friends(profileID,limit=None)
#     if friends is None:
#         log.warn("%d is not a musician" % (profileID))
#         return
#     log.info("%d has %d friends" % (profileID, len(friends)))
#     rank = []
#     # Exploring which friends of friends are friends of profileID
#     for f, friendID in enumerate(friends):
#         fFriendCount = fFriendMutual = 0
#         fFriends = get_friends(friendID)
#         if fFriends is not None:
#             log.info("\t%d/%d) %d has %d friends" % (f+1, len(friends), friendID, len(fFriends)))
#             for fF, fFriendID in enumerate(fFriends):
#                 if fFriendID == profileID:
#                     log.info("\t%d/%d)\t%d/%d) %d is seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID))
#                 else:    
#                     # If fFriend is a friend of profileID, retrieve artist info
#                     if fFriendID in friends:
#                         ffFriends = get_friends(fFriendID)
#                         if ffFriends is not None:
#                             fFriendCount += 1
#                             if profileID in ffFriends:
#                                 fFriendMutual += 1
#                                 log.info("\t%d/%d)\t%d/%d) %d friend of %d AND seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID, friendID))
#                             else:
#                                 log.info("\t%d/%d)\t%d/%d) %d not friend of seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID))
# 
#                     # Else just check whether fFriend is a musician or not
#                     elif is_artist(fFriendID):
#                         fFriendCount += 1
#                         log.info("\t%d/%d)\t%d/%d) %d not friend of seed" % (f+1, len(friends), fF+1, len(fFriends), fFriendID))
#                     else:
#                         log.info("\t%d/%d)\t%d/%d) %d not a musician" % (f+1, len(friends), fF+1, len(fFriends), fFriendID))
#         if fFriendCount > 0:
#             rank.append([fFriendMutual/float(fFriendCount),friendID])
#         log.info("\t%d/%d) %d has %d musician friends (%d friends of seed)" % 
#             (f+1, len(friends), friendID, fFriendCount, fFriendMutual))
#     rank.sort()
#     rank.reverse()
#     topFriends = [i[1] for i in rank[:size] if i[0] > 0]
#     log.info("The top friends of %d are: %s" % (profileID, topFriends))
#     return topFriends


# def getRecommendation(seedID, size=5):
#     pass
     
