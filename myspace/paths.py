#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides utility functions to parse MySpace URLs and pages.

view_friends_URL
mail_message_URL
parse_friends_URL
"""

import re

from download import download_page
from utils import is_digit

__author__ = "Claudio Baccigalupo"

# ###########################
# MySpace common URLs and fields
# ###########################

view_friends         = "http://friends.myspace.com/index.cfm?fuseaction=user.viewfriends&friendID="
view_profile         = "http://profile.myspace.com/index.cfm?fuseaction=user.viewprofile&friendID="
mail_message         = "http://messaging.myspace.com/index.cfm?fuseaction=mail.message&friendID="

mail_subject_field   = "ctl00$ctl00$ctl00$cpMain$cpMain$messagingMain$SendMessage$subjectTextBox"
mail_body_field      = "ctl00$ctl00$ctl00$cpMain$cpMain$messagingMain$SendMessage$bodyTextBox"
mail_send_field      = "ctl00_ctl00_ctl00_cpMain_cpMain_messagingMain_SendMessage_btnSend"
mail_confirm_pattern = "confirmmain"
login_email_field    = "ctl00$ctl00$cpMain$cpMain$LoginBox$Email_Textbox"
login_password_field = "ctl00$ctl00$cpMain$cpMain$LoginBox$Password_Textbox"

friends_list_pattern = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"(.*?)>'
page_count_pattern   = '</a> .+ <a .*? class="pagingLink">(.*?)</a> </span><span class="nav_right">'
is_artist_pattern    = "MySpace.Ads.Account = {\"Type\":\"7\""

profile_id_pattern   = '"DisplayFriendId":(.*?),'

def view_friends_URL(id, which_page=0):
    '''Returns the URL of the friends page of id.'''
    return view_friends + "%d&p=1&j=%d" % (id, which_page)

def view_profile_URL(id, which_page=0):
    '''Returns the URL of the profile page of id.'''
    return view_profile + "%d" % id

def mail_message_URL(id):
    '''Return the URL to mail a message to id.'''
    return mail_message + "%d" % id
    
# ###########################
# MySpace friends page parsing
# ###########################

def parse_friends_URL(url, only_id=True):
    '''Return list of friends and, if not only_id, page count and is artist.'''

    def parse_friends_list(friends_page):
        '''Returns the list of friend IDs in the page.'''
        friends =  re.findall(friends_list_pattern, friends_page)
        # Remove deleted accounts looking for empty friend[1]
        matches = [re.search(' title="(.*?)"', f[1]) for f in friends]
        return [{"id": int(friends[i][0]), "name": m.group(1)} for \
            i, m in enumerate(matches) if m is not None]

    def parse_friends_page_count(friends_page):
        '''Returns the number of friends pages in the page.'''
        match = re.search(page_count_pattern, friends_page)
        try:        
            return int(filter(is_digit, match.group(1)))
        except:
            return 1

    def parse_friends_is_artist(friends_page):
        '''Returns True if the page belongs to a musician.'''
        return friends_page.find(is_artist_pattern) > 0

    resp = download_page(url)
    friends = count_pages = is_artist = None
    if resp is None:
        logging.debug("URL error on: %s" % url)
    else:
        friends = parse_friends_list(resp)
        if not only_id:
            count_pages = parse_friends_page_count(resp)
            is_artist = parse_friends_is_artist(resp)
    if only_id:
        return friends
    else:
        return friends, count_pages, is_artist


# ###########################
# MySpace profile page parsing
# ###########################

def parse_profile_URL(url, only_artists=True):
    '''Return detail of profile. As for now, implemented ONLY for artists.'''

    def parse_profile_id(profile_page):
        '''Returns the ID of a profile from the profile page.'''
        match = re.search(profile_id_pattern, profile_page)
        try:        
            return int(filter(is_digit, match.group(1)))
        except:
            return None

    # Other functions to implement here

    resp = download_page(url)
    if resp is None:
        logging.debug("URL error on: %s" % url)
        return None
    id = parse_profile_id(resp)
    if id is None: # TO ADD: and only_artists:
        logging.debug("Profile is not an artist %s" % url)
        return None
    # name = parse_profile_name(resp)
    # suffix = parse_profile_suffix(resp)
    # last_login = parse_profile_last_login(resp)
    # count_friends = parse_profile_count_friends(resp)
    # count_top_friends = parse_profile_count_top_friends(resp)
    return {"id": id}
    # TO DO: return {"id": id, "name": name, "suffix": suffix, et cetera}
