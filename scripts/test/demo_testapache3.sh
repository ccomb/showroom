#!/usr/bin/env bash
# PARAMS:NAME,COMMENT

# create a file
mkdir htdocs

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

cat > start.sh << EOF
#!/bin/sh
sleep 99999999
EOF
