#!/bin/bash
# PARAMS: name

function first_install {
# create a PHP hello world
mkdir htdocs
cat > htdocs/index.php << EOF
<?php
    phpinfo();
?>
EOF

# create the Apache config
cat > apache2.conf << EOF
Listen $PORT
NameVirtualHost *:$PORT
<VirtualHost *:$PORT>
ServerName localhost
DocumentRoot $PWD/htdocs
#ErrorLog var/error.log
</VirtualHost>
EOF
}

function reconfigure_clone {
# $1 is the old name, $2 is the old port
sed -i "s/\/$1\//\/$name\//" apache2.conf
sed -i "s/$2/$PORT/" apache2.conf
}

