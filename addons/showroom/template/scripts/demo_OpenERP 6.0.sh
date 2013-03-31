#!/usr/bin/env bash
# PARAMS:name, version=6.0.4

function first_install {
# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
# egenix distribution setup is just a pain
sandbox/bin/easy_install http://downloads.egenix.com/python/egenix-mx-base-3.1.2.tar.gz
sandbox/bin/pip install http://download.gna.org/pychart/PyChart-1.39.tar.gz
sandbox/bin/pip install psycopg2==2.2.2 reportlab==2.4 pydot==1.0.2 lxml==2.2.8 pytz==2010k PIL==1.1.7 PyYAML==3.09 cherrypy==3.1.2 python-dateutil==1.5

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
virtualenv --no-site-packages --distribute sandbox

# copy and change the default config
NETRPC=$(($PORT+1000))
cp ./sandbox/lib/python2.*/site-packages/openerp_web-*.egg/doc/openerp-web.cfg .
sed -i "s/^server.socket_port =.*/server.socket_port = $PORT/" openerp-web.cfg
sed -i "s/^openerp.server.port = '8070'/openerp.server.port = '$NETRPC'/" openerp-web.cfg

# initialise and create the database
/usr/lib/postgresql/9.1/bin/initdb postgresql
echo "data_directory = './postgresql'" >> postgresql/postgresql.conf
echo "hba_file = './postgresql/pg_hba.conf'" >> postgresql/postgresql.conf
echo "ident_file = './postgresql/pg_ident.conf'" >> postgresql/postgresql.conf
echo "unix_socket_directory='.'" >> postgresql/postgresql.conf
echo "port = $((PORT+2000))" >> postgresql/postgresql.conf

# prepare the server config file
cat > ./openerp-server.conf << EOF
[options]
netrpc = True
netrpc_interface = localhost
netrpc_port = $NETRPC
xmlrpcs = False
xmlrpc = False
db_host = localhost
db_port = $((PORT+2000))
EOF

# create the startup script
cat > start.sh << EOF
#!/bin/bash
trap "pkill -1 -P \$\$" EXIT
/usr/lib/postgresql/9.1/bin/postgres -D ./postgresql &
postgres_pid=\$!
./sandbox/bin/openerp-server -c $PWD/openerp-server.conf &
openerp_pid=\$!
./sandbox/bin/openerp-web -c openerp-web.cfg &
web_pid=\$!
trap "kill \$web_pid; kill \$openerp_pid; kill \$postgres_pid" EXIT
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
cd openerp-server-$version
../sandbox/bin/python setup.py install
cd ../openerp-web-$version
../sandbox/bin/python setup.py install
cd ..
NETRPC=$(($PORT+1000))
sed -i "s/^port.*/port = $((PORT+2000))/" postgresql/postgresql.conf
sed -i "s/^netrpc_port.*/netrpc_port = $NETRPC/" openerp-server.conf
sed -i "s/^db_port.*/db_port = $((PORT+2000))/" openerp-server.conf
sed -i "s/^server.socket_port =.*/server.socket_port = $PORT/" openerp-web.cfg
sed -i "s/^openerp.server.port = .*/openerp.server.port = '$NETRPC'/" openerp-web.cfg
sed -i "s%.*openerp-server.conf.*%./sandbox/bin/openerp-server -c \"$PWD/openerp-server.conf\" \&%" start.sh
}
