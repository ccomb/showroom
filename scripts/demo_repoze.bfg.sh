#!/usr/bin/env sh
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT,TEST

# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install -i http://dist.repoze.org/bfg/current/simple --download-cache=$HOME/eggs repoze.bfg==1.2.1

# create a bfg project
sandbox/bin/paster create -t bfg_starter $NAME
cd $NAME

# change the port used by default
sed -i "s/port = 6543/port = $PORT/" $NAME.ini

# install our new application
../sandbox/bin/python setup.py develop

cd ..

# write a file with required information
cat > democonfig.ini <<EOF
[democonfig]
start= sandbox/bin/paster serve $NAME/$NAME.ini
stop=
status=
comments = $COMMENT
EOF

