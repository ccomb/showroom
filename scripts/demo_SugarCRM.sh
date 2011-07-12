#!/bin/bash
# PARAMS: name, username, password, usermail
# sudo aptitude install php5-cli apache2 php5-imap php5-curl
db_name=sugar
db_password=sugar
db_host=127.0.0.1
db_port=$((PORT+1000))
# download sugar
version=6.1.6
url=$REQUEST_HOST

#wget http://www.sugarforge.org/frs/download.php/7567/SugarCE-$version.zip
#wget http://www.sugarforge.org/frs/download.php/7678/SugarCE-6.1.1.zip
wget http://www.sugarforge.org/frs/download.php/8081/SugarCE-6.1.6.zip
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
mkdir mysql
mysql_install_db --no-defaults --datadir=$PWD/mysql/

# start mysql temporarily
/usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000)) &

# wait for mysql to be started
echo "Waiting for mysql to start..."
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root status
while [ $? -ne 0 ]; do
    sleep 0.5; echo "Waiting for mysql to start..."
    mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root status
done

# create a user with all privileges on the database
echo "\
CREATE USER 'sugar'@'localhost' IDENTIFIED BY 'sugar';
GRANT ALL ON sugarcrm.* TO 'sugar'@'localhost';
FLUSH PRIVILEGES;
" | mysql --socket=$PWD/mysql/mysqld.sock --user=root mysql

# stop mysql
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root shutdown

# hack into install script!
sed 3i\$_SESSION[\'setup_db_host_name\']=\'$db_host:$db_port\'\; -i sugar/install/dbConfig_a.php
sed 4i\$_SESSION[\'setup_db_admin_user_name\']=\'sugar\'\; -i sugar/install/dbConfig_a.php
sed 5i\$_SESSION[\'setup_db_admin_password\']=\'sugar\'\; -i sugar/install/dbConfig_a.php


# add contrab rule
#crontab -l >/tmp/crontab
#echo "* * * * * cd $PWD/sugar; php -f cron.php >/dev/null 2>&1">>/tmp/crontab
#crontab /tmp/crontab
#rm /tmp/crontab

# create a startup script
cat > start.sh << EOF
exec /usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000))
EOF
