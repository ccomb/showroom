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

    def _choose_server(self, cr, uid, ids, context=None):
        """ Select an available server for the application
        """
        server_obj = self.pool.get('showroom.server')
        server_ids = server_obj.search(cr, uid, [])
        chosen_server = None
        for server in server_obj.browse(cr, uid, server_ids):
            if len(server.application_ids) < server.max_applications:
                chosen_server = server.id
        if chosen_server is None:
            raise osv.except_osv(
                'Error',
                'No more available server now. Please retry later.')
        return chosen_server

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
