#!/usr/bin/env python
"""Provides send_message, for sending a message to a MySpace profile.'''

send_message connects to the MySpace Web page as a registered user, and
send a private message with given subject and body to a recipient profile.

Example usage: python compose.py 395541002 (requires account.py!)
"""

import sys
import getopt
import logging
import urllib
import ClientCookie
import ClientForm
import unittest

from account import *
from paths import *
from utils import *

__author__ = "Claudio Baccigalupo"

def send_message(recipient_id, subject, body, email, password, open=False):
    '''Send a MySpace message to recipient_id with given subject and body.'''
    # 1. Open a connection to MySpace
    if not open:
        open_connection(email, password)
    
    # 2. Open the Web page with the mail form
    url = mail_message_URL(recipient_id)
    form_resp = ClientCookie.urlopen(url)
    forms = ClientForm.ParseResponse(form_resp, backwards_compat=False)
    form_resp.close()
    
    # 3. Fill the form, submit, and return the result
    mail_form = forms[1]
    mail_form[mail_subject_field] = subject
    mail_form[mail_body_field] = body
    send_resp = ClientCookie.urlopen(mail_form.click(id=mail_send_field))
    result = send_resp.read()
    send_resp.close()
    if result.find(mail_confirm_pattern) > 0:
        return True
    if result.find(mail_captcha_pattern) > 0:
        logging.warning("Captcha required. Login manually once, then retry")
    return False
    
def open_connection(email, password):
    '''Log in to MySpace and store login data into a global opener.'''
    # 1. Prepare a cookie jar and a global opener
    jar = ClientCookie.CookieJar()
    opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
    ClientCookie.install_opener(opener)

    # 2. Open the Web page with the login form
    home_resp = ClientCookie.urlopen("http://www.myspace.com")
    forms = ClientForm.ParseResponse(home_resp, backwards_compat=False)
    home_resp.close()
    
    # 3. Fill the login form and submit
    login_form = forms[1]
    login_form[login_email_field] = email
    login_form[login_password_field] = password
    login_resp = ClientCookie.urlopen(login_form.click())
    result = login_resp.read()
    login_resp.close()
    with open("exit.html", 'w') as f:
        f.write(result)

    # 4. Check if login was successful
    try:        
        loginPatt = '"UserId":(.*?),'
        profile_id = int(re.search(loginPatt, result).group(1))
        return profile_id > 0
    except (TypeError, ValueError, AttributeError):
        return False


# ###########################
# Main functions
# ###########################


def main(argv=None):

    def usage():
        print ("Usage: %s <options> mySpaceUID" % argv[0])
        print ("   options:")
        print ("   -h [--help]    print this usage statement")
        print ("   -d [--debug]   set more verbose logging")
        print ("   -e [--email]   <value> specify e-mail to login with")
        print ("   -p [--pwd]     <value> specify password to login with")
        print ("   -s [--subject] <text> specify the subject of the message")
        print ("   -b [--body]    <text> specify the body of the message")
        print ("   -l [--log]     <file path> set the path to the log file")
        return

    email          = MYSPACE_EMAIL
    pwd            = MYSPACE_PWD
    subject        = "Test message"
    body           = "This is a test message"
    log_path       = None
    logging_config = {"level": logging.INFO}
    profile_id     = None
    if argv is None:
        argv = sys.argv
    try:
        ###### 1. Retrieve opts and args #####
        try:
            opts, args = getopt.getopt(argv[1:], "he:p:s:b:", 
                ["help", "email=", "pwd=", "subject=", "body="])
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
            elif opt in ("-e", "--email"):
                email = str(arg)
            elif opt in ("-p", "--password"):
                pwd = str(arg)
            elif opt in ("-s", "--subject"):
                subject = str(arg)
            elif opt in ("-b", "--body"):
                body = str(arg)
        ###### 3. Process args ######
        if len(args) < 1:
            raise Usage("You did not specify a recipient MySpaceUID")
        elif len(args) > 1:
            raise Usage("You specified more than one recipient MySpaceUID")
        else:
            profile_id = read_int(args[0])
        ###### 4. Enable logging ######
        logging_config["format"] = '%(asctime)s %(levelname)-8s %(message)s'
        logging_config["datefmt"] = '%Y/%M/%D %H:%M:%S'
        if log_path is not None:        
            logging_config["filename"] = os.path.join(log_path, "friends.log")
            logging_config["filemode"] = "w"
        logging.basicConfig(**logging_config)
        ###### 5. Send message ######
        if not open_connection(email, pwd):
            logging.error("Could not login %s to MySpace" % email)
            return 3
        result = send_message(profile_id, subject, body, email, pwd, open=True)
        if not result:
            logging.error("Could not send message to %s" % profile_id)
        else:
            logging.info("Message sent from %s to %d" % (email, profile_id))
        return result
    ###### Manage errors ######
    except Usage, err:
        print >>sys.stderr, err.msg
        usage()
        return 2

if __name__ == "__main__":
    sys.exit(main())


# ###########################
# Test functions
# ###########################

class TestCompose(unittest.TestCase):

    def testCompose(self):
        # Test that you can send a message to goremix
        self.assertTrue(send_message(395541002, "testCompose", "testBody", \
            MYSPACE_EMAIL, MYSPACE_PWD))
        # Add more tests if needed

