#!/bin/bash
# PARAMS: NAME 
# sudo aptitude install php5-cli apache2
# sudo pear install Console_Table

set -e # explicit shell errors

# download drupal
drupal_version=6.19
wget http://ftp.drupal.org/files/projects/drupal-$drupal_version.tar.gz
tar xzf drupal-$drupal_version.tar.gz
mv drupal-$drupal_version drupal6
cp drupal6/sites/default/default.settings.php drupal6/sites/default/settings.php

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

# create a startup script
cat > start.sh << EOF
exec mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000))
EOF





