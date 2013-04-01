#!/usr/bin/env bash
# PARAMS:comment

# create a file
mkdir htdocs

cat > start.sh << EOF
#!/bin/sh
# script which doesn't start
sleep 0.1
EOF
