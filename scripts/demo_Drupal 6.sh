#!/bin/bash
# PARAMS: name 
# sudo aptitude install php5-cli apache2
# sudo pear install Console_Table

# download drupal
drupal_version=6.19
db_name=drupal
db_user=drupal
db_pass=drupal
db_host=127.0.0.1
db_port=$((PORT+1000))

wget http://ftp.drupal.org/files/projects/drupal-$drupal_version.tar.gz
tar xzf drupal-$drupal_version.tar.gz
mv drupal-$drupal_version drupal6
cp drupal6/sites/default/default.settings.php drupal6/sites/default/settings.php
sed -i "s/^\$db_url.*/\$db_url='mysql:\/\/$db_user:$db_pass@$db_host:$db_port\/$db_name';/" drupal6/sites/default/settings.php

# download drush
#drush=drush-All-versions-3.0.tar.gz
#drush_version=drush-6.x-3.1.tar.gz
#wget http://ftp.drupal.org/files/projects/$drush_version
#tar xzf $drush_version

# create the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/drupal6
#ErrorLog var/error.log
</VirtualHost>
EOF

# initialize MySQL
mkdir mysql
mysql_install_db --no-defaults --datadir=$PWD/mysql/

# start mysql temporarily
mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000)) &

# wait for mysql to be started
echo "Waiting for mysql to start..."
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root status
while [ $? -ne 0 ]; do
    sleep 0.5; echo "Waiting for mysql to start..."
    mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root status
done

# create a database
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root create drupal

# create a user with all privileges on the database
echo "CREATE USER 'drupal'@'localhost' IDENTIFIED BY 'drupal';" > mysql.tmp
echo "GRANT ALL ON drupal.* TO 'drupal'@'localhost';" >> mysql.tmp
echo "FLUSH PRIVILEGES;" >> mysql.tmp
mysql --socket=$PWD/mysql/mysqld.sock --user=root mysql < mysql.tmp
rm mysql.tmp

# stop mysql
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root shutdown

# create a startup script
cat > start.sh << EOF
exec mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000))
EOF





