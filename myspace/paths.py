#!/usr/bin/env python
"""Provides utility functions to parse MySpace URLs and pages.'''

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

friends_list_pattern = r'<a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewProfile&friendID=(.*?)" class="msProfileTextLink"'
page_count_pattern   = '</a> .+ <a .*? class="pagingLink">(.*?)</a> </span><span class="nav_right">'
is_artist_pattern    = "MySpace.Ads.Account = {\"Type\":\"7\""

def view_friends_URL(profile_id, which_page=0):
    '''Returns the URL of the friends page of profile_id.'''
    return view_friends + "%d&p=1&j=%d" % (profile_id, which_page)

def mail_message_URL(profile_id):
    '''Return the URL to mail a message to profile_id.'''
    return mail_message + "%d" % profile_id
    
# ###########################
# MySpace friends page parsing
# ###########################

def parse_friends_URL(url, only_id=True):
    '''Return list of friends and, if not only_id, page count and is artist.'''

    def parse_friends_list(friends_page):
        '''Returns the list of friend IDs in the page.'''
        return map(int, re.findall(friends_list_pattern, friends_page))

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
