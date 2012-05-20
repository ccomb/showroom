#!/bin/bash
# PARAMS: name, version=1.4.8.2, admin_path=admin123

db_host=127.0.0.1
db_port=$((PORT+1000))
db_name=prestashop
db_user=prestashop
db_pass=prestashop

# download prestashop
url_presta=http://www.prestashop.com/ajax/controller.php?method=download\&type=releases\&file=prestashop_$version.zip\&language=en,fr
wget $url_presta -O  prestashop_$version.zip
unzip prestashop_$version.zip

# change install form to have default config for db
sed -i "s/localhost/$db_host:$db_port/" prestashop/install/index.php
sed -i "s/root/$db_user/" prestashop/install/index.php
sed -i "s/type=\"password\" id=\"dbPassword\"\/>/type=\"password\" id=\"dbPassword\" value=\"$db_pass\"\/>/" prestashop/install/index.php

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

# init mysql db
mysql_create_and_stop $db_host $db_port $db_name $db_user $db_pass

# create a startup script
cat > start.sh << EOF
exec /usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$db_port
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

