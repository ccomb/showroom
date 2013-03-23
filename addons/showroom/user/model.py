from openerp.osv import osv, fields


class User(osv.Model):
    """ Owner of the application
    """
    _inherit = 'res.users'

    _columns = {
        'application_ids': fields.one2many(
            'showroom.application',
            'user_id',
            'Applications',
            help='Your applications'),
    }
