#!/usr/bin/env bash
# PARAMS:name, login=admin, password, version=3.3.6, plugins

function first_install {
# create a virtualenv
virtualenv -p python2.4 --no-site-packages --distribute sandbox
virtualenv -p python2.4 --no-site-packages --distribute sandbox --relocatable

# install the project templates
sandbox/bin/pip install ZopeSkel==2.17 PasteDeploy==1.3.4 Paste==1.7.5.1 PasteScript==1.7.4.2
sandbox/bin/pip install -f http://dist.plone.org/thirdparty/ PILwoTk==1.1.6.4

# create a project
sandbox/bin/paster create --no-interactive -t plone3_buildout plone3 plone_version=$version zope_user=$login zope_password=$password http_port=$PORT
cd plone3

# add plugins
for package in $plugins; do
    sed -i "1,30s/^eggs =/eggs =\n    $package/" buildout.cfg
    sed -i "s/^zcml =/zcml =\n    $package/" buildout.cfg
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

# create a howto for installation instruction
cd ..
cat > howto.html << EOF
<p>To start using Plone 3, you must create a plone site. Do the following:</p>
<ol>
    <li>Click on <a href="manage_main">Zope Management Interface</a> and connect with the password you chose</li>
    <li>In the top right selection list, select "Plone Site"</li>
    <li>Choose an <i>Id</i> and a <i>Title</i> for your Plone site.<br/>
        The id will be visible in the URL<li/>
    <li>Click on "Add Plone Site", you should then see your site in the list</li>
    <li>Click on your site in the list</li>
    <li>Click on the "View" tab on the top</li>
    <li>Enjoy!</li>
</ol>
EOF
}

function reconfigure_clone {
cd plone3
sed -i "s/$2/$PORT/" buildout.cfg
sed -i "s/user = .*/user = $login:$password/" buildout.cfg
../sandbox/bin/python bootstrap.py -d -v 1.4.3
./bin/buildout -o

}
