#!/bin/bash
# PARAMS: name, version=1.4.8.2, admin_path=admin123

prestashop_version=$version
db_name=prestashop
db_user=prestashop
db_pass=prestashop
db_host=127.0.0.1
db_port=$((PORT+1000))

# download prestashop
url_presta=http://www.prestashop.com/ajax/controller.php?method=download\&type=releases\&file=prestashop_$prestashop_version.zip\&language=en,fr
echo $url_presta
file_down=controller.php?method=download\&type=releases\&file=prestashop_$prestashop_version.zip\&language=en,fr
echo $file_down
wget $url_presta
mv $file_down prestashop_$prestashop_version.zip
unzip prestashop_$prestashop_version.zip
#change install form for have default config for db
sed -i "s/localhost/$db_host:$db_port/" prestashop/install/index.php
sed -i "s/root/prestashop/" prestashop/install/index.php
sed -i "s/type=\"password\" id=\"dbPassword\"\/>/type=\"password\" id=\"dbPassword\" value=\"prestashop\"\/>/" prestashop/install/index.php

# create the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/prestashop
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
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root create prestashop

# create a user with all privileges on the database
echo "CREATE USER 'prestashop'@'localhost' IDENTIFIED BY 'prestashop';" > mysql.tmp
echo "GRANT ALL ON prestashop.* TO 'prestashop'@'localhost';" >> mysql.tmp
echo "FLUSH PRIVILEGES;" >> mysql.tmp
mysql --socket=$PWD/mysql/mysqld.sock --user=root mysql < mysql.tmp
rm mysql.tmp


# stop mysql
mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root shutdown

# create a startup script
cat > start.sh << EOF
exec /usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$((PORT+1000))
EOF

# create a popup for installation instruction
cat > popup.html << EOF
<p>When you have finished the Prestashop installation wizard, do the following:</p>
<ol>
  <li>First <a href="/showroom_manage/postinstall?app=$name">click here</a>to delete the install folder and rename /admin to /$admin_path</li>
  <li>Then you can go to your Prestashop <a href="/$admin_path">Admin panel</a></li>
</ol>
EOF

# create a post install script
cat > post_install.sh << EOF
cd prestashop
rm -R install
mv admin $admin_path
EOF

