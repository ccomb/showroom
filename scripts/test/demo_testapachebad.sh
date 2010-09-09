#!/usr/bin/env bash
# PARAMS:NAME,COMMENT

# create a file
mkdir htdocs

# create the Apache config
cat > apache2.conf << EOF
Invalid Apache Directive
EOF
