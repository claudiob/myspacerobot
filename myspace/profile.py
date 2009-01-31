#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides scrape_profile, for listing the detail of a MySpace profile.

scrape_profile connects to the MySpace Web page, retrieves the name, URL 
suffix, last login, number of friends and total friends of a MySpace profile.

NOTE: This function is not yet implemented

Example usage: python profile.py 395541002
"""

import sys
import getopt
import os
import logging
import unittest

from paths import view_friends_URL, parse_friends_URL
from threads import *
from utils import *

__author__ = "Claudio Baccigalupo"

def scrape_profile(id, only_artists=True):
    '''Return details of a MySpace profile as a dictionary.'''
    url = view_profile_URL(id)
    details = parse_profile_URL(url, only_artists)
    return details
