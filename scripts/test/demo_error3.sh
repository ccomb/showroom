#!/usr/bin/env bash
# PARAMS:name,comment

# create a file
mkdir htdocs

# create the Apache config
cat > apache2.conf << EOF
Bad apache directive
EOF

cat > start.sh << EOF
#!/bin/sh
# good script
exec sleep 99999999
EOF
