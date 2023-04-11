
# Script for setting up X-Risk Sysadmin application
# Code snippets taken from internet and credited where relevant
# 2030

# Workaround for problem with bash on OSX not supporting -i flag on read
# https://stackoverflow.com/questions/22634065/bash-read-command-does-not-accept-i-parameter-on-mac-any-alternatives

function readinput() {
  local CLEAN_ARGS=""
  default=''
  prompt=''
  while [[ $# -gt 0 ]]; do
    local i="$1"
    case "$i" in
      "-i")
		default="$2"
        shift
        shift
        ;;
      "-p")
		prompt="$2"
        shift
        shift
        ;;
      *)
        input=$1
        shift
        ;;
    esac
  done
  read -p "$prompt [$default]: " tempinput
  eval $input="${tempinput:-$default}" 
}


# ***************************** PRECHECKS **********************************
# Check for existence of ../x-risk/config.py
# If not found, report error as 'x-risk' folder needs to be at same level as 'x-risk-admin'

if ! [ -f ../x-risk/config.py ]; then
    echo "X-Risk config.py file cannot be found in ../x-risk/ folder. Is 'x-risk-admin' folder at same level as 'x-risk' folder?"
    exit
fi

if ! command -v jq &> /dev/null
then
    echo "jq command could not be found. Install from https://stedolan.github.io/jq/"
    exit
fi

cp ../x-risk/config.py config
source config


# ************************** SYSADMIN EMAIL *******************************

readinput -e -p "Admin email address - all notifications will be sent to this address" -i ${EMAIL_HOST_USER} adminemail


# *************************** SYSADMIN URL ********************************
# Generate default URL for sysadmin system using DOMAIN from ../x-risk/config.py

adminurl="${DOMAIN}/sysadmin"
rm config

readinput -e -p "Domain name to be used for sysadmin website - leave blank to autogenerate from X-Risk domain" -i ${adminurl} adminurl

# Remove trailing slash
adminurl=${adminurl%/}

# Autogenerate adminurl from config file
if [[ $adminurl == "" ]]; then
    adminurl="${DOMAIN}/sysadmin"
fi

# If local url, avoid https and remove path
if [[ $adminurl == 127.0.0.1:* ]]; then
    adminurl=${adminurl%/*}
    adminurl="http://${adminurl}"
fi

# Prepend 'https://' to domain name
if ! [[ $adminurl == http://* || $adminurl == https://* ]]; then
    adminurl="https://${adminurl}"
fi

echo "Sysadmin website will run from: ${adminurl}"


# *************************** APACHE USER ********************************
# Determine default Apache user by checking platform
# This is neeeded to chown ../x-risk/config.json so sysadmin application can make changes

wwwuser="www-data"
if [[ "$OSTYPE" == "darwin"* ]]; then
    wwwuser="_www"
fi

readinput -e -p "System user for Apache (typically 'www-data' on Linux, '_www' on OSX" -i ${wwwuser} wwwuser


# *************************** EXPIRY DATE ********************************
# Set default expiry date of Elsevier authentication tokens to 1 year from now
# Expiry date should however be set by user based on actual communication from Elsevier 
# to prevent tokens expiring without prior notifications being sent
#
# Cross-platform date calculation from:
# https://stackoverflow.com/questions/21958851/convert-unix-epoch-time-to-human-readable-date-on-mac-osx-bsd

expirydate=$(date +%Y-%m-%d)
nowseconds=$(date +%s)
yearseconds=$(expr 365 \* 24 \* 60 \* 60)
yearfromnowseconds=$(expr ${nowseconds} + ${yearseconds})
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    expirydate=$(date --date @${yearfromnowseconds} +"%Y-%m-%d")
elif [[ "$OSTYPE" == "darwin"* ]]; then
    expirydate=$(date -r ${yearfromnowseconds} +%Y-%m-%d)
fi

readinput -e -p "Expiry date of current Elsevier authentication tokens in form 'YYYY-MM-DD'" -i "${expirydate}" expirydate


# ************************** CREATE adminconfig.py ******************************

echo "
ADMINCONTACTEMAIL='${adminemail}'
ADMINURL='${adminurl}'
WWW_USER='${wwwuser}'
" > adminconfig.py


# *********************** MODIFY ../x-risk/config.json ***************************
# Load Elsevier authentication tokens from ../x-risk/config.json
# Uses jq library available from https://stedolan.github.io/jq/

apikey=$(jq .apikey ../x-risk/config.json)
insttoken=$(jq .insttoken ../x-risk/config.json)
echo "Calling sudo to update ../x-risk/config.json and change owner to allow access by Apache"
echo "
{
    \"apikey\": ${apikey},
    \"insttoken\": ${insttoken},
    \"expirydate\": \"${expirydate}\"
}
" | sudo tee ../x-risk/config.json >/dev/null
sudo chown ${wwwuser}:${wwwuser} ../x-risk/config.json
sudo chown ${wwwuser}:${wwwuser} scopusauthtokens/passcode/
sudo chown ${wwwuser}:${wwwuser} scopusauthtokens/tokenchecker/

# Create link to X-Risk's 'static' folder
ln -s ../x-risk/static static

# Outputting sysadmin.wsgi
echo "Creating sysadmin.wsgi"
echo "import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '$PWD')
from sysadmin import app as application" > sysadmin.wsgi

echo "Adding SECRET_KEY to sysadmin.wsgi"
python3 addsecretkey.py

# ********************************* COMPLETE **************************************

echo "SETUP COMPLETE!"

exit
