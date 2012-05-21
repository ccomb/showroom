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
echo
}

