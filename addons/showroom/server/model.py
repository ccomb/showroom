from openerp.osv import osv, fields


class Server(osv.Model):
    """ A server on which applications run
    """
    _name = 'showroom.server'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            help='Hostname of the server'),
        'application_ids': fields.one2many(
            'showroom.application',
            'host_id',
            'Applications',
            help='List of applications on the server'),
    }
