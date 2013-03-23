from openerp.osv import osv, fields


class Server(osv.Model):
    """ A server on which instances run
    """
    _name = 'showroom.server'

    _columns = {
        'name': fields.char(
            'Label',
            size=64,
            help='Hostname of the server'),
        'instance_ids': fields.one2many(
            'showroom.instance',
            'host_id',
            'Instances',
            help='List of instances on the server'),
    }
