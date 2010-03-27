#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT

# load vars and fonctions
. scripts/config.sh

# set virtualenv (just in case)
bin/virtualenv $DEMOS/$NAME --no-site-packages --distribute
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
parts=eggs
develop = $NAME

[eggs]
recipe = zc.recipe.egg
eggs =  
    repoze.bfg
    pastescript
    pastedeploy
    paste
    $NAME
EOF

bin/buildout

# create app conf

cat > deploy.cfg << EOF
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

cat > starter.sh << EOF
#!/usr/bin/env sh
cd $DEMOS/$NAME
bin/paster serve deploy.cfg

EOF

#return to the supervisor directory
cd -

