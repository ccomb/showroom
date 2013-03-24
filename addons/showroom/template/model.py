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
    }
