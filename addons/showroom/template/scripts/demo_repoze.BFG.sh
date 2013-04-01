#!/usr/bin/env bash
# PARAMS: port=6543

function create_template {

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
sandbox/bin/paster serve --daemon bfg/bfg.ini
EOF

}

function reconfigure_demo {
echo Nothing to do
}
