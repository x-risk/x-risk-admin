########################################
# Add secret key to Flask WSGI file
# https://gist.github.com/ndarville/3452907
########################################

import os

SYSADMIN_WSGI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sysadmin.wsgi')

try:
    import random
    SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(70)])
    secret = open(SYSADMIN_WSGI, 'a')
    secret.write("application.secret_key = '" + SECRET_KEY + "'\n")
    secret.close()
except IOError:
    Exception( "Please add the line 'application.secret_key = 'YOUR_SECRET_KEY' to sysadmin.wsgi \
              replacing YOUR_SECRET_KEY with random characters" )
