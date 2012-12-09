#!/usr/bin/env bash
# PARAMS:name

function first_install {
# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install -i http://dist.repoze.org/bfg/current/simple --download-cache=$HOME/eggs repoze.bfg==1.3

# create a bfg project
sandbox/bin/paster create -t bfg_starter bfg
cd bfg

# install our new application in the virtualenv
../sandbox/bin/python setup.py develop

cd ..
# relocate the virtualenv
virtualenv --no-site-packages --distribute sandbox --relocatable

cat > start.sh << EOF
exec sandbox/bin/paster serve bfg/bfg.ini
EOF

}

function reconfigure_clone {
echo
}
