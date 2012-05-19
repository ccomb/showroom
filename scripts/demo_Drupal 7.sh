#!/bin/bash
# PARAMS: name, version=7.14
# sudo aptitude install php5-cli apache2
# sudo pear install Console_Table

# download drupal
drupal_version=$version
drush_version=drush-6.x-3.3.tar.gz
db_name=drupal
db_user=drupal
db_pass=drupal
db_host=127.0.0.1
db_port=$((PORT+1000))
echo $db_port

wget http://ftp.drupal.org/files/projects/drupal-$drupal_version.tar.gz
tar xzf drupal-$drupal_version.tar.gz
mv drupal-$drupal_version drupal
cp drupal/sites/default/default.settings.php drupal/sites/default/settings.php
cat >> drupal/sites/default/settings.php << EOF
\$databases['default']['default'] = array(
  'driver' => 'mysql',
  'database' => '$db_name',
  'username' => '$db_user',
  'password' => '$db_pass',
  'host' => '$db_host',
  'port' => '$db_port',
  'prefix' => 'main_',
  'collation' => 'utf8_general_ci',
);
EOF

# create the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/drupal
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
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root create drupal

# create a user with all privileges on the database
echo "CREATE USER 'drupal'@'localhost' IDENTIFIED BY 'drupal';" > mysql.tmp
echo "GRANT ALL ON drupal.* TO 'drupal'@'localhost';" >> mysql.tmp
echo "FLUSH PRIVILEGES;" >> mysql.tmp
mysql --socket=$PWD/mysql/mysqld.sock --user=root mysql < mysql.tmp
rm mysql.tmp

# install drush and additional plugins
#if [ "$plugins" != "" ]; then
#    wget http://ftp.drupal.org/files/projects/$drush_version
#    tar xzf $drush_version
#
#    # install additional modules
#    cd drupal
#    ../drush/drush dl $plugins
#    cd ..
#fi

# stop mysql
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root shutdown

# create a startup script
cat > start.sh << EOF
exec /usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000))
EOF

# create a popup for installation instruction
cat > popup.html << EOF
<p>To finish the Drupal installation, do the following:</p>
<ol>
    <li>Visit the <a href="install.php">install.php</a> page.</li>
    <li>Finish the installation by filling in the forms</li>
    <li>Enjoy!</li>
</ol>
EOF

