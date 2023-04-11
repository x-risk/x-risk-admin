"""
Utility script that uses latest Elsevier API credentials in live x-risk folder 
to check they're able to download Scopus data correctly 
If there's a problem, email the CSER admin person

haselwimmer@gmail.com 17/01/2023
"""

import sys
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from scopusauthtokens.passcode import passcode
from scopusauthtokens.tokenchecker import tokenchecker, EXPIRYREMINDERWINDOW

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))
xrisk_dir = os.path.abspath(os.path.join(parent_dir, 'x-risk'))
sys.path.append(parent_dir)
sys.path.append(xrisk_dir)

import adminconfig
import config

# Location of lock file created if tokens aren't working
TOKENFAILURELOCKFILE = 'TOKENSFAILED'
TOKENFAILURELOCKFILE = os.path.join(xrisk_dir, TOKENFAILURELOCKFILE)

# Location of instructions PDF file
INSTRUCTIONS_FILE = "Instructions.pdf"  
INSTRUCTIONS = os.path.join(os.path.dirname(__file__), INSTRUCTIONS_FILE)

def send_scopus_reminder_message_to_admin(expirydate):
    """
    Send reminder email to admin to obtain new authentication tokens
    Email includes link for resetting tokens within system
    """
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "URGENT: Elsevier Scopus authentication tokens for X-Risk/TERRA due to expire soon"
    msg['From'] = config.EMAIL_HOST_USER
    msg['To'] = adminconfig.ADMINCONTACTEMAIL

    # Create new passcode with expiry to easily allow admin user to change tokens
    latestpasscode = passcode()
    entertokensurl = latestpasscode.getresetlink(adminconfig.ADMINURL)

    # Create the body of the message (a plain-text and an HTML version).
    text = """Dear CSER Admin,

The Elsevier API authentication tokens for the X-Risk/TERRA system are due to expire on """ + expirydate + """. 

Please follow the instructions in the attached "Instructions.pdf" file to obtain and implement new authentication tokens.

Once you have obtained valid authentication tokens from Elsevier, click the following link to enter them into the X-Risk/TERRA system:
""" + entertokensurl + """

Regards,

X-Risk/TERRA Sysadmin System

"""

    html = """
    <html>
    <head></head>
    <body>
        <p>Dear CSER Admin,<br><br>
        The Elsevier API authentication tokens for the X-Risk/TERRA system are due to expire on """ + expirydate + """. 
        <br><br>
        Please follow the instructions in the attached "Instructions.pdf" file to obtain and implement new authentication tokens.
        <br><br>
        Once you have obtained valid authentication tokens from Elsevier, click the following link to enter them into the X-Risk/TERRA system:<br>
        """ + entertokensurl + """
        <br><br>
        Regards,
        <br><br>
        X-Risk/TERRA Sysadmin System
        </p>  
    </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Add instructions attachment to email
    with open(INSTRUCTIONS, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {INSTRUCTIONS_FILE}",)
    msg.attach(part)

    with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
        server.ehlo()
        server.starttls()    
        server.login(config.EMAIL_HOST_USER, config.EMAIL_HOST_PASSWORD)
        server.sendmail(config.EMAIL_HOST_USER, adminconfig.ADMINCONTACTEMAIL, msg.as_string())

def send_error_message_to_admin(tokenchecker, errormessage):
    """
    Send error message to admin email that current authentication tokens are invalid
    """

    localtest = 'curl --header "Accept: application/json" --header "User-Agent: elsapy-v' + tokenchecker.elsversion + '" '
    localtest += '--header "X-ELS-APIKey: ' + tokenchecker.apikey + '" '
    if tokenchecker.insttoken: 
        localtest += '--header "X-ELS-Insttoken: ' + tokenchecker.insttoken + '" '
    localtest += '"' + tokenchecker.base_url + '?query=' + tokenchecker.testquery + '"'

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Problem downloading Elsevier Scopus"
    msg['From'] = config.EMAIL_HOST_USER
    msg['To'] = adminconfig.ADMINCONTACTEMAIL

    # Create new passcode with expiry to easily allow admin user to change tokens
    latestpasscode = passcode()
    entertokensurl = latestpasscode.getresetlink(adminconfig.ADMINURL)

    # Create the body of the message (a plain-text and an HTML version).
    text = """Dear CSER Admin,

There was a problem downloading the Elsevier Scopus data file for XRisk.

The exact error is:

""" + errormessage + """

You will need to:
(i) Contact Elsevier to obtain correct apikey and insttoken authentication token(s)
(ii) Click following link to enter new apikey and insttoken authentication tokens into X-Risk/TERRA system:
""" + entertokensurl + """

For further details about how to obtain correct authentication tokens from Elsevier, see the attached "Instructions.pdf" file.

To reproduce this error on a local computer, open command prompt and enter:

""" + localtest + """

If the above curl request is operating correctly, you should see lots of data including the 'dc:description' field. If 'dc:description' field is missing, that will create problems for xrisk.

Regards,

X-Risk/TERRA Sysadmin System

"""

    html = """\
    <html>
    <head></head>
    <body>
        <p>Dear CSER Admin,<br><br>
        There was a problem downloading the Elsevier Scopus data file for XRisk.<br><br>
        The exact error is:<br><br>
            <code>
    """ + errormessage + """
            </code>
        <br><br>
        You will need to:<br>
        (i) Contact Elsevier to obtain correct <code>apikey</code> and <code>insttoken</code> authentication token(s)<br>
        (ii) Click following link to enter new apikey and insttoken authentication tokens into X-Risk/TERRA system:<br>
    """ + entertokensurl + """<br> 
        <br>
        For further details about how to obtain and implement correct authentication tokens from Elsevier, see the attached "Instructions.pdf" file.
        <br><br>
        To reproduce this error on a local computer, open command prompt and enter:<br><br>
            <code>
    """ + localtest  + """
            </code><br><br>
        If the above curl request is operating correctly, you should see lots of data including the 'dc:description' field. If 'dc:description' field is missing, that will create problems for xrisk.<br><br>
        Regards,<br><br>
        X-Risk/TERRA Sysadmin System<br>
        </p>  
    </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Add instructions attachment to email
    with open(INSTRUCTIONS, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {INSTRUCTIONS_FILE}",)
    msg.attach(part)

    with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
        server.ehlo()
        server.starttls()    
        # server.set_debuglevel(1)    
        server.login(config.EMAIL_HOST_USER, config.EMAIL_HOST_PASSWORD)
        server.sendmail(config.EMAIL_HOST_USER, adminconfig.ADMINCONTACTEMAIL, msg.as_string())


# ***************************************************
# ***************** MAIN SCRIPT *********************
# ***************************************************
# *** Checks whether current authentication tokens **
# **** are valid and also whether they're due to ****
# ******** expire within EXPIRYREMINDERWINDOW *******
# ***************************************************

tokenchecker = tokenchecker()
tokencheckerresults = tokenchecker.run()

if tokencheckerresults['SUCCESS']:
    # If TOKENFAILURELOCKFILE exists remove it
    if os.path.isfile(TOKENFAILURELOCKFILE) is True: os.remove(TOKENFAILURELOCKFILE)
    print("SUCCESS: Valid authentication tokens downloaded test abstract: " + tokencheckerresults['DATA'])

    if (tokenchecker.expiressoon()):
        print("WARNING: Sending notification as tokens due to expire on " + tokenchecker.expirydate + " - within " + str(EXPIRYREMINDERWINDOW) + " days of now")
        send_scopus_reminder_message_to_admin(tokenchecker.expirydate)

else:
    # Create TOKENFAILURELOCKFILE as flag to prevent normal crontab tasks from running
    f = open(TOKENFAILURELOCKFILE, 'w')
    f.close()

    print("FAILURE: Sending notification as token checker error: " + tokencheckerresults['DATA'])
    send_error_message_to_admin(tokencheckerresults['OBJ'], tokencheckerresults['DATA'])

