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

from paths import view_profile_URL, parse_profile_URL
from threads import *
from utils import *
from cache import *

__author__ = "Claudio Baccigalupo"

def scrape_profile(profile, only_artists=True):
    '''Return details of a MySpace profile as a dictionary.'''
    url = view_profile_URL(profile)
    new_profile = parse_profile_URL(url, only_artists)
    logging.debug("Loaded profile of %s (from MySpace)" % profile)
    return new_profile

def load_profile(profile, cache=None):
    '''Retrieve all the friends of id either from cache or the web.'''
    ###### 1. Load from cache if available #####
    # sys.exit()
    new_profile = from_cache(profile, cache, ext="p")
    #logging.info("new profile: %s " % (new_profile))
    if new_profile is not False:
        return new_profile
    ###### 2. Load from web and store in cache otherwise #####
    new_profile = scrape_profile(profile)
    to_cache(profile, cache, new_profile, ext="p")
    return new_profile

def print_profile(profile, cache=None):
    if 'name' not in profile:
        profile = load_profile(profile, cache)
    return "%s [%d]" % (profile['name'], profile['id'])

def fill_profile(profile, cache=None):
    if 'name' not in profile or 'url' not in profile:
        profile = load_profile(profile, cache)
    return profile
        


# ###########################
# Main functions
# ###########################

def main(argv=None):

    def usage():
        # Add an interactive version to add parameters one by one
        print ("Usage: %s <options> mySpaceUID" % argv[0])
        print ("   options:")
        print ("   -h [--help]  print this usage statement")
        print ("   -c [--cache] <path> set the path to the cache files")
        print ("   -d [--debug] set more verbose logging")
        print ("   -l [--log]   <path> set the path to the log file")
        return

    profile_id     = None
    cache_path     = None
    log_path       = None
    logging_config = {"level": logging.INFO}
    if argv is None:
        argv = sys.argv
    try:
        ###### 1. Retrieve opts and args #####
        try:
            opts, args = getopt.getopt(argv[1:], "hdc:l:", 
            ["help", "cache=", "log="])
        except getopt.error, msg:
             raise Usage(msg)
        ###### 2. Process opts ###### 
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-l", "--log"):
                log_path = os.path.expanduser(arg)
                if not os.path.exists(log_path):
                    try:
                        os.mkdir(log_path)
                    except:
                        raise Usage("Could not create log directory")
            elif opt in ("-d", "--debug"):
                logging_config["level"] = logging.DEBUG
            elif opt in ("-c", "--cache"):
                cache_path = os.path.expanduser(arg)
                if not os.path.exists(cache_path):
                    try:
                        os.mkdir(cache_path)
                    except:
                        raise Usage("Could not create cache directory")
        ###### 3. Process args ######
        if len(args) < 1:
            raise Usage("You did not specify a MySpaceUID")
        elif len(args) > 1:
            raise Usage("You specified more than one MySpaceUID")
        else:
            profile_id = read_int(args[0])
        ###### 4. Enable logging ######
        logging_config["format"] = '%(asctime)s %(levelname)-8s %(message)s'
        logging_config["datefmt"] = '%Y/%M/%D %H:%M:%S'
        if log_path is not None:        
            logging_config["filename"] = os.path.join(log_path, "friends.log")
            logging_config["filemode"] = "w"
        logging.basicConfig(**logging_config)
        ###### 5. Retrieve friends ######
        profile = load_profile({'id': profile_id}, cache_path)
        return profile
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())

