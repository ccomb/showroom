#!/usr/bin/env bash
# PARAMS:name,comment

# create a file
touch foobar

cat > start.sh << EOF
#!/bin/sh
exec sleep 99999999
EOF
