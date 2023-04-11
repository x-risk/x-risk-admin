"""
Library to manage one-time passcode for modifying Elsevier authentication tokens
One-time passcode is emailed to admin contact so they can easily modify authentication 
tokens through web browser without need for remembering login details
Passcode is send to ../config.py/ADMINCONTACTEMAIL

Created by sh801, 1st April 2023
"""

import os
import time
import json
import secrets
import pwd
import grp
import adminconfig

# Location of current passcode file
PASSCODEFILE = 'passcode.json'

# Value to indicate passcode is reset
PASSCODERESET = ''

# Expiry time of passcode in minutes 
PASSCODEEXPIRYTIME = 24 * 60

# Time between passcode checks in seconds to prevent brute-force attacks
PASSCODETIMEDELAYS = 1

# Create current passcode file if not exists
PASSCODEFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "passcode", PASSCODEFILE)
if os.path.isfile(PASSCODEFILE) is False:
    with open(PASSCODEFILE, 'w') as f:
        json.dump({'CURRENTPASSCODE': PASSCODERESET, 'MODIFIED': str(time.time()), 'LASTCHECKED': str(time.time())}, f, indent=4)
    # Change file owner so Apache can modify
    uid = pwd.getpwnam(adminconfig.WWW_USER).pw_uid
    gid = grp.getgrnam(adminconfig.WWW_USER).gr_gid
    os.chown(PASSCODEFILE, uid, gid)


class passcode():
    """
    Class to manage passcode
    """

    def __init__(self):
        """
        Init class
        """

        self.refreshfromstore()

    def refreshfromstore(self):
        """
        Load values from current passcode file
        """

        f = open(PASSCODEFILE)
        currentpasscode = json.load(f)
        self.CURRENTPASSCODE = currentpasscode['CURRENTPASSCODE']
        self.MODIFIED = float(currentpasscode['MODIFIED'])
        self.LASTCHECKED = float(currentpasscode['LASTCHECKED'])

    def create(self):
        """
        Create live one-time passcode and save to passcode store
        """

        self.refreshfromstore()
        self.CURRENTPASSCODE = secrets.token_urlsafe(32)
        self.MODIFIED = time.time()
        self.LASTCHECKED = time.time()
        self.update()        

        return self.CURRENTPASSCODE

    def getresetlink(self, baseurl):
        """
        Creates reset link using supplied baseurl
        """

        return baseurl + '/' + self.create()

    def isexpired(self):
        """
        Checks whether passcode has expired using PASSCODEEXPIRYTIME
        """

        self.refreshfromstore()
        if (time.time() >= (self.MODIFIED + (60 * PASSCODEEXPIRYTIME))): 
            return True
        return False
    
    def isvalid(self, testpasscode):
        """
        Test for valid passcode against stored passcode ignoring expiry
        """

        self.refreshfromstore()

        # First wait requisite time period based on LASTCHECKED
        if (int(self.LASTCHECKED) + PASSCODETIMEDELAYS) > time.time():
            sleeptime = (int(self.LASTCHECKED) + PASSCODETIMEDELAYS) - time.time()
            time.sleep(sleeptime)

        # Update LASTCHECKED
        self.LASTCHECKED = time.time()
        self.update()

        # Carry out checking of testpasscode
        if testpasscode == PASSCODERESET: return False
        if self.CURRENTPASSCODE == testpasscode: return True
        return False
        
    def reset(self):
        """
        Reset one-time passcode
        
        Resetting one-time passcode equates to access being denied
        """

        self.CURRENTPASSCODE = PASSCODERESET
        self.MODIFIED = self.LASTCHECKED = time.time()
        self.update()

    def update(self):
        """
        Write one-time passcode to passcode store
        """

        with open(PASSCODEFILE, 'w') as f:
            json.dump({'CURRENTPASSCODE': self.CURRENTPASSCODE, 'MODIFIED': self.MODIFIED, 'LASTCHECKED': self.LASTCHECKED}, f, indent=4)
