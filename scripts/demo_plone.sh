#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT

# load vars and fonctions
. scripts/config.sh

# set virtualenv (just in case)
python2.4 bin/virtualenv $DEMOS/$NAME --no-site-packages --distribute
. $DEMOS/$NAME/bin/activate

cd $DEMOS/$NAME

# create buildout conf, bootstrap and launch buildout
cat > buildout.cfg <<EOF
[buildout]
newest = false
parts =
    zope2
    instance
extends = http://dist.plone.org/release/3.3/versions.cfg
versions = versions
find-links =
    http://dist.plone.org/release/3.3
    http://download.zope.org/ppix/
    http://download.zope.org/distribution/
    http://effbot.org/downloads
eggs = PILwoTk
develop =

[zope2]
recipe = plone.recipe.zope2install
url = \${versions:zope2-url}

[instance]
recipe = plone.recipe.zope2instance
zope2-location = \${zope2:location}
user = admin:admin
http-address = $PORT
debug-mode = off
verbose-security = off
eggs =
    Plone
    \${buildout:eggs}
zcml = 
EOF

wget http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py
python bootstrap.py

bin/buildout

cat > starter.sh << EOF
#!/usr/bin/env sh
cd $DEMOS/$NAME
bin/instance fg
EOF

# create site
cat > bin/initialize.py << EOF
# -*- coding: utf-8 -*-
import os
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
app=makerequest(app)

user = app.acl_users.getUserById('admin')
user = user.__of__(app.acl_users)
newSecurityManager(None, user)

print 'Adding plone site'
app.manage_addProduct['CMFPlone'].addPloneSite(os.environ['NAME'])
site = app[os.environ['NAME']]

print 'Adding user. Dont work for now'
site.portal_registration.addMember('admin', 'admin', ['Manager'])
transaction.commit()
EOF

bin/instance run bin/initialize.py

#return to the supervisor directory
cd -
