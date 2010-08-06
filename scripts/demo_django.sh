#!/usr/bin/env sh
# PARAMS:NAME,COMMENT

set -e # explicit fail on errors

# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install --download-cache=$HOME/eggs django==1.2.1

# create a django project
sandbox/bin/django-admin.py startproject project
cd project

# create a django app
../sandbox/bin/django-admin.py startapp application

cat > ../start.sh << EOF
#!/bin/sh
sandbox/bin/python project/manage.py runserver $PORT
EOF
