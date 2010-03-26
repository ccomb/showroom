#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT

# load vars and fonctions
. scripts/config.sh

port=$(get_free_port)

# set virtualenv (just in case)
bin/virtualenv $DEMOS/$NAME --no-site-packages --distribute
. $DEMOS/$NAME/bin/activate

cd $DEMOS/$NAME

# create buildout conf, bootstrap and launch buildout
cat > buildout.cfg <<EOF
[buildout]
parts=$NAME

[$NAME]
recipe = zc.recipe.egg
eggs =  
    repoze.bfg
    pastescript
    pastedeploy
    paste
    aws.demos.$NAME

EOF

wget http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py
python bootstrap.py -d

bin/buildout

# create app conf

cat > deploy.cfg << EOF
[DEFAULT]
debug = true

[app:main]
use = egg:aws.demos.$NAME#app
reload_templates = true
debug_authorization = false
debug_notfound = false

[server:main]
use = egg:Paste#http
host = $BASE_URL
port = $port

EOF

cat > starter.sh << EOF
#!/usr/bin/env sh
cd $DEMOS/$NAME
bin/paster serve deploy.cfg

EOF

#return to the supervisor directory
cd -

echo $BASE_URL:$port/

