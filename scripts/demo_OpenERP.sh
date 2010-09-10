#!/usr/bin/env sh
# PARAMS:name,comment,test


# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
# egenix distribution setup is just a pain
sandbox/bin/easy_install http://downloads.egenix.com/python/egenix-mx-base-3.1.2.tar.gz
sandbox/bin/pip install http://download.gna.org/pychart/PyChart-1.39.tar.gz
sandbox/bin/pip install --download-cache=$HOME/eggs psycopg2==2.2.2 reportlab==2.4 pydot==1.0.2 lxml==2.2.7 pytz==2010k

version=5.0.12

# download and install the server
wget http://openerp.com/download/stable/source/openerp-server-$version.tar.gz
tar xzf openerp-server-$version.tar.gz
cd openerp-server-$version
../sandbox/bin/python setup.py install
cd ..

# download and install the web interface
wget http://openerp.com/download/stable/source/openerp-web-$version.tar.gz
tar xzf openerp-web-$version.tar.gz
cd openerp-web-$version
../sandbox/bin/python setup.py install
cd ..

# copy and change the default config
XMLRPC=$(($PORT+1000))
#NETRPC=$(($PORT+2000))
cp ./sandbox/lib/python2.6/site-packages/openerp_web-$version-py2.6.egg/config/openerp-web.cfg .
sed -i "s/^server.socket_port =.*/server.socket_port = $PORT/" openerp-web.cfg
sed -i "s/^port = '8070'/port = '$XMLRPC'/" openerp-web.cfg


cat > start.sh << EOF
#!/bin/bash
trap "pkill -9 -P \$\$" EXIT
#./sandbox/bin/openerp-server --port=$XMLRPC --net_port=$NETRPC &
./sandbox/bin/openerp-server --port=$XMLRPC --no-netrpc &
./sandbox/bin/openerp-web -c openerp-web.cfg
EOF

