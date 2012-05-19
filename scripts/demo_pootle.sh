#!/usr/bin/env bash
# PARAMS:name version=2.1.6
set -e

# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the required packages
sandbox/bin/pip install Django==1.3.1
sandbox/bin/pip install http://freefr.dl.sourceforge.net/project/translate/Translate%20Toolkit/1.9.0/translate-toolkit-1.9.0.tar.bz2
sandbox/bin/pip install http://freefr.dl.sourceforge.net/project/translate/python-Levenshtein/0.10.1/python-Levenshtein-0.10.1.tar.bz2

wget http://freefr.dl.sourceforge.net/project/translate/Pootle/${version}/Pootle-${version}.tar.bz2
tar xjf Pootle-${version}.tar.bz2
cd Pootle-${version}

../sandbox/bin/python manage.py syncdb
../sandbox/bin/python manage.py initdb
../sandbox/bin/python manage.py refresh_stats
..//sandbox/bin/pip install lxml==2.3.3

cp localsettings.py ../sandbox/local/lib/*/site-packages/

cat > ../start.sh << EOF
#!/bin/sh
exec ./PootleServer --port=$PORT
EOF
