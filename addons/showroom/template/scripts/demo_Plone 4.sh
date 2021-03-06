#!/usr/bin/env bash
# PARAMS: login=admin, password, version=4.1.4, plugins

function first_install {
# create a virtualenv
virtualenv -p python2.7 --no-site-packages --distribute sandbox

# install the project templates
sandbox/bin/pip install ZopeSkel==2.17 PIL==1.1.7 PasteDeploy==1.3.4 Paste==1.6

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

cd ..
virtualenv -p python2.7 --no-site-packages --distribute sandbox --relocatable
}


function reconfigure_clone {
# $1 is the old name, $2 is the old port
cd plone4
sed -i "s/$2/$PORT/" buildout.cfg
sed -i "s/user = .*/user = $login:$password/" buildout.cfg
../sandbox/bin/python bootstrap.py -d -v 1.4.4
./bin/buildout -o
}
