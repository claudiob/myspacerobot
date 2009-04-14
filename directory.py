#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import sys
import getopt
import os
import logging
import threading

from recommend import *



page_count_directory_pattern = '<a href="javascript:NextPage(.*?)">(.*?)</a>(\s*?)</td>'
artists_list_pattern = r'<td><a href="http://profile\.myspace\.com/index\.cfm\?fuseaction=user\.viewprofile\&friendID=(.*?)">(.*?)</a></td>'

def parse_artists_URL(which_page=0):
    '''Return list of musiciands and, if not only_id, page count.'''

    def parse_directory_page_count(directory_page):
        '''Returns the number of artists pages in the page.'''
        match = re.search(page_count_directory_pattern, directory_page)
        try:        
            return int(filter(is_digit, match.group(2)))
        except:
            return 1

    def parse_artists_list(directory_page):
        '''Returns the list of musicians IDs in the page.'''
        artists =  re.findall(artists_list_pattern, directory_page)
        return [{"id": int(f[0]), "name": f[1]} for f in artists]
        
        
    url = music_directory_url + "&page=%d" % which_page
    resp = download_page(url)
    artists = count_pages = None
    if resp is None:
        logging.debug("URL error on: %s" % url)
        return None
    else:
        artists = parse_artists_list(resp)
    return artists

# def scrape_directory():
#     '''Retrieve all the MySpace musicians from the web that satisfy filters.'''
#     url = music_directory_URL()
#     artists, count_pages = parse_artists_URL(url, only_id=False)
#     if count_pages is None:
#         logging.debug("Error retrieving directory")
#         artists = None
#     else:
#         pages = range(1, count_pages) # For each page after the first
#         URLs = [music_directory_URL(page) for page in pages]
#         more_artists = call_threaded(parse_artists_URL, URLs, queueSize=20)
#         artists.extend(flatten(more_artists))
#         logging.debug("Loaded %d artists in directory (from MySpace)" % len(artists))
#     return artists
# 
# def load_directory(cache=None):
#     '''Retrieve all the MySpace musicians either from cache or the web.'''
#     ###### 1. Load from cache if available #####
#     # sys.exit()
#     directory = from_cache({'id': 0}, cache, ext="d")
#     if directory is not False:
#         logging.debug("Loaded %d artists in directory (from cache)" % len(directory))
#         return directory
#     ###### 2. Load from web and store in cache otherwise #####
#     directory = scrape_directory()
#     to_cache({'id': 0}, cache, directory, ext="d")
#     return directory




# ###########################
# Main functions
# ###########################

def main(argv=None):

    def usage():
        # Add an interactive version to add parameters one by one
        print ("Usage: %s <options>" % argv[0])
        print ("   options:")
        print ("   -h [--help]  print this usage statement")
        print ("   -t [--test]  only run test")
        print ("   -d [--debug] set more verbose logging")
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
            opts, args = getopt.getopt(argv[1:], "htdoc:l:m:x:b:s:g:e:p:q:", 
            ["help", "test", "debug", "only", "cache=", "log=", 
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
        if len(args) > 0:
            raise Usage("You specified too many parameters")
        ###### 4. Enable logging ######
        logging_config["format"] = '%(asctime)s %(levelname)-8s %(message)s'
        logging_config["datefmt"] = '%Y/%M/%D %H:%M:%S'
        if log_path is not None:        
            logging_config["filename"] = os.path.join(log_path, "friends.log")
            logging_config["filemode"] = "w"
        logging.basicConfig(**logging_config)
        filters = {"max_pages": max_pages, "min_pages": min_pages, \
                   "only_artists": False, "size": size, "min_common": min_common, \
                   "beta": beta, "max_messages": max_messages, \
                   "email": email, "pwd": pwd}
        ###### 5. Retrieve directory ######
        which_page = 0
        while True:
            artists_set = parse_artists_URL(which_page)
            if artists_set is None or which_page > 1:
                break
            which_page +=1
            logging.debug("Directory page #%d;  artists: %s" % (which_page, artists_set))
            for profile in artists_set:
                if only_build:
                    recs = build_recommendations(profile, beta, size, min_common, filters, cache_path)
                    if recs is not None:
                        print "The recommendatios based on profile %s are:" % print_profile(profile, cache_path)
                        for i, rec in enumerate(recs):
                            print "%d) Recommend %s to %s" % (i+1, print_profile(rec["what"], cache_path), print_profile(rec["to"], cache_path))
                    return recs
                messages_sent = send_recommendations(profile, filters, cache_path)
                if messages_sent:
                    print "Page %d, sent %d recommendations for %s" % (which_page, len(messages_sent), print_profile(profile, cache_path))
                else:
                    print "Page %d, no recommendation sent for %s" % (which_page, print_profile(profile, cache_path))
        # return something
            

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
