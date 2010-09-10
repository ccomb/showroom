#!/usr/bin/env sh
# PARAMS:name,comment,test


# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install --download-cache=$HOME/eggs bluebream==1.0b2

# create a bfg project
sandbox/bin/paster create --no-interactive -t bluebream bb
cd bb

# change the port used by default
sed -i "s/^port = .*/port = $PORT/" "deploy.ini"

# bootstrap and buildout
../sandbox/bin/python bootstrap.py
./bin/buildout

cat > ../start.sh << EOF
cd bb
exec bin/paster serve deploy.ini
EOF

