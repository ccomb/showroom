#!/usr/bin/env bash
# PARAMS:NAME,COMMENT

# create a file
touch foobar

cat > start.sh << EOF
#!/bin/sh
sleep 99999999
EOF
