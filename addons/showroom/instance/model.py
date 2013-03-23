from openerp.osv import osv, fields


class Instance(osv.Model):
    """A demo instance
    """
    _name = 'showroom.instance'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            help='Name of the instance'),
        'host_id': fields.many2one(
            'showroom.server',
            'Server',
            help='Server on which the instance runs'),
        'user_id': fields.many2one(
            'res.users',
            'Owner',
            help='Owner of the instance'),
        'permanent': fields.boolean(
            'Permanent',
            help='Instance is permanent'),
        'template_id': fields.many2one(
            'showroom.template',
            'Type',
            help='Type of app'),
    }
