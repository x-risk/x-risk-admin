"""
Flask application for performing sysadmin functions on X-Risk/TERRA

Currently manages resetting of Elsevier Scopus authentication tokens without 
need for username/password login by sending passcode with timeout to admin email 

haselwimmer@gmail.com 07/04/2023
"""

import sys, os
sys.path.insert(0, os.getcwd())

import smtplib
import time
import pwd
import grp
from flask import Flask, render_template, request, redirect
from markupsafe import Markup
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from scopusauthtokens.passcode import passcode, PASSCODEEXPIRYTIME, PASSCODETIMEDELAYS
from scopusauthtokens.tokenchecker import tokenchecker, EXPIRYREMINDERWINDOW

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))
xrisk_dir = os.path.abspath(os.path.join(parent_dir, 'x-risk'))
sys.path.append(parent_dir)
sys.path.append(xrisk_dir)

import adminconfig
import config

app = Flask(__name__)
application = app # For beanstalk

@app.route('/')
def home():
    """
    Default page showing current status of authentication tokens
    """

    newtokenchecker = tokenchecker()
    tokencheckerresults = newtokenchecker.cachedstatus()
    expirydate = datetime.strptime(newtokenchecker.expirydate, '%Y-%m-%d').strftime("%d/%m/%Y")

    showemailform = False
    icon = '<i class="material-icons text-success mdi-48px" style="padding-bottom:5px;">check_circle</i>'
    errormessage = "<span class=\"text-success\"><b>Authentication tokens working correctly</b></span>"
    status = "<p>They are due to expire on <b>" + expirydate + "</b>.</p>"
    
    if tokencheckerresults['SUCCESS'] is False:
        showemailform = True
        icon = '<i class="material-icons text-danger mdi-48px" style="padding-bottom:5px;">cancel</i>'
        errormessage = "<span class=\"text-danger\"><b>Authentication tokens not working</b></span>"
        status = """
        <p> 
        This will cause problems with the running of the X-Risk/TERRA website and 
        new authentication tokens need to be obtained <b>urgently</b>.
        </p>
        <p>
        To receive an email providing instructions on how to obtain new authentication tokens from Elsevier, 
        enter the registered admin email address for X-Risk/TERRA below. 
        </p>
        """
    else:
        if newtokenchecker.expiressoon():
            showemailform = True
            icon = '<i class="material-icons mdi-48px" style="padding-bottom:5px;color:#fb8c00">warning</i>'
            errormessage = "<span style='color:#fb8c00'><b>Authentication tokens due to expire on " + expirydate + "</b></span>"
            status = """
            <p>New authentication tokens need to be obtained as soon as possible from Elsevier 
            to prevent loss of service to X-Risk/TERRA. If you've received an email notifying you that 
            authentication tokens are due to expiry soon, please follow the instructions in the email.
            </p>
            <p>
            To receive an email providing instructions on how to obtain new authentication tokens 
            from Elsevier, enter the registered admin email address for X-Risk/TERRA below. 
            </p>
            """

    status += "<p><i>Last updated: " + tokencheckerresults['LASTSAVED'][:16] + "</i></b>"

    return render_template("index.html", \
        showemailform=showemailform, \
        baseurl=adminconfig.ADMINURL, \
        title="X-Risk Status", \
        errormessage=Markup(errormessage), \
        icon=Markup(icon), \
        status=Markup(status) )

@app.route('/resendpasscode', methods=["GET", "POST"])
def resendpasscode():
    """
    If supplied admin email matches stored admin email, send token resetting link
    """

    adminemail = request.form["adminemail"].strip()
    if adminemail.lower() == adminconfig.ADMINCONTACTEMAIL.lower():

    # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Reset Elsevier Scopus authentication tokens"
        msg['From'] = config.EMAIL_HOST_USER
        msg['To'] = adminconfig.ADMINCONTACTEMAIL

        # Create new passcode with expiry to easily allow admin user to change tokens
        latestpasscode = passcode()
        newpasscode = latestpasscode.create()
        entertokensurl = adminconfig.ADMINURL + '/' + newpasscode

        # Create the body of the message (a plain-text and an HTML version).
        text = """Dear CSER Admin,

To reset Elsevier Scopus authentication tokens, click this link:    
""" + entertokensurl + """

For information about obtaining new authentication tokens from Elsevier Scopus, 
open the attached "Instructions" document.

Regards,

X-Risk/TERRA Sysadmin System
"""

        html = """\
        <html>
        <head></head>
        <body>
            <p>Dear CSER Admin,<br><br>
            To reset Elsevier Scopus authentication tokens, click this link:<br> 
            """ + entertokensurl + """<br>
            <br>
            For information about obtaining new authentication tokens from Elsevier Scopus, 
            open the attached "Instructions" document.<br>
            <br>
            Regards,<br><br>
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

        # Add 'Instructions.pdf' attachment to email
        filename = "Instructions.pdf"  

        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )

        msg.attach(part)

        with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()    
            server.login(config.EMAIL_HOST_USER, config.EMAIL_HOST_PASSWORD)
            server.sendmail(config.EMAIL_HOST_USER, adminconfig.ADMINCONTACTEMAIL, msg.as_string())

    return render_template("passcodesent.html", baseurl=adminconfig.ADMINURL, title="Link sent")

@app.route('/<userpasscode>')
def inittokenupdate(userpasscode):
    """
    Initialize token update procedure using user-supplied passcode 
    User-supplied passcode will have been sent via email on token failure / annual schedule   
    """

    latestpasscode = passcode()   
    if latestpasscode.isvalid(userpasscode):
        if latestpasscode.isexpired():
            return passcodeexpired()
        else:
            return passcodevalid(userpasscode)
    else:
        return passcodeincorrect()

def passcodeexpired():
    """
    Inform user that link has expired and give them option to be sent another link
    """

    status = """
    Reset authentication tokens link must be used within """ + str(PASSCODEEXPIRYTIME) + """ 
    minutes of being sent. To be sent another link, enter the registered admin email address 
    for X-Risk/TERRA below:
    """
    return render_template("index.html", \
        showemailform=True, \
        baseurl=adminconfig.ADMINURL, \
        title="Link expired", 
        status=status )
  
def passcodevalid(userpasscode):
    """
    If passcode valid, present form for entering new authentication tokens 
    """    
    return render_template("entertokens.html", \
        baseurl=adminconfig.ADMINURL, \
        title="Enter authentication tokens", 
        userpasscode=userpasscode )

def passcodeincorrect():
    """
    If passcode incorrect, give user option to be sent another link  
    but include delay to prevent brute force attack

    A passcode=incorrect may be due to passcode being deleted after successfully updating tokens
    """

    time.sleep(PASSCODETIMEDELAYS)
    status = """
    Your tokens reset link does not appear to be valid. 
    It may have been reset following a successful attempt to update the tokens. 
    To be sent another link, enter the registered admin email address for X-Risk/TERRA below:
    """
    return render_template("index.html", \
        showemailform=True, \
        baseurl=adminconfig.ADMINURL, \
        title="Invalid link", \
        status=status )
    
@app.route('/updatetokens/<userpasscode>/', methods=["POST"])
def updatetokens(userpasscode):
    """
    Process supplied authentication tokens
    If valid tokens, update system with new tokens
    """

    latestpasscode = passcode()
    if latestpasscode.isvalid(userpasscode):

        # If passcode is valid, check supplied token values with Elsevier
        newtokenchecker = tokenchecker()
        apikey = request.form["apikey"].strip()
        insttoken = request.form["insttoken"].strip()
        newtokenchecker.settokens(apikey, insttoken)
        tokencheckerresults = newtokenchecker.run()

        if tokencheckerresults['SUCCESS']:
            # If supplied tokens are valid, save tokens and reset passcode as no longer required
            expirydate = request.form["expirydate"]
            newtokenchecker.savetokens(apikey, insttoken, expirydate)
            latestpasscode.reset()
            return redirect(adminconfig.ADMINURL)
        else:
            # If supplied tokens invalid, allow user to enter different authentication tokens
            return render_template("entertokens.html", \
                baseurl=adminconfig.ADMINURL, \
                title="Tokens error", \
                preciseerror=Markup("<p>Precise error: <code>" + tokencheckerresults['DATA'] + "</code></p>"), \
                errormessage="Authentication tokens not valid", \
                userpasscode=userpasscode, \
                body="Please reenter different authentication tokens below:" )
    else:
        return passcodeincorrect()
