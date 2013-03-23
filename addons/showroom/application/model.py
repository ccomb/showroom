from openerp.osv import osv, fields


class Application(osv.Model):
    """A demo application
    """
    _name = 'showroom.application'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            help='Name of the application'),
        'host_id': fields.many2one(
            'showroom.server',
            'Server',
            help='Server on which the application runs'),
        'user_id': fields.many2one(
            'res.users',
            'Owner',
            help='Owner of the application'),
        'permanent': fields.boolean(
            'Permanent',
            help='Application is permanent',
            readonly=True),
        'template_id': fields.many2one(
            'showroom.template',
            'Type',
            help='Type of app'),
    }
