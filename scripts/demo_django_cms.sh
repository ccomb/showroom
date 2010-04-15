#!/usr/bin/env sh
# PARAMS:NAME,COMMENT
set -e # explicit fail on errors

# load vars and fonctions
. $SCRIPTS/config.sh

# set virtualenv (just in case)
$BIN/virtualenv $DEMOS/$NAME --no-site-packages --distribute
. $DEMOS/$NAME/bin/activate

cd $DEMOS/$NAME

! [ -f bin/paster ] && bin/pip install django-reversion south django PIL


! [ -d django-cms-2.0 ] && git clone git://github.com/digi604/django-cms-2.0.git
cd django-cms-2.0 && python setup.py develop

cd $DEMOS/$NAME
rm -Rf example
cp -R django-cms-2.0/example/ example

cat > buildout.cfg << EOF
[buildout]
newest = false
extensions = gp.vcsdevelop
vcs-extend-develop =
    git://github.com/digi604/django-cms-2.0.git#egg=django-cms
parts = eggs supervisor

[eggs]
recipe = zc.recipe.egg
eggs =
    repoze.bfg
    dj.paste
    PasteScript
    pysqlite
initialization =
    sys.path.append("\${buildout:directory}")
    sys.path.append("\${buildout:directory}/example")

[supervisor]
recipe=collective.recipe.supervisor
port=$SUPERVISOR_PORT
serverurl=http://localhost:$SUPERVISOR_PORT
programs=
    10 app \${buildout:directory}/bin/paster [serve deploy.ini] \${buildout:directory}/example true

EOF

bootstrap
bin/python bootstrap.py -d
bin/buildout -N buildout:eggs-directory=$HOME/eggs

cat > deploy.ini << EOF
[DEFAULT]
debug = true

[app:main]
use = egg:Paste#urlmap
/$NAME = app

[app:app]
use=egg:dj.paste
django_settings_module=example.settings

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = $PORT

EOF

cat > example/local_settings.py << EOF
# -*- coding: utf-8 -*-
import os

CMS_MEDIA_ROOT = "$DEMO/$NAME/django-cms-2.0/cms/media/cms/"

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'cms.db'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.i18n",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    "cms.context_processors.media",
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'cms.middleware.multilingual.MultilingualURLMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
)
EOF

cd example
python manage.py syncdb --noinput
python manage.py migrate
cd ..
cp example/cms.db cms.db

echo $COMMENT > about.txt

supervisor_daemon_sh

