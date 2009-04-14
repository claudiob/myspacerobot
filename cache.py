#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides from_cache and to_cache, for loading/storing data to hard disk.

from_cache returns local data related to id from cache dir.
to_cache stores into a local file in cache dir data related to id.

Test usage: python cachhe.py
"""

from __future__ import with_statement # Backward compatibility with Python 2.5
import os
import pickle
import unittest
import re
import logging

from download import download_page
from utils    import is_digit, flatten
from threads  import call_threaded

__author__ = "Claudio Baccigalupo"


# Could move every main function in this file, like this:
# # RECOMMEND.PY
# 
# def send_recommendations(triples, opts=None, cache=None):
#     '''For each triple T, recommend T[what] T[to] based on T[for].'''
#     count_messages = 0
#     for triple in triples:
#         target_id   = triple["to"]
#         target_sent = get_profile_key(target_id, "triples", cache) or []
#         # 1. Check the target has not received enough recommendations #####
#         if target_send and len(target_sent) >= max_messages:
#             logging.debug("Skipping target %d (enough sent)" % target_id)
#             continue
#         # 2. Prepare body and subject and send the message    
#         subject     = build_message_subject(triple)
#         body        = build_message_body(triple)
#         outcome     = send_message({'id' : target_id}, subject, body, email, pwd)
#         if not outcome: 
#             logging.error("Send error while recommending %s" % rec)
#             continue
#             ### return False ## Write sys.exit within the captcha!!
#         logging.info("Recommended %s to %s" % (triple["what"], triple["to"]))
#         target_sent.append(triple) 
#         set_profile_key(target_id, "triples", cache, target_sent)
#         count_messages = count_messages + 1
#     logging.info("Sent %d recommendations" % count_messages)
#     return messages 
# 
# 
# ### SCRAPE.PY
# 
# def load_profile_key(index, key, cache, overwrite=True, value=None):
#     # 1. If called with profile suffix, check which is the MySpaceUID #####
#     if str(index).isdigit():
#         id = index
#     else:
#         id = scrape_profile_keys(index, "id", cache)["id"]
#     # 2. Try to retrieve the profile from local cache #####
#     profile = from_cache({'id': id}, cache) or {}
#     if not key:
#         return profile
#     # 3. Update the profile if required to do so #####
#     if (key not in profile) or overwrite:
#         if value:
#             profile.update({key: value})
#         else:
#             profile.update(scrape_profile_keys(id, key, cache))
#         to_cache({'id':id}, cache, profile)
#     if key not in profile:
#         logging.info("Key '%s' not found for profile %d" % (key, id))
#         return None
#     return profile[key]
# 
# def get_profile_key(id, key, cache):
#     return load_profile_key(id, key, cache, overwrite=False, value=None)
# 
# def set_profile_key(id, key, cache, value):
#     return load_profile_key(id, key, cache, overwrite=True, value=value)
# 
# def scrape_profile_keys(id, key, cache):
#     if key in ["id", "name", "suffix"]:
#         return scrape_profile_page(id)
#     elif key in ["friends", "is_artist"]: # "page_count"
#         return scrape_friends_page(1, id, cache)
#     else:
#         return {}
# 
# def scrape_profile_page(index):
#     '''Scrape a MySpace profile page and return name and URL suffix.'''    
# 
#     def parse_profile_id(html):
#          '''Returns the ID of a profile from the profile page.'''
#          pattern_profile_id = '"DisplayFriendId":(.*?),'
#          match = re.search(pattern_profile_id, html) if html else None
#          if match:
#              return int(filter(is_digit, match.group(1)))
#          else:
#              logging.warning("No ID found for profile")
#              return None
#     
#     def parse_profile_name(html):
#         '''Parse the profile page for the profile name.'''
#         pattern_profile_name = '<meta property="myspace:profileType" content="Music" about="(.*?)" typeof="myspace:MusicProfile" >'       
#         match = re.search(pattern_profile_name, html) if html else None
#         if match:
#             return match.group(1)
#         else:
#             logging.warning("No name found for profile")
#             return None
#     
#     def parse_profile_suffix(html):
#         '''Parse the profile page for the myspace.com/<URL suffix>.'''
#         pattern_profile_suffix = '<td><div align="left">&nbsp;&nbsp;.*?<a href="http://www.myspace.com/(.*?)">www.myspace.com/.*?</a>.*?&nbsp;&nbsp;</div></td>'
#         match = re.search(pattern_profile_suffix, html) if html else None
#         if match:
#             return match.group(1)
#         else:
#             # Try with the non-musician version of the pattern
#             pattern_profile_suffix = '<span class="urlLink"><a href="http://www.myspace.com/(.*?)".*?>www.myspace.com/.*?</a></span>'
#             match = re.search(pattern_profile_suffix, html) if html else None
#             if match:
#                 return match.group(1)
#             else:
#                 logging.warning("No URL suffix found for profile")
#                 return None
#     # Consider index as the MySpaceID if integer, else as MySpaceSuffix
#     if str(index).isdigit():
#         view_profile_prefix = "http://profile.myspace.com/index.cfm?fuseaction=user.viewprofile&friendID="
#         profile_page        = download_page(view_profile_prefix + str(index))
#         id, suffix          = int(index), parse_profile_suffix(profile_page)
#     else:
#         main_profile_prefix = "http://www.myspace.com/"
#         profile_page        = download_page(main_profile_prefix + str(index))
#         id, suffix          = parse_profile_id(profile_page), str(index)
#     name = parse_profile_name(profile_page)
#     return {"id": id, "name": name, "suffix": suffix}
# 
# def scrape_friends_page(page, id, cache):
#     '''Scrape a friends page and return list of friends, is artist, #pages.'''    
#     def parse_friends_list(html, cache):
#         '''Returns the list of friend IDs in the page and subsequent pages.'''
#         ##### 1. Retrieve the number of friends pages #####
#         pattern_friends_list = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"(.*?)>'
#         friends = re.findall(pattern_friends_list, html) if html else None
#         # Filter out deleted accounts looking for empty friend[1]
#         matches = [re.search(' title="(.*?)"', f[1]) for f in friends]
#         friends_list = []
#         for i, m in enumerate(matches):
#             if m is not None:
#                 friend_id =  int(friends[i][0])
#                 friend_name = m.group(1)
#                 # Store newfound friends to cache
#                 set_profile_key(friend_id, "name", cache, friend_name)
#                 friends_list.append(friend_id)
#         return friends_list
#     
#     def parse_friends_page_count(html):
#         '''Returns the number of friends pages in the page.'''
#         pattern_page_count = '</a> .+ <a .*? class="pagingLink">(.*?)</a> </span><span class="nav_right">'
#         match = re.search(pattern_page_count, html) if html else None
#         if match:        
#             return int(filter(is_digit, match.group(1)))
#         else:
#             logging.debug("No page count for profile- returning 1")
#             return 1
#     
#     def parse_friends_is_artist(html):
#         '''Returns True if the page belongs to a musician.'''
#         pattern_is_artist = "MySpace.Ads.Account = {\"Type\":\"7\""
#         return html.find(pattern_is_artist) > 0
#     
#     logging.debug("Scraping friends of %d, page %d" % (id, page))
#     view_friends_prefix = "http://friends.myspace.com/index.cfm?fuseaction=user.viewfriends&friendID="
#     view_friends_URL    = view_friends_prefix + "%d&p=1&j=%d" % (id, page)
#     friends_page = download_page(view_friends_URL)
#     friends_keys = {}
#     friends      = parse_friends_list(friends_page, cache)
#     logging.debug("Scraped friends of %d, page %d" % (id, page))
#     if page > 1:
#         return friends    
#     is_artist    = parse_friends_is_artist(friends_page)
#     page_count   = parse_friends_page_count(friends_page)
#     more_pages   = range(2, page_count)
#     params       = {"id": id, "cache": cache}
#     more_friends = call_threaded(scrape_friends_page, more_pages, \
#                                  queueSize=20, params=params)
#     friends.extend(flatten(more_friends))        
#     logging.debug("Scraped all %d friends of %s" % (len(friends), id))
#     return {"friends": friends, "is_artist": is_artist}
# 

### CACHE.PY

def get_cache_path(profile, cache_dir, ext=None):
    '''Convert 123456789012 into [cache_dir]/123/456/789/012[ext].txt.'''
    path = "/".join([str(profile["id"]).zfill(12)[3*i:3*i+3] for i in range(4)])
    if ext is not None:
        path = path + ext
    return os.path.join(cache_dir, path + ".txt")

def from_cache(profile, cache_dir, ext=None):
    '''Return data of id from cache, False if error.'''
    try:
        path = get_cache_path(profile, cache_dir, ext)
        with open(path, 'r') as f:
            return pickle.load(f)
    except (IOError, TypeError, AttributeError):
        return False

def to_cache(profile, cache_dir, data, ext=None):
    '''Store data into local file, False if error.'''
    try:
        path = get_cache_path(profile, cache_dir, ext)
        folder = os.path.split(path)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, 'w') as f:
            pickle.dump(data, f)
        return True
    except (IOError, TypeError, OSError, AttributeError):
        return False
 
class TestCache(unittest.TestCase):
    
    def setUp(self):
        self.id = 999999999999
        self.cache_dir = "cache"
        self.path = get_cache_path(self.id, self.cache_dir)
    
    def tearDown(self):
        if os.path.exists(self.path): 
            os.remove(self.path) 
        
    def testCache(self):
        to_cache(self.id, self.cache_dir, "Test")
        self.assertEqual("Test", from_cache({'id': self.id}, self.cache_dir))

if __name__ == '__main__':
    unittest.main()
                