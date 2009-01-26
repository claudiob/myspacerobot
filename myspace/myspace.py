#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import re
from urltry import *
from utils import is_digit

baseURL = "http://friends.myspace.com/" # "http://216.178.38.204/"
viewFriendsURL = baseURL + "index.cfm?fuseaction=user.viewfriends&friendID="
viewProfileURL = baseURL + "index.cfm?fuseaction=user.viewprofile&friendid="

def get_friends_URL(profileID, page=0):
    '''Returns the URL of the friends page of profileID.'''
    return viewFriendsURL + "%d&p=1&j=%d" % (profileID, page)

# ###########################
# MySpace friends parse functions
# ###########################

def parse_friends(url, complete=False):
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

def parse_friends_list(friendsPage):
    '''Returns the list of friend IDs in the page.'''
    friendPatt = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"'
    return map(int, re.findall(friendPatt, friendsPage))

def parse_friends_page_count(friendsPage):
    '''Returns the number of friends pages in the page.'''
    pagesPatt = '</a> .+ <a .*? class="pagingLink">(.*?)</a> </span><span class="nav_right">'
    try:        
        c = int(filter(is_digit, re.search(pagesPatt, friendsPage).group(1)))
    except:
        c = 1
    return c
    
def parse_friends_is_musician(friendsPage):
    '''Returns True if the page belongs to a musician.'''
    musicianPatt = "MySpace.Ads.Account = {\"Type\":\"7\""
    return friendsPage.find(musicianPatt) > 0

