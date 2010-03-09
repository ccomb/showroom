#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT
if [ $# -ne 2 ]
then
    echo "not enough parameters" $# $@
    exit
fi

# get params
name=$1

# load vars and fonctions
. scripts/config.sh

port=$(get_free_port)

# set virtualenv (just in case)
virtualenv virtualenv_$name
. virtualenv_$name/bin/activate

# create and goto app dir
mkdir -p demos/$name
cd demos/$name

# create buildout conf, bootstrap and launch buildout
cat > buildout.cfg <<EOF
[buildout]
parts=$name

[$name]
recipe = zc.recipe.egg
eggs =  repoze.bfg
        pastescript
        pastedeploy
        paste

EOF

wget http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py
python bootstrap.py

bin/buildout

# create app conf

cat > $name.cfg << EOF
[DEFAULT]
debug = true

[app:main]
use = egg:aws.demos#app
reload_templates = true
debug_authorization = false
debug_notfound = false

[server:main]
use = egg:Paste#http
host = $BASE_URL
port = $port

EOF

#return to the supervisor directory
cd -

# add app conf to supervisor conf
cat >> supervisor.conf << EOF
[program:$name]
command = paster serve $name.ini
process_name = $name
directory = demos/$name/
priority = 10
redirect_stderr = false

EOF

echo $BASE_URL:$port/

