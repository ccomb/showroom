from openerp.osv import osv, fields


class Template(osv.Model):
    """An application template
    """
    _name = 'showroom.template'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            help='Name of the template'),
        'instance_ids': fields.one2many(
            'showroom.instance',
            'template_id',
            'Current instances',
            help='Current instances for this template'),
    }


