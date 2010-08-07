#!/usr/bin/env sh
# PARAMS:NAME,COMMENT,LOGIN,PASSWORD
# PLUGINS:aws.minisite,Products.collage,collective.plonefinder,Products.FCKeditor

set -e # explicit fail on errors

# create a virtualenv
virtualenv --no-site-packages --distribute sandbox

# install the project templates
sandbox/bin/pip install --download-cache=$HOME/eggs ZopeSkel==2.17 PIL==1.1.7

# create a project
sandbox/bin/paster create --no-interactive -t plone3_buildout plone4 plone_version=4.0rc1 zope_user=$LOGIN zope_password=$PASSWORD http_port=$PORT
cd plone4

# build the application
../sandbox/bin/python bootstrap.py
./bin/buildout

# create the startup script
cat > ../start.sh << EOF
#!/usr/bin/env sh
exec plone4/bin/instance console
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
#app.manage_addProduct['CMFPlone'].addPloneSite(os.environ['NAME'])
#site = app[os.environ['NAME']]
#
##print 'Adding user. Dont work for now'
#site.portal_registration.addMember('$LOGIN', '$PASSWORD', ['Manager'])
#transaction.commit()
#EOF
#
#bin/instance run bin/initialize.py

