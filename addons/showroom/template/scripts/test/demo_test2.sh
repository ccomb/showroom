#!/usr/bin/env bash
# PARAMS:comment

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
# we forgot the exec, a trap should be added during deployment
sleep 99999999
EOF
