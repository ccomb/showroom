from openerp.osv import osv, fields


class Template(osv.Model):
    """An application template.
    The template is installed locally then is deployed on hosts
    """
    _name = 'showroom.template'

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
