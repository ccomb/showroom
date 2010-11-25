#!/usr/bin/env bash
# PARAMS: name, login=admin, password, version=4.0.2, plugins
set -e

# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the project templates
sandbox/bin/pip install --download-cache=$HOME/eggs ZopeSkel==2.17 PIL==1.1.7

# create a project
sandbox/bin/paster create --no-interactive -t plone3_buildout plone4 plone_version=$version zope_user=$login zope_password=$password http_port=$PORT
cd plone4

# add plugins
for package in $plugins; do
    sed -i "1,30s/^eggs =/eggs =\n    $package/" buildout.cfg
done

# build the application
../sandbox/bin/python bootstrap.py -d -v 1.4.4
./bin/buildout

# create the startup script
cat > ../start.sh << EOF
#!/usr/bin/env sh
exec plone4/bin/instance console
EOF

