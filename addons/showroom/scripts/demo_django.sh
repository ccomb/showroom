#!/usr/bin/env bash
# PARAMS:name

function first_install {
# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install Django==1.3.1

# create a django project
sandbox/bin/django-admin.py startproject project
cd project

# create a django app
../sandbox/bin/django-admin.py startapp application

# needed to be able to clone the virtualenv
virtualenv --no-site-packages --distribute sandbox --relocatable

cat > ../start.sh << EOF
#!/bin/sh
exec sandbox/bin/python project/manage.py runserver --noreload $PORT
EOF
}

function reconfigure_clone {
sed -i "s/$2/$PORT/" start.sh
}
