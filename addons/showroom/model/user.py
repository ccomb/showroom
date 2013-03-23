from openerp.osv import osv, fields


class User(osv.Model):
    """ Owner of the instance
    """
    _inherit = 'res.users'

    _columns = {
        'instance_ids': fields.one2many(
            'showroom.instance',
            'user_id',
            'Instances',
            help='Your instances'),
    }
