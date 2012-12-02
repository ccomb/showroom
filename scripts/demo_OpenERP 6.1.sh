#!/usr/bin/env bash
# PARAMS:name, version=20121025-233243, admin_password=admin

function first_install {
# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# create a buildout
cat >> buildout.cfg << EOF
[buildout]
parts = openerp
versions = versions
find-links = http://download.gna.org/pychart/

[openerp]
recipe = anybox.recipe.openerp:server
version = nightly 6.1 $version
options.db_host = localhost
options.db_port = $((PORT+1000))
options.admin_passwd = $admin_password
options.xmlrpc_port = $PORT
options.netrpc = False

[versions]
MarkupSafe = 0.15
Pillow = 1.7.7
PyXML = 0.8.4
babel = 0.9.6
feedparser = 5.1.1
gdata = 2.0.16
lxml = 2.3.3
mako = 0.6.2
psycopg2 = 2.4.4
pychart = 1.39
pydot = 1.0.28
pyparsing = 1.5.6
python-dateutil = 1.5
python-ldap = 2.4.9
python-openid = 2.2.5
pytz = 2012b
pywebdav = 0.9.4.1
pyyaml = 3.10
reportlab = 2.5
simplejson = 2.4.0
vatnumber = 1.0
vobject = 0.8.1c
werkzeug = 0.8.3
xlwt = 0.7.3
zc.buildout = 1.5.2
zc.recipe.egg = 1.3.2
zsi = 2.0-rc3
EOF

# get the boostrap script
wget https://raw.github.com/buildout/buildout/master/bootstrap/bootstrap.py

# bootstrap and buildout
./sandbox/bin/python bootstrap.py
./bin/buildout

# needed to be able to clone the virtualenv
virtualenv --no-site-packages --distribute sandbox

# initialise and create the database
/usr/lib/postgresql/9.1/bin/initdb postgresql
echo "data_directory = './postgresql'" >> postgresql/postgresql.conf
echo "hba_file = './postgresql/pg_hba.conf'" >> postgresql/postgresql.conf
echo "ident_file = './postgresql/pg_ident.conf'" >> postgresql/postgresql.conf
echo "unix_socket_directory='.'" >> postgresql/postgresql.conf
echo "port = $((PORT+1000))" >> postgresql/postgresql.conf

# create the startup script
cat > start.sh << EOF
#!/bin/bash
trap "pkill -1 -P \$\$" EXIT
/usr/lib/postgresql/9.1/bin/postgres -D ./postgresql &
postgres_pid=\$!
./bin/start_openerp &
openerp_pid=\$!
trap "kill \$openerp_pid; kill \$postgres_pid" EXIT
cat
EOF

# create a popup for installation instruction
#cat > popup.html << EOF
#<p>To start using OpenERP, you must create a database. Do the following:</p>
#<ol>
#    <li>Click on "Manage Databases"</li>
#    <li>Click on "Create"</li>
#    <li>Fill in the form:
#        <ul>
#            <li>Super admin password: <your admin password></li>
#            <li>New database name: <your_database_name></li>
#            <li>Load Demonstration data: check if you need demo data</li>
#            <li>Default Language: choose your language</li>
#            <li>Administrator password: <choose a password for the "admin" account></li>
#            <li>Confirm password: <repeat the same password></li>
#        </ul>
#    <li>Click on OK, and wait a few seconds</li>
#    <li>Start configuring your new database</li>
#</ol>
#EOF

}

function reconfigure_clone {
sed -i "s/^port.*/port = $((PORT+1000))/" postgresql/postgresql.conf
sed -i "s/^options.db_port.*/options.db_port = $((PORT+1000))/" buildout.cfg
sed -i "s/^options.admin_passwd.*/options.admin_passwd = $admin_password/" buildout.cfg
sed -i "s/^options.xmlrpc_port.*/options.xmlrpc_port = $PORT/" buildout.cfg
./sandbox/bin/python bootstrap.py
./bin/buildout -o
}
