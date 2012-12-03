#!/bin/bash
# PARAMS: name, version=7.14
# sudo aptitude install php5-cli apache2
# sudo pear install Console_Table

# download drupal
export drupal_version=$version
export drush_version=drush-6.x-3.3.tar.gz
export db_name=drupal
export db_user=drupal
export db_pass=drupal
export db_host=127.0.0.1
export db_port=$((PORT+1000))

function first_install {
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
mysql_create_and_stop $db_host $db_port $db_name $db_user $db_pass

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

# create a startup script
cat > start.sh << EOF
exec /usr/sbin/mysqld --no-defaults --socket=./mysql/mysqld.sock --datadir=./mysql/ --log-error=./mysql/mysql-error.log --port=$((PORT+1000))
EOF

# create a howto for installation instruction
cat > howto.html << EOF
<p>To finish the Drupal installation, do the following:</p>
<ol>
    <li>Visit the <a href="install.php">install.php</a> page.</li>
    <li>Finish the installation by filling in the forms</li>
    <li>Enjoy!</li>
</ol>
EOF
}

function reconfigure_clone {
# $1 is the old name, $2 is the old port, $3 is the old user
sed -i "s/^\$db_url.*/\$db_url='mysql:\/\/$db_user:$db_pass@$db_host:$db_port\/$db_name';/" drupal/sites/default/settings.php
sed -i "s/$(($2 + 1000))/$db_port/" start.sh
sed -i "s/'port' => .*/'port' => '$db_port',/" drupal/sites/default/settings.php
# recreate the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/drupal
#ErrorLog var/error.log
</VirtualHost>
EOF

}
