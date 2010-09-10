#!/usr/bin/env bash
# PARAMS:name,comment

# create a file
mkdir htdocs

# create the Apache config
cat > apache2.conf << EOF
# good apache directive
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
# script which doesn't start
sleep 0.1
EOF
