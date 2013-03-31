#!/bin/bash
# PARAMS: name, version=1.4.8.2
set -x

export db_host=127.0.0.1
export db_port=$((PORT+1000))
export db_name=prestashop
export db_user=prestashop
export db_pass=prestashop

function first_install {
# download and extract prestashop
url=http://www.prestashop.com/ajax/controller.php?method=download\&type=releases\&file=prestashop_${version}.zip\&language=en,fr
wget $url -O  prestashop.zip
unzip prestashop.zip

if [ "$version" ">" "1.5.0.0" ]; then 
    sed -i "s/database_server = 'localhost'/database_server = '$db_host:$db_port'/" prestashop/install/controllers/http/database.php
    sed -i "s/database_login = 'root'/database_login = '$db_user'/" prestashop/install/controllers/http/database.php
    sed -i "s/database_password = ''/database_password = '$db_pass'/" prestashop/install/controllers/http/database.php
else
    # change install form to have default config for db
    sed -i "s/localhost/$db_host:$db_port/" prestashop/install/index.php
    sed -i "s/root/$db_user/" prestashop/install/index.php
    sed -i "s/type=\"password\" id=\"dbPassword\"\/>/type=\"password\" id=\"dbPassword\" value=\"$db_pass\"\/>/" prestashop/install/index.php
fi

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
exec /usr/sbin/mysqld --no-defaults --socket=./mysql/mysqld.sock --datadir=./mysql/ --log-error=./mysql/mysql-error.log --port=$db_port
EOF

# create a howto for installation instruction
cat > howto.html << EOF
<p>When you have finished the Prestashop installation wizard, do the following:</p>
<ol>
  <li>First <a href="/showroom_manage/postinstall?app=$name">click here</a> to delete the install folder and rename /admin to /myadmin</li>
  <li>Then you can go to your Prestashop <a href="/myadmin">Admin panel</a></li>
</ol>
EOF

# create a post install script
cat > post_install.sh << EOF
cd prestashop
rm -R install
mv admin myadmin
EOF
}


function reconfigure_clone {
# $1 is the old name, $2 is the old port
sed -i "s/app=$1/app=$name/" howto.html
sed -i "s/\/$1\//\/$name\//" apache2.conf
sed -i "s/$2/$PORT/" apache2.conf
if [ "$version" ">" "1.5.0.0" ]; then 
    sed -i "s/$(($2 + 1000))/$db_port/" prestashop/install/controllers/http/database.php
else
    sed -i "s/$(($2 + 1000))/$db_port/" prestashop/install/index.php
fi
sed -i "s/$(($2 + 1000))/$db_port/" start.sh
}

