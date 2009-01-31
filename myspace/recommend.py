#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import sys
import getopt
import os
import logging
import threading

from cache import *
from threads import *
from utils import *
from top_friends import *


# SHOULD ADD A PARAMETER FOR A MORE RANDOM BEHAVIOUR?
def build_recommendations(profile, beta=0, size=1, filters=None, cache=None):
    top_friends = load_top_friends(profile, beta, size, filters, cache)
    if top_friends is None:
        logging.debug("No top friends found for %s" % profile)
        return
    top_friends = [friend["profile"] for friend in top_friends]
    recs = []
    for i, friend in enumerate(top_friends):
        friends = load_friends(friend, filters, cache)
        for top in top_friends[i+1:]:
            if not top in [r["to"] for r in recs] and not (top in friends):
                recs.append({"what":friend, "to":top})
                break
    return recs     
    
def send_recommendations(profile, beta=0, size=1, filters=None, cache=None):
    pass
    
# ###########################
# Test functions
# ###########################

class TestRecommend(unittest.TestCase):
    def testRecommend(self):
        # Add meaningful test
        self.assertTrue(True)

# ###########################
# Main functions
# ###########################

def main(argv=None):

    def usage():
        # Add an interactive version to add parameters one by one
        print ("Usage: %s <options> mySpaceUID" % argv[0])
        print ("   options:")
        print ("   -h [--help]  print this usage statement")
        print ("   -t [--test]  only run test")
        print ("   -d [--debug] set more verbose logging")
        print ("   -a [--all]   include also not musician profiles")
        print ("   -m [--min]   <int> specify the minimum friends' pages")
        print ("   -x [--max]   <int> specify the maximum friends' pages")
        print ("   -b [--beta]  <float> specify the popularity bias [0-1]")
        print ("   -s [--size]  <int> specify the number of top friends")
        print ("   -c [--cache] <path> set the path to the cache files")
        print ("   -l [--log]   <path> set the path to the log file")
        return

    min_pages      = 2    # min 80 friends
    max_pages      = 30   # max 1200 friends
    beta           = 0.75
    size           = 10
    only_artists   = True
    profile_id     = None
    cache_path     = None
    log_path       = None
    logging_config = {"level": logging.INFO}
    if argv is None:
        argv = sys.argv
    try:
        ###### 1. Retrieve opts and args #####
        try:
            opts, args = getopt.getopt(argv[1:], "htdac:l:m:x:b:s:", 
            ["help", "test", "debug", "all", "cache=", "log=", 
             "min=", "max=", "beta=", "size="])
        except getopt.error, msg:
             raise Usage(msg)
        ###### 2. Process opts ###### 
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-t", "--test"):
                suite = unittest.TestSuite()
                suite.addTest(unittest.makeSuite(TestRecommend))
                unittest.TextTestRunner(verbosity=2).run(suite)
                sys.exit()
            elif opt in ("-l", "--log"):
                log_path = os.path.expanduser(arg)
                if not os.path.exists(log_path):
                    try:
                        os.mkdir(log_path)
                    except:
                        raise Usage("Could not create log directory")
            elif opt in ("-c", "--cache"):
                cache_path = os.path.expanduser(arg)
                if not os.path.exists(cache_path):
                    try:
                        os.mkdir(cache_path)
                    except:
                        raise Usage("Could not create cache directory")
            elif opt in ("-d", "--debug"):
                logging_config["level"] = logging.DEBUG
            elif opt in ("-a", "--all"):
                only_artists = False
            elif opt in ("-m", "--min"):
                min_pages = read_int(arg)
            elif opt in ("-x", "--max"):
                max_pages = read_int(arg)
            elif opt in ("-b", "--beta"):
                beta = read_float(arg)
            elif opt in ("-s", "--size"):
                size = read_int(arg)
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
        profile = {"id": profile_id}
        filters = {"max_pages": max_pages, "min_pages": min_pages, \
                   "only_artists": only_artists}
        recs = build_recommendations(profile, beta, size, filters, cache_path)
        if recs is not None:
            print "The recommendatios based on profile %s are:" % profile
            for i, rec in enumerate(recs):
                print "%d) Recommend %s to %s" % (i+1, rec["what"], rec["to"])
            #open_connection(email, pwd)
            #result = send_rec_message(...)
        return recs
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())

# 
# def send_rec_message(target_id, target_name, recName, recURL, seedName):
#     '''Send a MySpace message recommending an artist to a target profile.'''
#     url = "http://messaging.myspace.com/index.cfm?fuseaction=mail.message&friendID=%d" % target_id
#     subject = "You like %s, you will love %s" % (seedName, recName)
#     body = '''Hello %s,
# I am MySpace Robot, and I am here to help you discover new music!
# 
# Since you like %s, I think that you might also enjoy a band called %s. 
# Feel free to check out their MySpace at:
# 
# %s
# 
# and then reply to this message telling me if you liked them or not.
# I hope you will enjoy the music! Ciao :) 
# ''' % (target_name, seedName, recName, recURL)
# 
#     fp = ClientCookie.urlopen(url)
#     forms = ClientForm.ParseResponse(fp, backwards_compat=False)
#     fp.close()
#     form = forms[1]
#     form["ctl00$ctl00$ctl00$cpMain$cpMain$messagingMain$SendMessage$subjectTextBox"] = subject
#     form["ctl00$ctl00$ctl00$cpMain$cpMain$messagingMain$SendMessage$bodyTextBox"] = body
#     fp = ClientCookie.urlopen(form.click(id="ctl00_ctl00_ctl00_cpMain_cpMain_messagingMain_SendMessage_btnSend"))
#     result = fp.read()
#     fp.close()
#     return result.find("confirmmain") > 0
# 
# 
# 
# # 179485614 piratas
# # 284314184 go ape
# # 213036694 danger
# # 17442338 placebo
# # 115476392 sux
# # 64481548 subsonica
# # 48154667 amaral
# # 155754525 bon iver
# # 395541002 goremix
# 
