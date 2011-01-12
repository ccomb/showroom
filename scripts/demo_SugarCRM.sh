#!/bin/bash
# PARAMS: name
# sudo aptitude install php5-cli apache2

# download sugar
version=6.1.1

#wget http://www.sugarforge.org/frs/download.php/7567/SugarCE-$version.zip
wget http://www.sugarforge.org/frs/download.php/7678/SugarCE-6.1.1.zip
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

# create a database
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root create sugar

# create a user with all privileges on the database
echo "CREATE USER 'sugar'@'localhost' IDENTIFIED BY 'sugar';" > mysql.tmp
echo "GRANT ALL ON sugar.* TO 'sugar'@'localhost';" >> mysql.tmp
echo "FLUSH PRIVILEGES;" >> mysql.tmp
mysql --socket=$PWD/mysql/mysqld.sock --user=root mysql < mysql.tmp
rm mysql.tmp

# stop mysql
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root shutdown

# add contrab rule
crontab -l >/tmp/crontab
echo "* * * * * cd $PWD/sugar; php -f cron.php >/dev/null 2>&1">>/tmp/crontab
crontab /tmp/crontab
rm /tmp/crontab

# create a startup script
cat > start.sh << EOF
exec /usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000))
EOF
