#!/usr/bin/env bash
# PARAMS:name,LOGIN,PASSWORD
# PLUGINS:aws.minisite,Products.collage,collective.plonefinder,Products.FCKeditor
set -e


# create a virtualenv
virtualenv -p python2.4 --no-site-packages --distribute sandbox

# install the project templates
sandbox/bin/pip install --download-cache=$HOME/eggs ZopeSkel==2.17
sandbox/bin/pip install --download-cache=$HOME/eggs -f http://dist.plone.org/thirdparty/ PILwoTk==1.1.6.4

# create a project
sandbox/bin/paster create --no-interactive -t plone3_buildout plone3 plone_version=3.3.5 zope_user=$LOGIN zope_password=$PASSWORD http_port=$PORT
cd plone3

# build the application
../sandbox/bin/python bootstrap.py
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
#site.portal_registration.addMember('$LOGIN', '$PASSWORD', ['Manager'])
#transaction.commit()
#EOF
#
#bin/instance run bin/initialize.py

