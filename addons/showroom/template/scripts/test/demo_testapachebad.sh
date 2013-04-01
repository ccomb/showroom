#!/usr/bin/env bash
# PARAMS:comment

# create a file
mkdir htdocs

# create the Apache config
cat > apache2.conf << EOF
Invalid Apache Directive
EOF
