from openerp.osv import osv, fields
#from ConfigParser import SafeConfigParser
from os.path import join, dirname
import os
import string

#CONFIG = SafeConfigParser()
HERE = dirname(dirname(__file__))
#CONFIG.read(join(HERE, 'showroom.ini'))
## XXX don't use this file for that
PATHS = {
    #  'bin' : join(HERE, CONFIG.get('paths', 'bin')),
    'scripts': join(HERE, 'template', 'scripts'),
    #  'demos' : join(HERE, CONFIG.get('paths', 'demos')),
    #  'templates' : join(HERE, CONFIG.get('paths', 'templates')),
    #  'var' : join(HERE, CONFIG.get('paths', 'var')),
    #  'etc' : join(HERE, CONFIG.get('paths', 'etc')),
}
#ADMIN_HOST = CONFIG.get('global', 'hostname')
#PROXY_HOST = CONFIG.get('global', 'proxy_host')
#PROXY_PORT = CONFIG.get('global', 'proxy_port')


class Template(osv.Model):
    """An application template.
    The template is installed locally from a script, then is deployed on hosts.
    """
    _name = 'showroom.template'

    def _get_scripts(self, cr, uid, context):
        scripts = [(filename, filename[5:-3])
                   for filename in os.listdir(PATHS['scripts'])
                   if filename.startswith('demo_')
                   and filename.endswith('.sh')]
        return scripts

    def onchange_script(self, cr, uid, ids, filename):
        params = {}
        data = {'value': {'params': []}}
        if not filename:
            return data
        with open(join(PATHS['scripts'], filename)) as script:
            for line in script:
                if line.split(':')[0].strip() == '# PARAMS':
                    # params looks like: ['version=6.26', 'plugins']
                    params = [s.split('=') for s in
                              map(string.strip, line.strip().split(':')[1].split(','))
                              if s != '']
                    break
        # appending (5,) in the first place allows to empty the field
        data = {'value': {'params': [(5,)] + [
            (0, 0, {'key': param[0],
                    'value': (param[1:] or [''])[0]}
             ) for param in params]}}
        # data look like:
        # {'value': {'params': [(0, 0, {'key': 'foo1', 'value': 'bar1'}),
        #                       (0, 0, {'key': 'foo2', 'value': 'bar2'})]}}
        return data

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            help='Name of the template'),
        'application_ids': fields.one2many(
            'showroom.application',
            'template_id',
            'Current applications',
            help='Current applications for this template'),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('installing', 'Installing'),
             ('install_error', 'Cannot install'),
             ('installed', 'Installed'),
             ('deploying', 'Deploying'),
             ('deploy_error', 'Cannot deploy'),
             ('deployed', 'Deployed'),
             ('undeploying', 'Undeploying'),
             ('undeploy_error', 'Cannot undeploy'),
             ('uninstalling', 'Uninstalling'),
             ('uninstall_error', 'Cannot uninstall'),
             ],
            'State',
            required=True,
            help='Current state of the template'),
        'script': fields.selection(
            _get_scripts,
            'Build script',
            required=True,
            help='The build script to use for the template'),
        'params': fields.one2many(
            'showroom.template.param',
            'template_id',
            'Parameters'),
        #'toto2': fields.sparse('params', type='char'),

    }

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context)

    def install(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'installing'}, context)

    def install_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'install_error'}, context)

    def installed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'installed'}, context)

    def deploy(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'deploying'}, context)

    def deploy_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'deploy_error'}, context)

    def deployed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'deployed'}, context)

    def undeploy(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'undeploying'}, context)

    def undeploy_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'undeploy_error'}, context)

    def uninstall(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'uninstalling'}, context)

    def uninstall_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'uninstall_error'}, context)

    _defaults = {
        'state': 'draft',
    }


class Parameter(osv.Model):
    """ A template parameter
    """
    _name = 'showroom.template.param'
    _columns = {
        'template_id': fields.many2one(
            'showroom.template',
            'Template',
            ondelete='cascade'),
        'key': fields.char('Parameter', 64),
        'value': fields.char('Value', 64)
    }
