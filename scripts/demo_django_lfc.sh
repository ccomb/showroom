#!/usr/bin/env sh
# PARAMS:NAME,COMMENT
set -e # explicit fail on errors

# load vars and fonctions
. $SCRIPTS/config.sh

! [ -d $DEMOS/$NAME ] && hg clone https://gawel@bitbucket.org/diefenbach/lfc-buildout-development/ $DEMOS/$NAME

# set virtualenv (just in case)
$BIN/virtualenv $DEMOS/$NAME --no-site-packages --distribute
. $DEMOS/$NAME/bin/activate

cd $DEMOS/$NAME

bin/pip install PIL

cat > demo.cfg << EOF
[buildout]
extends = buildout.cfg
newest = false
parts += supervisor eggs

[eggs]
recipe = zc.recipe.egg
eggs =
    \${django:eggs}
    dj.paste
    repoze.bfg
    PasteScript
    lxml
    SaladeDeFruits
extra-paths =
    \${django:extra-paths}
    \${buildout:directory}

[supervisor]
recipe=collective.recipe.supervisor
port=$SUPERVISOR_PORT
serverurl=http://localhost:$SUPERVISOR_PORT
programs=
    10 app \${buildout:directory}/bin/paster [serve deploy.ini] \${buildout:directory}/ true
    20 proxy \${buildout:directory}/bin/paster [serve proxy.ini] \${buildout:directory}/ true

EOF

bootstrap
bin/python bootstrap.py -d
STATIC_DEPS=true bin/buildout -N -c demo.cfg buildout:eggs-directory=$HOME/eggs

cat > deploy.ini << EOF
[DEFAULT]
debug = true

[app:main]
use=egg:dj.paste
django_settings_module=lfc_project.settings

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = $PORT2

EOF

cat > proxy.ini << EOF
[DEFAULT]
debug = true

[app:main]
use = egg:Paste#urlmap
/$NAME = app

[app:app]
use=egg:SaladeDeFruits#rewrite
uri = http://127.0.0.1:$PORT2/

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = $PORT

EOF

supervisor_daemon_sh

