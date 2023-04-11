"""
Library to manage checking Scopus with current authentication tokens

Script attempts arbitrary download using auth tokens and checks whether abstract received

haselwimmer@gmail.com 04/04/2023
"""

import sys
import os
import json
import time
import pwd
import grp
import requests
from datetime import datetime, timedelta

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir, os.path.pardir))
xrisk_dir = os.path.abspath(os.path.join(parent_dir, 'x-risk'))
sys.path.append(parent_dir)
sys.path.append(xrisk_dir)

import adminconfig

# Number of days before token expiry date to start sending reminders
EXPIRYREMINDERWINDOW = 30

# Location of tokenchecker file that caches most recent live test run of tokens
TOKENCHECKERFILE = 'tokenchecker.json'

# Create tokenchecker file file if not exists
TOKENCHECKERFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tokenchecker", TOKENCHECKERFILE)
if os.path.isfile(TOKENCHECKERFILE) is False:
    with open(TOKENCHECKERFILE, 'w') as f:
        json.dump({'SUCCESS': True, 'LASTSAVED': str(datetime.now())}, f, indent=4)
    # Change file owner so Apache can modify
    uid = pwd.getpwnam(adminconfig.WWW_USER).pw_uid
    gid = grp.getgrnam(adminconfig.WWW_USER).gr_gid
    os.chown(TOKENCHECKERFILE, uid, gid)

"""
Class for managing token checking
"""
class tokenchecker():

    def __init__(self):
        """
        Initialize class including loading stored API credentials
        """

        self.base_url = u'https://api.elsevier.com/content/search/scopus/'
        self.elsversion = '0.3.2'
        self.testquery = "TITLE-ABS-KEY%28%22human+extinction%22%29+AND+PUBYEAR+%3D+2000&view=COMPLETE"
        self.actualtokens = True

        # Load stored Elsevier API credentials by default
        config_file = os.path.join(parent_dir, "x-risk/config.json")
        with open(config_file, 'r') as f:
            elsevierconfig = json.load(f)
            self.apikey = elsevierconfig['apikey']
            self.insttoken = elsevierconfig['insttoken']
            self.expirydate = elsevierconfig['expirydate']

    def settokens(self, apikey, insttoken):
        """
        Override stored credentials
        """

        self.apikey = apikey
        self.insttoken = insttoken
        self.actualtokens = False

    def savetokens(self, apikey, insttoken, expirydate):
        """
        Save credentials
        """

        self.apikey = apikey
        self.insttoken = insttoken
        self.expirydate = expirydate
        self.actualtokens = True

        config_file = os.path.join(parent_dir, "x-risk/config.json")
        with open(config_file, 'w') as f:
            json.dump({'apikey': apikey, 'insttoken': insttoken, 'expirydate': expirydate}, f, indent=4)

        # We're only saving tokens that have been successfully verified
        self.statustocache(True)

    def cachedstatus(self):
        """
        Get lastest run of call to Elsevier API using cache file        
        """

        parsed_json = {'SUCCESS': False}
        with open(TOKENCHECKERFILE) as f:
            parsed_json = json.load(f)

        return parsed_json            

    def statustocache(self, success):
        """
        Cache latest run to prevent excessive calls to Elsevier API
        """

        if (self.actualtokens):
            with open(TOKENCHECKERFILE, 'w') as f:
                json.dump({'SUCCESS': success, 'LASTSAVED': str(datetime.now())}, f, indent=4)

    def expiressoon(self):
        """
        Checks whether tokens are due to expire soon
        """

        reminderdate = datetime.strptime(self.expirydate, '%Y-%m-%d') - timedelta(days=EXPIRYREMINDERWINDOW)

        if (datetime.now() > reminderdate):
            return True
        return False

    def run(self):
        """
        Run token checker
        """

        # Create URL to load from query and Elsevier endpoint
        url = self.base_url + '?query=' + self.testquery

        # Run query with error checking
        headers = {
            "X-ELS-APIKey"  : self.apikey,
            "User-Agent"    : "elsapy-v%s" % self.elsversion,
            "Accept"        : 'application/json'
            }
        if self.insttoken: headers["X-ELS-Insttoken"] = self.insttoken
        r = requests.get(
            url,
            headers = headers
            )
        if r.status_code == 200:
            results = json.loads(r.text)

            # We check first entry to see if it has 'dc:description' field
            firstentry = results['search-results']['entry'][0]

            if 'dc:description' in firstentry:
                self.statustocache(True)
                return {'SUCCESS': True, 'OBJ': self, 'DATA': firstentry['dc:description'][:40] + "..."}
            else:
                self.statustocache(False)
                return {'SUCCESS': False, 'OBJ': self, 'DATA': "Missing 'dc:description' field from sample entry"}

        else:
            try:
                error_message = json.loads(r.text)

                # Try and extract human-readable error for non-technical users
                if 'service-error' in error_message:
                    error_message = error_message['service-error']
                    if 'status' in error_message:
                        error_message = error_message['status']
                        if 'statusText' in error_message:
                            error_message = error_message['statusText']

                if 'error-response' in error_message:
                    error_message = error_message['error-response']
                    if 'error-message' in error_message:
                        error_message = error_message['error-message']

                if type(error_message) is dict:
                    error_message = json.dumps(error_message)

            except ValueError as e:
                error_message = r.text

            self.statustocache(False)
            return {'SUCCESS': False, 'OBJ': self, 'DATA': error_message}
