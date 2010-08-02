#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT,TEST

# load vars and fonctions
. $SCRIPTS/config.sh

# set virtualenv (just in case)
$BIN/virtualenv $DEMOS/$NAME --no-site-packages --distribute
. $DEMOS/$NAME/bin/activate

cd $DEMOS/$NAME

# create buildout conf, bootstrap and launch buildout
cat > buildout.cfg <<EOF
[buildout]
newest = false
parts=eggs

[eggs]
recipe = zc.recipe.egg
eggs =
    repoze.bfg
    pastescript
    pastedeploy
    paste

EOF

wget http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py
python bootstrap.py

bin/buildout

bin/paster create -t bfg_zodb $NAME

cat > buildout.cfg <<EOF
[buildout]
newest = false
parts=eggs supervisor
develop = $NAME

[eggs]
recipe = zc.recipe.egg
eggs = 
    repoze.bfg
    pastescript
    pastedeploy
    paste
    $NAME

[supervisor]
recipe=collective.recipe.supervisor
port=$SUPERVISOR_PORT
serverurl=http://localhost:$SUPERVISOR_PORT
programs=
    10 app \${buildout:directory}/bin/paster [serve deploy.ini] \${buildout:directory}/ true

EOF

bin/buildout

# create app conf

cat > deploy.ini << EOF
[DEFAULT]
debug = true

[app:main]
use = egg:Paste#urlmap
/$NAME = app

[app:app]
use = egg:$NAME#app
reload_templates = true
debug_authorization = false
debug_notfound = false
zodb_uri = file://%(here)s/Data.fs

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = $PORT

EOF

supervisor_daemon_sh

echo $COMMENT > about.txt
#return to the supervisor directory
cd -

