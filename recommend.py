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
from compose import *
from account import *
from profile import *


# SHOULD ADD A PARAMETER FOR A MORE RANDOM BEHAVIOUR?
def build_recommendations(profile, beta=0, size=1, min_common= 5, filters=None, cache=None):
    '''Build pairs of profile's friends to recommend one to another.'''
    top_friends = load_top_friends(profile, beta, size, min_common, filters, cache)
    if top_friends is None:
        logging.debug("No top friends found for %s" % profile)
        return
#    top_friends = [friend["profile"] for friend in top_friends]
    recs = []
    for i, friend in enumerate(top_friends):
        friends = load_friends(friend, filters, cache)
        for top in top_friends[i+1:]:
            if not top in [r["to"] for r in recs] and not (top in friends):
                recs.append({"what":friend, "to":top})
                break
    return recs
    
def get_message_subject(seed, whom):
    #    try:
    return "You like %s, you will love %s" % (seed["name"], whom["name"])
    #    except KeyError:
    #        return "Music recommendation"


def get_message_body(seed, whom, to):
    template = '''Hello %s,
    I am MySpace Robot, and I am here to help you discover new music!

    Since you like %s, I think that you might also enjoy the music of %s. 
    So check out this MySpace profile: 
    http://www.myspace.com/%s
    and enjoy the music! 

    If you have the time, please reply to this message and tell me if you
    liked this recommendation or not. This would mean a lot to me!
    Ciao :)''' 
    #    try:
    return template % (to["name"], seed["name"], whom["name"], whom["url"])
    #    except KeyError:
    #        return "Music recommendation"


# Here I should pass recommendations, not profile, and call build outside...
def send_recommendations(profile, opts=None, cache=None):
    '''Send MySpace messages for the music recommendations built.'''
    ###### 1. Calculate recommendations for the given profile seed #####
    size, beta, max_messages = opts["size"], opts["beta"], opts["max_messages"]
    min_common = opts["min_common"]
    email, pwd = opts["email"], opts["pwd"]
    recs =  build_recommendations(profile, beta, size, min_common, opts, cache)
    if recs is None:
        logging.debug("No recommendations based on %s" % profile)
        return
    ###### 2. For any target, check if any message has already been sent #####
    cache_ext = "r" # Save recommendations as "<ID>r.txt"
    messages = []
    for rec in recs:
        ## TEMP TO TRY
        sent_to_recipient = from_cache(rec["to"], cache, ext=cache_ext)
        if sent_to_recipient and len(sent_to_recipient) >= max_messages:
            logging.debug("Skipping recommendation %s (enough)" % rec)
        else:
            profile = fill_profile(profile, cache)
            rec["what"] = fill_profile(rec["what"], cache)
            rec["to"] = fill_profile(rec["to"], cache)
            subject = get_message_subject(profile, rec["what"])
            body = get_message_body(profile, rec["what"], rec["to"])
            result = send_message(rec["to"], subject, body, email, pwd)
            if result is False: 
                logging.error("Send error while recommending %s" % rec)
                return False # Because captcha is required                
            if result: # Recipient is not away   
                logging.info("Recommended %s to %s" % (rec["what"], rec["to"]))
                if sent_to_recipient:
                    sent_to_recipient = sent_to_recipient.append(rec)
                else:
                    sent_to_recipient = [rec]
                messages.append(rec)
            to_cache(rec["to"], cache, sent_to_recipient, ext=cache_ext)
    return messages 
    
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
        print ("   -o [--only]  only build messages (without sending them)")
        print ("   -m [--min]   <int> specify the minimum friends' pages")
        print ("   -x [--max]   <int> specify the maximum friends' pages")
        print ("   -b [--beta]  <float> specify the popularity bias [0-1]")
        print ("   -s [--size]  <int> specify the number of top friends")
        print ("   -q [--common]<int> specify the minimum common friends")
        print ("   -g [--msgs]  <int> specify the max messages per profile")
        print ("   -e [--email] <value> specify the e-mail to send messages")
        print ("   -p [--pwd]   <value> specify the password to send messages")
        print ("   -c [--cache] <path> set the path to the cache files")
        print ("   -l [--log]   <path> set the path to the log file")
        return

    min_pages      = 2    # min 80 friends
    max_pages      = 30   # max 1200 friends
    beta           = 0.75
    size           = 10
    min_common     = 5
    max_messages   = 1
    email          = MYSPACE_EMAIL
    pwd            = MYSPACE_PWD
    only_artists   = True
    only_build     = False
    profile_id     = None
    cache_path     = None
    log_path       = None
    logging_config = {"level": logging.INFO}
    if argv is None:
        argv = sys.argv
    try:
        ###### 1. Retrieve opts and args #####
        try:
            opts, args = getopt.getopt(argv[1:], "htdaoc:l:m:x:b:s:g:e:p:q:", 
            ["help", "test", "debug", "all", "only", "cache=", "log=", 
             "min=", "max=", "beta=", "size=", "common=",
             "msgs=", "email=", "pwd=", "name="])
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
            elif opt in ("-o", "--only"):
                only_build = True
            elif opt in ("-m", "--min"):
                min_pages = read_int(arg)
            elif opt in ("-x", "--max"):
                max_pages = read_int(arg)
            elif opt in ("-b", "--beta"):
                beta = read_float(arg)
            elif opt in ("-s", "--size"):
                size = read_int(arg)
            elif opt in ("-q", "--common"):
                min_common = read_int(arg)
            elif opt in ("-e", "--email"):
                email = str(arg)
            elif opt in ("-p", "--pwd"):
                pwd = str(arg)
            elif opt in ("-g", "--msgs"):
                max_messages = read_int(arg)
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
        ###### 5. Retrieve profile name ######
        profile = load_profile({'id':profile_id}, cache_path)
        ###### 6. Retrieve friends ######
        filters = {"max_pages": max_pages, "min_pages": min_pages, \
                   "only_artists": only_artists, "size": size, \
                   "beta": beta, "max_messages": max_messages, \
                   "email": email, "pwd": pwd, "min_common": min_common}
        if only_build:
            recs = build_recommendations(profile, beta, size, min_common, filters, cache_path)
            if recs is not None:
                print "The recommendatios based on profile %s are:" % print_profile(profile, cache_path)
                for i, rec in enumerate(recs):
                    print "%d) Recommend %s to %s" % (i+1, print_profile(rec["what"], cache_path), print_profile(rec["to"], cache_path))
            return recs
        messages_sent = send_recommendations(profile, filters, cache_path)
        if messages_sent:
            print "Sent %d recommendations" % len(messages_sent)
        else:
            print "No recommendation sent"
        return messages_sent



    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())
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
