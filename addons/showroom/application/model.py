from openerp.osv import osv, fields


class Application(osv.Model):
    """A demo application
    """
    _name = 'showroom.application'

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            readonly=True,
            required=True,
            states={'draft': [('readonly', False)]},
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
            readonly=True,
            required=True,
            states={'draft': [('readonly', False)]},
            help='Type of app'),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('cloning', 'Installing'),
             ('clone_error', 'Cannot install'),
             ('stopped', 'Stopped'),
             ('starting', 'Starting'),
             ('running', 'Running'),
             ('start_error', 'Cannot start'),
             ('destroying', 'Destroying'),
             ('destroy_error', 'Cannot destroy'),
             ('stop_error', 'Cannot stop'),
             ('stopping', 'Stopping'),
             ],
            'State',
            required=True,
            help='Current state of the application'),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'state': 'draft',
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

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context)

    def clone(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cloning'}, context)

    def _clone(self, cr, uid, ids, context=None):
        # create a container config
        container_config = (
            'lxc.utsname = bfg\n'
            'lxc.network.type = veth\n'
            'lxc.network.flags = up\n'
            'lxc.network.link = br0\n'
            'lxc.network.hwaddr = 0a:00:00:00:00:%(mac)s\n'
            'lxc.network.ipv4 = %(ip)s/24\n'
            % {'mac': params['mac'], 'ip': params['ip']}
        )
        with open(join(demopath, 'lxc.conf'), 'w+') as configfile:
            configfile.write(container_config)


    def clone_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'clone_error'}, context)

    def start(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'starting'}, context)

    def stop(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'stopping'}, context)

    def destroy(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'destroying'}, context)

    def running(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'running'}, context)

    def start_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'start_error'}, context)

    def stopped(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'stopped'}, context)

    def stop_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'stop_error'}, context)

    def destroy_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'destroy_error'}, context)

    def get_available_ip(): #TODO
        """ return the first available ip
        FIXME improve
        """
        demos = []
        users = os.listdir(PATHS['demos'])
        for user in users:
            demos += installed_demos(user)
        ips = [int(demo['ip'].split('.')[3]) for demo in demos if demo['ip'].isdigit()]
        ip = 1
        while ip in ips:
            ip += 1
        assert(ip<254) # fixme
        return '192.168.0.' + str(ip)

    def get_available_mac():
        """ return the first available mac address
        FIXME improve
        """
        demos = []
        users = os.listdir(PATHS['demos'])
        for user in users:
            demos += installed_demos(user)
        macs = [int(demo['mac'], 16) for demo in demos if demo['mac']!='']
        mac = 0
        while mac in macs:
            mac += 1
        assert(mac<254) # fixme
        return hex(mac)[2:]

