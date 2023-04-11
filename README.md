# X-Risk Admin
The **X-Risk Admin** system provides an easy-to-use system for monitoring and updating the Elsevier authentication tokens used by the main **X-Risk** website. Elsevier authentication tokens come with an expiry date so it's important to regularly check that tokens are still valid. The system also send out early notifications if tokens are soon to expire so they can be renewed well before they become invalid.

## Elements of X-Risk Admin
The **X-Risk Admin** system consists of the following elements:

### Status monitoring
The status of the current Elsevier authentication tokens installed within **X-Risk** can be viewed by going to the **X-Risk Admin** homepage at:

```
https://yourdomain.com/sysadmin
```

- **Working tokens**: If tokens are working correctly and are not due to expire within the next 30 days, a green tick will be displayed with the text "Authentication tokens working correctly". The expiry date of the tokens will also be displayed on the webpage.

- **Expired tokens**: If tokens are due to expire within the next 30 days, an orange warning icon will be displayed with the text "Authentication tokens due to expire on [expiry date]". The webpage will also display an email field so the user can be sent instructions via email on how to obtain new tokens from Elsevier and enter these new tokens into the **X-Risk Admin** system. *NOTE: The email address entered **must** match the admin email address entered during setup.*

- **Invalid tokens**: If tokens are no longer working correctly, a red cross icon will be displayed with the text "Authentication tokens not working". The webpage will also display an email field so the user can be sent instructions via email on how to obtain new tokens from Elsevier and enter these new tokens into the **X-Risk Admin** system. *NOTE: The email address entered **must** match the admin email address entered during setup.*

The system also runs a daily 'cron' task to check the validity/expiry of authentication tokens. In the event authentication tokens are invalid or due to expire within 30 days, the system sends a notification email with instructions on how to apply for new tokens from Elsevier and enter these new tokens into the **X-Risk Admin** system. 

It is, however, hoped that users will only ever receive expiry notifications and never invalid token notifications. Repeated expiry notifications should ensure new authentication tokens are obtained from Elsevier and entered into the **X-Risk** system well before the existing authentication tokens become invalid.

### Reset links sent via email
When it is necessary for the user to modify the authentication tokens for **X-Risk** - because the current tokens are no longer valid or are due to expire imminently - the **X-Risk Admin** system generates a randomized 'passcode' weblink which is included in every notification email. The user clicks on this passcode weblink to enter new authentication tokens, avoiding the need for the user to remember specific usernames/passwords. After the **X-Risk Admin** system checks the new authentication tokens are valid, the **X-Risk** system is updated with the new tokens. 

**NOTE: It is impossible to modify X-Risk's authentication tokens through the X-Risk Admin system without entering valid authentication tokens.**

For security, all passcode weblinks expire after 24 hours. However if the user is unable to use a particular passcode weblink for whatever reason, they can be sent a new weblink (valid for 24 hours) by entering the admin email address into a webform on **X-Risk Admin**.

Once new (and valid) authentication tokens have been entered into the **X-Risk Admin** system, the passcode system is reset and all passcode weblinks are rendered invalid - preventing anyone from updating the authentication tokens until the next time tokens are invalid or due-to-expire. 

**NOTE: The X-Risk Admin system will only send token reset links to the admin email address provided during setup. It is therefore important this email account is managed securely.**

### Step-by-step instructions in all email notifications
Every notification email sent by the **X-Risk Admin** system includes an `Instructions.pdf` document attachment providing step-by-step instructions on what the user should do to obtain new authentication tokens from Elsevier and how they should then enter these new tokens into the **X-Risk Admin** system.

## Technical overview
The **X-Risk Admin** system uses Python's Flask framework to minimize library dependencies and is designed to run alongside **X-Risk**'s existing Python Django framework. As both **X-Risk Admin** and **X-Risk** applications use the same `mod-wsgi-py3` Apache module - which is Python3-minor-version specific - it is important **X-Risk Admin** uses the exact same 'minor' version of Python3 as **X-Risk**. 

NOTE: In latest tests, **X-Risk** does not appear to be compatible with Python == 3.10 due to problems with Django 1.11 in Python3.10. The version of Tensorflow required by **X-Risk** is Tensorflow 1 which is also not compatible with Python >= 3.8. The recommended version of Python3 for both **X-Risk** and **X-Risk Admin** is therefore 3.5 - 3.7

## Installing X-Risk Admin

### Folder location
The **X-Risk Admin** website must be set up on the same server as the main **X-Risk** website and should share the same parent folder as `x-risk`. So if `x-risk` is located at:

```
/home/projects/x-risk/
```

`x-risk-admin` must be located at:

```
/home/projects/x-risk-admin/
```

The actual domain name used for **X-Risk Admin** may however be different from the domain name of the main **X-Risk** website, eg. `sysadmin.yourdomain.com`. This documentation, however, assumes **X-Risk Admin** runs off the same domain name as **X-Risk** but with the dedicated path `/sysadmin`, eg. `https://xrisk.domain/sysadmin`

NOTE: In all references to `/path/to/x-risk/` and `/path/to/x-risk-admin/` below, you should replace these paths with the absolute path of your `x-risk` and `x-risk-admin` folders respectively, eg. `/home/projects/x-risk/` and `/home/projects/x-risk-admin/`. Both these folders should share the same parent directory, eg. `/home/projects/`

### SMTP account for sending notifications
The **X-Risk Admin** system uses the same SMTP settings as the main **X-Risk** system to send email notifications. As long as these settings are working correctly for **X-Risk**, they will work correctly for **X-Risk Admin**.

### Information required during setup
The following information will be required during setup and should be determined before running the setup process:

- *Admin email address*: The admin email address all notifications will be sent through to. This email address will receive authentication reset links so it is important the email account is secure and maintained by an individual with appropriate access to change **X-Risk**'s authentication tokens.

- *Domain name of sysadmin website*: The domain name with path, eg. `yourdomain.com/sysadmin` that will be used to access the **X-Risk Admin** system. If the admin system will use the same domain as the main **X-Risk** application, it is important the path does not conflict with **X-Risk**'s existing Django directories (therefore avoid `/cms` and `/admin`). By default the path will be set using the `DOMAIN` value from `../x-risk/config.py` and will be `https://DOMAIN/sysadmin`.

- *System user for Apache*: The Apache system user, typically `www-data` on Linux and `_www` on OSX. The setup script will change the owner of `../x-risk/config.json` to this value to ensure the **X-Risk Admin** system can make changes to this file - which contains the Elsevier authentication tokens. To find the `WEBSERVER-USER/GROUP` for Apache, type `sudo apachectl -S`.

- *Expiry date of current Elsevier authentication tokens*: This should be the expiry date (in the form `YYYY-MM-DD`) of the current Elsevier authentication tokens. It is important the expiry date is correct so the system can send advanced notifications to the *Admin email address* (see above) well before the current Elsevier authentication tokens are due to expire. The system is currently set up to send daily warning notifications 30 days before tokens are due to expire.

Collect all of this information above before starting the **X-Risk Admin** software installation process.

### Install system software
The bulk of the system software required for the **X-Risk Admin** system will have been set up during the creation of the main **X-Risk** website. Refer to https://github.com/x-risk/x-risk for more information on the **X-Risk** system software.

In addition to the **X-Risk** system software already installed, the command line tool `jq` should be installed using:
```
sudo apt-get install jq
```

### Install X-Risk Admin software
Navigate to the parent folder above **X-Risk**. If **X-Risk** is located at `/home/projects/x-risk/` for example, change to `/home/projects/` folder with:

```
cd /home/projects/
```

Download **X-Risk Admin** source code from:

```
git clone https://github.com/x-risk/x-risk-admin.git
```

Change directory to the `x-risk-admin` folder with:

```
cd x-risk-admin
```

Modify the `Instructions.odt` (OpenOffice) file, replacing all bracketed text in red with the appropriate text for your organisation. You will need to change `[YOUR ORGANISATION]`, `[YOUR ELSEVIER REFERENCE NUMBER]`, `[YOUR ELSEVIER INSTTOKEN]` and `[YOURDOMAIN.COM]` with equivalent values for your organisation/domain. Finally, save the modified file in PDF format as `Instructions.pdf` - this will be the attached file sent to the admin email address in notifications.

Create and enable virtual environment for Python3 using the same 'minor' version of Python3 as **X-Risk**, eg. Python3.7. To retrieve the 'minor' version number of Python3 that **X-Risk** uses, type:

```
source ../x-risk/venv/bin/activate
python3 --version
deactivate
```
The 'minor' version number will be the first number after "`Python 3.`", eg. `7` in "`Python 3.7.16`". Insert this `MINOR_VERSION_NUMBER` below:

```
which python3.[MINOR_VERSION_NUMBER]
virtualenv -p [insert_path_from_previous_prompt] venv
source venv/bin/activate
```


Install necessary Python libraries by typing:

```
pip install -r requirements.txt
```

Run `setup.sh` and enter the details gathered during the `Information required during setup` stage, above:

```
./setup.sh
```

The setup process will add an expiry date to `../x-risk/config.json` and output a configuration file `/path/to/x-risk-admin/adminconfig.py`. To modify configuration settings, edit `/path/to/x-risk-admin/adminconfig.py`.

Once the setup process finishes, you will need to switch to system user `su` if you want to test the application locally. This is because the Flask application must create files using Apache user privileges in order for Apache to write to the same files during live deployment. 

To switch to `su` and test the application locally, type:

```
sudo su
source venv/bin/activate
FLASK_APP=sysadmin.py flask run
```

Open a web browser and load the **X-Risk Admin** local application at:

```
http://127.0.0.1:5000
```

Remember to type `exit` to leave the system user `su` once local testing is complete.


## Deploying X-Risk Admin
Assuming **X-Risk Admin** will be running on the same domain as **X-Risk**, add the following section of Apache conf code to the start of your **X-Risk** Apache conf file for HTTP/Port 80 below `ServerAlias...`:

```
# Link subdomain 'sysadmin' to Flask sysadmin application
WSGIScriptAlias /sysadmin /path/to/x-risk-admin/sysadmin.py
WSGIDaemonProcess xrisk-admin user=www-data group=www-data threads=5 home=/path/to/x-risk-admin python-home=/path/to/x-risk-admin/venv

<directory /path/to/x-risk-admin/>
    WSGIProcessGroup xrisk-admin
    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptReloading On
    Require all granted
</directory>

```

The **X-Risk** HTTP/Port 80 conf file should then look like:

```
<VirtualHost *:80>

    ServerName www.yourdomain.com
    ServerAlias yourdomain.com

    # Link subdomain 'sysadmin' to Flask sysadmin application
    WSGIScriptAlias /sysadmin /path/to/x-risk-admin/sysadmin.py
    ...
```

Repeat with the **X-Risk** HTTPS/Port 443 conf file, inserting:

```
# Link subdomain 'sysadmin' to Flask sysadmin application
WSGIScriptAlias /sysadmin /path/to/x-risk-admin/sysadmin.py
WSGIDaemonProcess ssl-xrisk-admin user=www-data group=www-data threads=5 home=/path/to/x-risk-admin python-home=/path/to/x-risk-admin/venv

<directory /path/to/x-risk-admin/>
    WSGIProcessGroup ssl-xrisk-admin
    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptReloading On
    Require all granted
</directory>
```

The **X-Risk** HTTPS/Port 443 conf file should then look like:

```
<IfModule mod_ssl.c>
<VirtualHost *:443>

    ServerName www.yourdomain.com
    ServerAlias yourdomain.com

    # Link subdomain 'sysadmin' to Flask sysadmin application
    WSGIScriptAlias /sysadmin /path/to/x-risk-admin/sysadmin.py
    ...
```

Modifying both conf files in this way allows the **X-Risk Admin** Flask application to run alongside the **X-Risk** Django application. All requests with the initial path `http[s]://yourdomain.com/sysadmin` are routed to **X-Risk Admin** while other requests are routed to **X-Risk**.

Finally reload Apache to load the modified conf files:

```
sudo apachectl restart
```

## Adding token checker to cron job
The **X-Risk Admin** system needs to run a daily script (`scopuscheck.py`) to check if the Elsevier authentication tokens are invalid or are due to expire within 30 days. If tokens are invalid or due to expire, the script sends a notification email to the admin email contact contained in `adminconfig.py` (set during setup - see above).

To set up the `scopuscheck.py` script to run as a daily cron job, edit your list of cron jobs by typing `sudo crontab -e` and add the following line at the start of the file after initial comments but before other cron entries:

```
# Run x-risk-admin daily shell script which checks whether Elsevier credentials are correct
@daily /path/to/x-risk-admin/cron_daily.sh 2>&1 | /path/to/x-risk/timestamp.sh >> /path/to/x-risk/cron.log
```

By placing the **X-Risk Admin** cron job before **X-Risk** cron jobs, the **X-Risk Admin** system can determine if authentication tokens are invalid and, if necessary, block **X-Risk** from potentially using invalid tokens.

To ensure **X-Risk** is prevented from using invalid tokens, edit the **X-Risk** monthly cron shell script located at `/path/to/x-risk/cron_monthly.sh`. Add the following code immediately before the line `echo "Retrieving text data from Scopus text archive"`:

```
# **********************************************************
# ** Sysadmin: Check if failed authentication tokens  
# ** Sysadmin: LOCKFILE exists and exit if it does
# ** Sysadmin: as we don't want to process incomplete data
# **********************************************************
echo "Checking existence of failed authentication tokens lockfile"
if [ -f $SCRIPTPATH/TOKENSFAILED ]; then
    echo "Failed authentication tokens lockfile found - QUITTING"
    exit 0
else
    echo "No lockfile found, continuing..."
fi
```

Once the cron files have been updated as above and the **X-Risk Admin** website is running at `http[s]://yourdomain.com/sysadmin`, the **X-Risk Admin** system will be monitoring the validity/expiry of authentication tokens used by **X-Risk**. 

To check the current status of Elsevier authentication tokens with **X-Risk Admin**, go to:

```
http[s]://yourdomain.com/sysadmin
```

## Copyright

TERRA Application  
Copyright (c) 2018 Gorm Shackleford  
Released under MIT License

Material Kit Template  
Copyright (c) 2017 Creative Tim  
Released under MIT License  
https://www.creative-tim.com/product/material-kit

Bootstrap-Select  
Copyright (c) 2012-2018 SnapAppointments, LLC  
Released under MIT License  
https://developer.snapappointments.com/bootstrap-select/
