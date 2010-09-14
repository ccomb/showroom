#!/bin/bash
# PARAMS: name 
set -e


# create a PHP hello world
mkdir htdocs
cat > htdocs/index.php << EOF
<?php
    echo 'hello world';
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

