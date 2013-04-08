from openerp.osv import osv, fields
from os.path import join, dirname, exists, isdir
import logging
import os
import shutil
import string
import subprocess

_logger = logging.getLogger(__name__)
HERE = dirname(dirname(__file__))
PATHS = {
    #  'bin' : join(HERE, CONFIG.get('paths', 'bin')),
    'scripts': join(HERE, 'template', 'scripts'),
    'templates': join(HERE, 'templates'),
    #  'templates' : join(HERE, CONFIG.get('paths', 'templates')),
    #  'var' : join(HERE, CONFIG.get('paths', 'var')),
    #  'etc' : join(HERE, CONFIG.get('paths', 'etc')),
}

# create directories if they don't exist
for d in PATHS:
    directory = PATHS[d]
    if not exists(directory) and not isdir(directory):
        os.makedirs(directory)
        _logger.info('Created %s', directory)


class InstallationError(Exception):
    pass


class DestructionError(Exception):
    pass


class Template(osv.Model):
    """An application template.
    The template is installed locally from a script, then is deployed on hosts.
    """
    _name = 'showroom.template'
    _inherit = ['mail.thread']

    def _get_scripts(self, cr, uid, context):
        scripts = [(filename, filename[5:-3])
                   for filename in os.listdir(PATHS['scripts'])
                   if filename.startswith('demo_')
                   and filename.endswith('.sh')]
        return scripts

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
        'state': fields.selection(
            [('draft', 'Draft'),
             ('installing', 'Installing'),
             ('install_error', 'Cannot install'),
             ('installed', 'Installed'),
             ('deploying', 'Deploying'),
             ('deploy_error', 'Cannot deploy'),
             ('deployed', 'Deployed'),
             ('undeploying', 'Undeploying'),
             ('undeploy_error', 'Cannot undeploy'),
             ('uninstalling', 'Uninstalling'),
             ('uninstall_error', 'Cannot uninstall'),
             ],
            'State',
            required=True,
            help='Current state of the template'),
        'script': fields.selection(
            _get_scripts,
            'Build script',
            required=True,
            help='The build script to use for the template'),
        'params': fields.one2many(
            'showroom.template.param',
            'template_id',
            'Parameters'),
        'user_id': fields.many2one('res.users', u'Template owner'),
    }

    _defaults = {
        'state': 'draft',
        'user_id': lambda self, cr, uid, context: uid,
    }

    def onchange_script(self, cr, uid, ids, filename):
        params = {}
        data = {'value': {'params': []}}
        if not filename:
            return data
        with open(join(PATHS['scripts'], filename)) as script:
            for line in script:
                if line.split(':')[0].strip() == '# PARAMS':
                    # params looks like: ['version=6.26', 'plugins']
                    params = [s.split('=') for s in
                              map(string.strip, line.strip().split(':')[1].split(','))
                              if s != '']
                    break
        # appending (5,) in the first place allows to empty the field XXX replace with 3,0,[...]
        data = {'value': {'params': [(5,)] + [
            (0, 0, {'key': param[0],
                    'value': (param[1:] or [''])[0]}
             ) for param in params]}}
        # data look like:
        # {'value': {'params': [(0, 0, {'key': 'foo1', 'value': 'bar1'}),
        #                       (0, 0, {'key': 'foo2', 'value': 'bar2'})]}}
        return data

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context)

    def install(self, cr, uid, ids, context=None):
        host_id = self.pool.get('showroom.server').search(
            cr, uid, [('name', '=', 'localhost')])
        if not host_id:
            raise osv.except_osv(
                'Error',
                'You cannot install a template without at least a localhost server')
        self.write(cr, uid, ids, {'state': 'installing'}, context)
        for template in self.browse(cr, uid, ids, context):
            self.pool.get('showroom.job').create(cr, uid, {
                'name': 'install',
                'model': 'showroom.template',
                'res_id': template.id,
                'function': '_install',
                'kwargs': {
                    'script': template.script,
                    'params':
                        dict([(p.key, p.value) for p in template.params]
                             + [('name', template.name)])
                },
                'host_id': host_id[0],
                'success_signal': 'install_ok',
                'failure_signal': 'install_failed',
            })

    def install_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'install_error'}, context)

    def installed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'installed'}, context)

    def deploy(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'deploying'}, context)

    def deploy_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'deploy_error'}, context)

    def deployed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'deployed'}, context)

    def undeploy(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'undeploying'}, context)

    def undeploy_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'undeploy_error'}, context)

    def uninstall(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'uninstalling'}, context)

    def uninstall_error(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'uninstall_error'}, context)

    def _install(self, cr, uid, **kwargs):
        """ This method is run from the threaded job
        It runs the template installation script
        """
        config_obj = self.pool.get('ir.config_parameter')
        script = kwargs['script']
        params = kwargs['params']
        app_name = params['name']
        # add environment variables for the install script
        env = os.environ.copy()
        env['name'] = app_name

        # put the virtualenv path first
        env['PATH'] = os.path.abspath('bin') + ':' + env['PATH']
        env['HOST'] = config_obj.get_param(cr, uid, 'showroom.admin_host')
        env.update(params)
        # add an http_proxy to manage a download cache
        PROXY_HOST = config_obj.get_param(cr, uid, 'showroom.proxy_host')
        PROXY_PORT = config_obj.get_param(cr, uid, 'showroom.proxy_port')
        env['http_proxy'] = 'http://%s:%s/' % (PROXY_HOST, PROXY_PORT)

        # create the directory for the demo
        user = self.pool.get('res.users').read(cr, uid, uid, ['name'])
        userpath = join(PATHS['templates'], str(user['id']) + '_' + user['name'])
        if not os.path.exists(userpath):
            os.mkdir(userpath)
        demopath = join(userpath, app_name)
        if not os.path.exists(demopath):
            os.mkdir(demopath)
        else:
            raise InstallationError(
                'This template already exists on the filesystem: %s'
                % demopath)

        # run the install script
        util_functions = join(PATHS['scripts'], 'functions.sh')
        install_functions = join(PATHS['scripts'], script)
        shell_command = [
            'bash',
            '-c',
            'source "%s" && source "%s" && export -f first_install && bash -xce first_install'
            % (util_functions, install_functions)]
        _logger.debug('Running: %s from: %s',
                      ' '.join(shell_command),
                      demopath)
        # TODO run on a remote host with salt?
        try:
            retcode = subprocess.call(shell_command, cwd=demopath, env=env)
            if retcode != 0:
                raise InstallationError('Installation script ended with an error')
        except Exception:
            _logger.debug('Deleted %s', demopath)
            shutil.rmtree(demopath)
            raise

        # set the start script to executable
        start_script = join(demopath, 'start.sh')
        if os.path.exists(start_script):
            os.chmod(start_script, 0744)
            # add a shebang and trap if forgotten
            with open(start_script, 'r+') as s:
                start = ''
                content = s.read()
                if (not content.startswith('#!')
                    or all([not line.startswith('trap')
                            for line in content.splitlines()[:5]])):
                    start = '#!/bin/bash\ntrap "pkill -P \$\$" EXIT\n'
                content = start + content
                s.seek(0)
                s.truncate()
                s.write(content)

        _logger.info('Finished installing %s', app_name)


class Parameter(osv.Model):
    """ A template parameter
    """
    _name = 'showroom.template.param'
    _columns = {
        'template_id': fields.many2one(
            'showroom.template',
            'Template',
            ondelete='cascade'),
        'key': fields.char('Parameter', 64),
        'value': fields.char('Value', 64)
    }
