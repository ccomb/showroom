#!/usr/bin/env bash
# PARAMS:version=5.0.16

function first_install {
# create a virtualenv
virtualenv -p python2.6 --no-site-packages --distribute sandbox

# install the required packages
# egenix distribution setup is just a pain
sandbox/bin/easy_install http://downloads.egenix.com/python/egenix-mx-base-3.1.2.tar.gz
sandbox/bin/pip install http://download.gna.org/pychart/PyChart-1.39.tar.gz
sandbox/bin/pip install --download-cache=$HOME/eggs psycopg2==2.2.2 reportlab==2.4 pydot==1.0.2 lxml==2.2.8 pytz==2010k PIL==1.1.7 cherrypy==3.1.2

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

# needed to be able to clone the virtualenv
virtualenv -p python2.6 --no-site-packages --distribute sandbox --relocatable

# copy and change the default config
NETRPC=$(($PORT+1000))
cp ./sandbox/lib/python*/site-packages/openerp_web-$version-*.egg/config/openerp-web.cfg .
sed -i "s/^server.socket_port =.*/server.socket_port = $PORT/" openerp-web.cfg
sed -i "s/^port = '8070'/port = '$NETRPC'/" openerp-web.cfg

# initialise and create the database
/usr/lib/postgresql/9.1/bin/initdb postgresql
echo "data_directory = './postgresql'" >> postgresql/postgresql.conf
echo "hba_file = './postgresql/pg_hba.conf'" >> postgresql/postgresql.conf
echo "ident_file = './postgresql/pg_ident.conf'" >> postgresql/postgresql.conf
echo "unix_socket_directory='.'" >> postgresql/postgresql.conf
echo "port = $((PORT+2000))" >> postgresql/postgresql.conf

# create the startup script
cat > start.sh << EOF
#!/bin/bash
trap "pkill -1 -P \$\$" EXIT
/usr/lib/postgresql/9.1/bin/postgres -D ./postgresql &
postgres_pid=\$!
./sandbox/bin/openerp-server --no-xmlrpc --net_port=$NETRPC --db_host=localhost --db_port=$((PORT+2000)) &
openerp_pid=\$!
./sandbox/bin/openerp-web -c openerp-web.cfg &
web_pid=\$!
trap "kill \$web_pid; kill -1 \$openerp_pid; kill \$postgres_pid" EXIT
cat
EOF

# create a howto for installation instruction
cat > howto.html << EOF
<p>To start using OpenERP, you must create a database. Do the following:</p>
<ol>
    <li>Click on "Databases"</li>
    <li>Click on "Create"</li>
    <li>Fill in the form:
        <ul>
            <li>Super admin password: admin</li>
            <li>New database name: <your_database_name></li>
            <li>Load Demonstration data: check if you need demo data</li>
            <li>Default Language: choose your language</li>
            <li>Administrator password: <choose a password for the "admin" account></li>
            <li>Confirm password: <repeat the same password></li>
        </ul>
    <li>Click on OK, and wait a few seconds</li>
    <li>Start configuring your new database</li>
</ol>
EOF
}

function reconfigure_clone {
# $1 is the old name, $2 is the old port
cd openerp-server-$version
../sandbox/bin/python setup.py install
cd ../openerp-web-$version
../sandbox/bin/python setup.py install
cd ..
NETRPC=$(($PORT+1000))
sed -i "s/^server.socket_port =.*/server.socket_port = $PORT/" openerp-web.cfg
sed -i "s/^port = .*/port = '$NETRPC'/" openerp-web.cfg
sed -i "s/^port.*/port = $((PORT+2000))/" postgresql/postgresql.conf
sed -i "s/--net_port=.*/--net_port=$NETRPC --db_host=localhost --db_port=$((PORT+2000)) \&/" start.sh
}
