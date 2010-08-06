#!/usr/bin/env sh
# PARAMS:NAME,COMMENT

set -e # explicit fail on errors

virtualenv --no-site-packages --distribute sandbox
sandbox/bin/pip install --download-cache=$HOME/eggs django-reversion south django PIL

wget http://pypi.python.org/packages/source/d/django-cms/django-cms-2.1.0.beta3.tar.gz
tar xzf django-cms-2.1.0.beta3.tar.gz
cd django-cms-2.1.0.beta3


cd $DEMOS/$NAME
rm -Rf example
cp -R django-cms-2.0/example/ example

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

