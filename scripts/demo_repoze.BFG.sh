#!/usr/bin/env sh
# PARAMS:name,comment,test


# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install -i http://dist.repoze.org/bfg/current/simple --download-cache=$HOME/eggs repoze.bfg==1.2.1

# create a bfg project
sandbox/bin/paster create -t bfg_starter bfg
cd bfg

# change the port used by default
sed -i "s/port = 6543/port = $PORT/" "bfg.ini"

# install our new application in the virtualenv
../sandbox/bin/python setup.py develop

cat > ../start.sh << EOF
exec sandbox/bin/paster serve bfg/bfg.ini
EOF

