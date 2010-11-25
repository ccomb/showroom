#!/usr/bin/env bash
# PARAMS:name, login=admin, password, version=3.3.5, plugins
set -e


# create a virtualenv
virtualenv -p python2.4 --no-site-packages --distribute sandbox

# install the project templates
sandbox/bin/pip install --download-cache=$HOME/eggs ZopeSkel==2.17
sandbox/bin/pip install --download-cache=$HOME/eggs -f http://dist.plone.org/thirdparty/ PILwoTk==1.1.6.4

# create a project
sandbox/bin/paster create --no-interactive -t plone3_buildout plone3 plone_version=$version zope_user=$login zope_password=$password http_port=$PORT
cd plone3

# add plugins
for package in $plugins; do
    sed -i "1,30s/^eggs =/eggs =\n    $package/" buildout.cfg
done

# build the application
../sandbox/bin/python bootstrap.py -d -v 1.4.3
./bin/buildout

# create the startup script
cat > ../start.sh << EOF
#!/usr/bin/env sh
exec plone3/bin/instance console
EOF

# create site
#cat > bin/initialize.py << EOF
## -*- coding: utf-8 -*-
#import os
#import transaction
#from AccessControl.SecurityManagement import newSecurityManager
#from Testing.makerequest import makerequest
#app=makerequest(app)
#
#user = app.acl_users.getUserById('admin')
#user = user.__of__(app.acl_users)
#newSecurityManager(None, user)
#
#print 'Adding plone site'
#app.manage_addProduct['CMFPlone'].addPloneSite(os.environ['name'])
#site = app[os.environ['name']]
#
##print 'Adding user. Dont work for now'
#site.portal_registration.addMember('$login', '$password', ['Manager'])
#transaction.commit()
#EOF
#
#bin/instance run bin/initialize.py

