#!/bin/bash
# PARAMS: name
# sudo aptitude install php5-cli apache2 php5-imap php5-curl
export db_host=127.0.0.1
export db_port=$((PORT+1000))
export db_name=sugar
export db_user=sugar
export db_pass=sugar
export version=6.4.5
export url=$REQUEST_HOST

function first_install {
# download sugar
#wget http://www.sugarforge.org/frs/download.php/7567/SugarCE-$version.zip
#wget http://www.sugarforge.org/frs/download.php/7678/SugarCE-6.1.1.zip
wget http://dl.sugarforge.org/sugarcrm/2SugarCE6.4.0/SugarCE6.4.0/SugarCE-$version.zip
#cp ../SugarCE-$version.zip .
unzip SugarCE-$version.zip
mv SugarCE-Full-$version sugar

# create the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/sugar
#ErrorLog var/error.log
</VirtualHost>
EOF

# initialize MySQL
mysql_create_and_stop $db_host $db_port $db_name $db_user $db_pass

# hack into install script!
sed 3i\$_SESSION[\'setup_db_host_name\']=\'$db_host:$db_port\'\; -i sugar/install/dbConfig_a.php
sed 4i\$_SESSION[\'setup_db_database_name\']=\'$db_name\'\; -i sugar/install/dbConfig_a.php
sed 4i\$_SESSION[\'setup_db_admin_user_name\']=\'$db_user\'\; -i sugar/install/dbConfig_a.php
sed 5i\$_SESSION[\'setup_db_admin_password\']=\'$db_pass\'\; -i sugar/install/dbConfig_a.php


# add contrab rule
#crontab -l >/tmp/crontab
#echo "* * * * * cd $PWD/sugar; php -f cron.php >/dev/null 2>&1">>/tmp/crontab
#crontab /tmp/crontab
#rm /tmp/crontab

# create a startup script
cat > start.sh << EOF
DIR=`pwd`
exec /usr/sbin/mysqld --no-defaults --socket=$DIR/mysql/mysqld.sock --datadir=$DIR/mysql/ --log-error=$DIR/mysql/mysql-error.log --port=$db_port
EOF
}

function reconfigure_clone {
# create the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/sugar
#ErrorLog var/error.log
</VirtualHost>
EOF
# hack into install script!
sed 3i\$_SESSION[\'setup_db_host_name\']=\'$db_host:$db_port\'\; -i sugar/install/dbConfig_a.php
sed 4i\$_SESSION[\'setup_db_database_name\']=\'$db_name\'\; -i sugar/install/dbConfig_a.php
sed 4i\$_SESSION[\'setup_db_admin_user_name\']=\'$db_user\'\; -i sugar/install/dbConfig_a.php
sed 5i\$_SESSION[\'setup_db_admin_password\']=\'$db_pass\'\; -i sugar/install/dbConfig_a.php
}
