#!/usr/bin/env sh
source scripts/config.sh

if [ -d $DEMOS_BASE_DIR/$1 ]
then
    rm -r $DEMOS_BASE_DIR/$1
    echo "ok"
else
    echo "error, unknown application"
fi
