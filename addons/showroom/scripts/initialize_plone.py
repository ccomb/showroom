# -*- coding: utf-8 -*-
import os
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest

user = app.acl_users.getUserById('admin')
newSecurityManager(None, user)
app=makerequest(app)

print 'Adding plone site'
app.manage_addProduct['CMFPlone'].addPloneSite(os.environ['name'])
site = app[os.environ['name']]

print 'Adding user'
site.acl_users.source_users.doAddUser('admin', 'admin')
site.acl_users.source_groups.addPrincipalToGroup('admin', 'Administrators')
transaction.commit()
