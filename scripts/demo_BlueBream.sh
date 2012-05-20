#!/usr/bin/env bash
# PARAMS:name

# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install distribute==0.6.24
sandbox/bin/pip install PasteDeploy==1.3.4 Paste==1.7.5.1 PasteScript==1.7.4.2
sandbox/bin/pip install bluebream==1.0


# create a bfg project
sandbox/bin/paster create --no-interactive -t bluebream bb
cd bb

# change the port used by default
sed -i "s/^port = .*/port = $PORT/" "deploy.ini"

# bootstrap and buildout
../sandbox/bin/python bootstrap.py --version 1.4.3
./bin/buildout

cat > ../start.sh << EOF
cd bb
exec bin/paster serve deploy.ini
EOF

