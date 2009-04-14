#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides utility functions to parse MySpace URLs and pages.

view_friends_URL
mail_message_URL
parse_friends_URL
"""

import logging
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
mail_to_field        = "ctl00_ctl00_ctl00_cpMain_cpMain_messagingMain_SendMessage_autoCompleteV2_rcptList"
mail_confirm_pattern = "confirmmain"
mail_captcha_pattern = "captcha"
login_email_field    = "ctl00$ctl00$cpMain$cpMain$LoginBox$Email_Textbox"
login_password_field = "ctl00$ctl00$cpMain$cpMain$LoginBox$Password_Textbox"

friends_list_pattern = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"(.*?)>'
# 20090409 The previous pattern changed in April 2009 to the following:
friends_list_pattern = r'<div friendid="([0-9]*?)" class="friendHelperBox"><div><a href="http://www.myspace.com/(.*?)" class="msProfileTextLink"(.*?)>'
page_count_pattern   = '</a> .+ <a .*? class="pagingLink">(.*?)</a> </span><span class="nav_right">'
is_artist_pattern    = "MySpace.Ads.Account = {\"Type\":\"7\""

profile_id_pattern   = '"DisplayFriendId":(.*?),'
profile_name_pattern = '<meta property="myspace:profileType" content="Music" about="(.*?)" typeof="myspace:MusicProfile"'
profile_url_pattern  = '<td><div align="left">&nbsp;&nbsp;.*?<a href="http://www.myspace.com/(.*?)">www.myspace.com/.*?</a>.*?&nbsp;&nbsp;</div></td>'

music_directory_url  = "http://collect.myspace.com/index.cfm?fuseaction=music.directory"

def view_friends_URL(profile, which_page=0):
    '''Returns the URL of the friends page of id.'''
    return view_friends + "%d&p=1&j=%d" % (profile["id"], which_page)

def view_profile_URL(profile):
    '''Returns the URL of the profile page of id.'''
    return view_profile + "%d" % profile["id"]

def mail_message_URL(profile):
    '''Return the URL to mail a message to id.'''
    return mail_message + "%d" % profile["id"]
    
# ###########################
# MySpace friends page parsing
# ###########################

def parse_friends_URL(url, only_id=True):
    '''Return list of friends and, if not only_id, page count and is artist.'''

    def parse_friends_seed_name(friends_page):
        # Unused option to load a profile name from the friends page
        # Unfortunately, depends on the page langauge, and works only by adding
        # cookie manager to open us.myspace.com, or else directly the cookie MSCulture
        # with IPCulture=en-US using ClientCookie in download.py
        seed_name_pattern = '<span class="feature_headtext">&nbsp;amigos de(.*?)</span>'
        try:        
            return re.search(seed_name_pattern, friends_page).group(1)
        except:
            return False

    def parse_friends_list(friends_page):
        '''Returns the list of friend IDs in the page.'''
        friends =  re.findall(friends_list_pattern, friends_page)
        # Remove deleted accounts looking for empty friend[2] 
        matches = [re.search(' title="(.*?)"', f[2]) for f in friends]
        return [{"id": int(friends[i][0]), "name": m.group(1), "url": friends[i][1]} for \
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
            # name = parse_friends_seed_name(resp)
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

    def parse_profile_name(profile_page):
        '''Returns the name of a profile from the profile page.'''
        try:        
            return re.search(profile_name_pattern, profile_page).group(1)
        except:
            return None

    def parse_profile_suffix(profile_page):
        '''Returns the URL suffix from the profile page.'''
        try:        
            return re.search(profile_url_pattern, profile_page).group(1)
        except:
            return None
            # If it's not a musician, then it's
            # <span class="urlLink"><a href="http://www.myspace.com/bellatopa" title="Perfil MySpace para Antonella" class="url">www.myspace.com/bellatopa</a></span>

    resp = download_page(url)
    if resp is None:
        logging.debug("URL error on: %s" % url)
        return None
    id = parse_profile_id(resp)
    if id is None: # TO ADD: and only_artists:
        logging.debug("Profile is not an artist %s" % url)
        return None
    name = parse_profile_name(resp)
    url = parse_profile_suffix(resp)
    return {"id": id, "name": name, "url": url}
