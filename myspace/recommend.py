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
# Main functions
# ###########################


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
                suite.addTest(unittest.makeSuite(TestTopFriends))
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
        return recs
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())

# 
# 
# def usage():
#     # Add an interactive version to add parameters one by one
#     print ("Usage: friends.py <options>")
#     print ("   options:")
#     print ("   -h [--help]    print this usage statement")
#     print ("   -v [--verbose] more info to standard out")
#     print ("   -o [--open]    open closest profiles in a web browser")
#     print ("   -a [--artist]  <mySpaceUID> specify the starting artist ID")
#     print ("   -b [--beta]    <value in [0,1]> specify the popularity bias")
#     print ("   -m [--minimum] <integer> specify the minimum number of friends")
#     print ("   -x [--maximum] <integer> specify the maximum number of pages")
#     print ("   -c [--cache]   <cache path> set the path to the cache folder")
#     print ("   -l [--log]     <log file path> set the path to the log file")
#     return
# 
# 
# 
# def main(argv=None):
#     if argv is None:
#         argv = sys.argv[1:]
#     profileID = 284314184 # By default use Go Ape
#     friends = []
#     grabList = []
#     cachePath = os.path.expanduser("cache")
#     flag_verbose = skip = 0
#     beta = 0.75
#     size = 5
#     minimum = 100
#     openbrowser = False
#     maxPages = 30
# 
#     # Add as parameters maxPages and MIN pages!
#     
#     loggingConfig = {"format":'%(asctime)s %(levelname)-8s %(message)s',
#                      "datefmt":'%Y/%M/%D %H:%M:%S', "level": logging.INFO}
# 
#     try:
#         opts, args = getopt.getopt(argv, "hvoa:l:c:b:s:m:x:", 
#             ["help", "verbose", "open", "artist=", "log=", "cache=", 
#              "beta=", "size=", "minimum=", "maximum="])
#     except getopt.GetoptError, err:
#         print >> sys.stderr, "Poorly specified options..." + str(err)
#         usage()
#         sys.exit(2)
#     if len(opts) < 1:
#         print ("not enough args specified, try again")
#         usage()
#         sys.exit(2)
# 
#     for opt, arg in opts:
#         if opt in ("-h", "--help"):
#             usage()
#             sys.exit()
#         elif opt in ("-l", "--log"):
#             logPath = os.path.expanduser(arg)
#             if not os.path.exists(logPath):
#                 try:
#                     os.mkdir(logPath)
#                 except:
#                     print "Could not create log directory"
#                     usage()
#                     return 183
#             # Should add a log rotator here
#             loggingConfig ={"format":'%(asctime)s %(levelname)-8s %(message)s',
#                              "datefmt":'%Y/%M/%D %H:%M:%S',
#                              "filename":os.path.join(logPath ,"friends.log"),
#                              "filemode":"w", "level": logging.INFO}        
#         elif opt in ("-v", "--verbose"):
#             flag_verbose = True
#             loggingConfig["level"] = logging.DEBUG
#         elif opt in ("-m", "--minimum"):
#             minimum = int(arg)
#         elif opt in ("-x", "--maximum"):
#             maxPages = int(arg)
#         elif opt in ("-a", "--artist"):
#             profileID = int(arg)
#         elif opt in ("-b", "--beta"):
#             beta = float(arg)
#         elif opt in ("-s", "--size"):
#             size = int(arg)
#         elif opt in ("-c", "--cache"):
#              cachePath = os.path.expanduser(arg)
#         else:
#             print "Poorly specified options..."
#             usage()
#             return 4
# 
#     logging.basicConfig(**loggingConfig)
#     
#     logging.info("Estimating closest artist of %d" % profileID)
#     start = time.time()    
#     closest = get_closest_friends(profileID, size, beta, minimum, maxPages, cachePath)
#     logging.info("Elapsed time: %s" % (time.time() - start))
#     print "%d closest of %d: %s" % (len(closest), profileID, closest)
#     if openbrowser:
#         open_closest_friends(closest)
#     recommend_friends(closest, maxPages, cachePath)
# 
# if __name__ == "__main__":
#     sys.exit(main())
# 
# 
# ######### POI C'E' LA PARTE DI SEND!!
# 
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
# def usage():
#     print ("Usage: composer.py <options>")
#     print ("   options:")
#     print ("   -h [--help]     print this usage statement")
#     print ("   -e [--email]    <value> specify e-mail to login to MySpace")
#     print ("   -p [--pwd]      <value> specify password to login to MySpace")
#     print ("   -i [--id]       <mySpaceUID> specify the recipient ID")
#     print ("   -n [--name]     <value> specify the recipient name")
#     print ("   -r [--recname]  <value> specify the recommended profile name")
#     print ("   -u [--recurl]   <url> specify the recommended profile URL")
#     print ("   -s [--seedname] <value> specify the seed profile name")
#     return
# 
# 
# def main(argv=None):
#     if argv is None:
#         argv = sys.argv[1:]
#     
#     email = account.email
#     pwd = account.pwd
#     target_id = 395541002 # goremix
#     target_name = "goremix"
#     recName = "Placebo"
#     recURL = "www.myspace.com/placebo"
#     seedName = "Muse"
#     
#     loggingConfig = {"format":'%(asctime)s %(levelname)-8s %(message)s',
#                      "datefmt":'%Y/%M/%D %H:%M:%S', "level": logging.INFO}
# 
#     try:
#         opts, args = getopt.getopt(argv, "e:p:i:n:r:u:s:", 
#             ["email=", "pwd=", "id=", "name=", "recname=", "recurl=", 
#              "seedname="])
#     except getopt.GetoptError, err:
#         print >> sys.stderr, "Poorly specified options..." + str(err)
#         usage()
#         sys.exit(2)
# #    if len(opts) < 1:
# #        print ("not enough args specified, try again")
# #        usage()
# #        sys.exit(2)
#     for opt, arg in opts:
#         if opt in ("-h", "--help"):
#             usage()
#             sys.exit()
#         elif opt in ("-e", "--email"):
#             email = str(arg)
#         elif opt in ("-p", "--pwd"):
#             pwd = str(arg)
#         elif opt in ("-i", "--id"):
#             target_id = int(arg)
#         elif opt in ("-n", "--name"):
#             target_name = str(arg)
#         elif opt in ("-r", "--recname"):
#             recName = str(arg)
#         elif opt in ("-u", "--recurl"):
#             recURL = str(arg)
#         elif opt in ("-s", "--seedname"):
#             seedName = str(arg)
#         else:
#             print "Poorly specified options..."
#             usage()
#             return 4
# 
#     logging.basicConfig(**loggingConfig)
#     
#     open_connection(email, pwd)
#     result = send_rec_message(target_id, target_name, recName, recURL, seedName)
#     print result
# 
#     # cambia per:
#     # if open_connection():
#     #   for each message:
#     #       send_message():
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
