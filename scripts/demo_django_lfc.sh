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
extra-paths =
    \${django:extra-paths}
    \${buildout:directory}

[supervisor]
recipe=collective.recipe.supervisor
port=$SUPERVISOR_PORT
serverurl=http://localhost:$SUPERVISOR_PORT
programs=
    10 app \${buildout:directory}/bin/paster [serve deploy.ini] \${buildout:directory}/ true

EOF

bootstrap
bin/python bootstrap.py -d
bin/buildout -N -c demo.cfg buildout:eggs-directory=$HOME/eggs

cat > deploy.ini << EOF
[DEFAULT]
debug = true

[app:main]
use = egg:Paste#urlmap
/$NAME = app

[app:app]
use=egg:dj.paste
django_settings_module=lfc_project.settings

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = $PORT

EOF

cat >> lfc_project/settings.py << EOF

# demo
MEDIA_URL = '/$NAME/media/'
ADMIN_MEDIA_PREFIX = '/$NAME/media/admin/'

EOF

supervisor_daemon_sh

