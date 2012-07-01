# -*- coding: utf-8 -*-
from pyramid_signup.managers import UserManager
from ConfigParser import SafeConfigParser
from os.path import isdir, join, dirname, exists
from xmlrpclib import ServerProxy
from base64 import b64encode
import logging
import os
import shutil
import string
import subprocess
import urllib
import time

#logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

CONFIG = SafeConfigParser()
PATH = dirname(dirname(__file__))

CONFIG.read(join(PATH, 'showroom.ini'))
# XXX don't use this file for that
PATHS = {
  'bin' : join(PATH, CONFIG.get('paths', 'bin')),
  'scripts' : join(PATH, CONFIG.get('paths', 'scripts')),
  'demos' : join(PATH, CONFIG.get('paths', 'demos')),
  'templates' : join(PATH, CONFIG.get('paths', 'templates')),
  'var' : join(PATH, CONFIG.get('paths', 'var')),
  'etc' : join(PATH, CONFIG.get('paths', 'etc')),
  'supervisor' : join(PATH, CONFIG.get('paths', 'supervisor')),
}
ADMIN_HOST = CONFIG.get('global', 'hostname')
PROXY_HOST = CONFIG.get('global', 'proxy_host')
PROXY_PORT = CONFIG.get('global', 'proxy_port')

# create directories if they don't exist
for d in PATHS:
    directory = PATHS[d]
    if not exists(directory) and not isdir(directory):
        os.makedirs(directory)
        LOG.info('%s created.', directory)


class SuperVisor(object):
    """class to manage the supervisor process
    """
    def __init__(self, user, configpath=None):
        self.user = user
        # connect to supervisor
        if configpath is None:
            self.configpath = PATHS['supervisor']
        else:
            self.configpath = configpath
        supervisor_conf = SafeConfigParser()
        supervisor_conf.read(self.configpath)
        serverurl = supervisor_conf.get('supervisorctl', 'serverurl')
        self.xmlrpc = ServerProxy(serverurl)

    @property
    def is_running(self):
        try:
            self.xmlrpc.supervisor.getPID()
            return True
        except:
            return False

    def start(self):
        if self.is_running:
            LOG.info(u'OK, supervisor was already running.')
            return
        else:
            LOG.info(u'Starting supervisor...')
            subprocess.Popen([join(PATH, 'bin', 'supervisord'),
                              '-c', PATHS['supervisor']],
                              close_fds=True).wait()
        assert(self.is_running), "Could not start supervisor"

    def stop(self):
        # remove hard links for apache configs
        for demo in installed_demos(self.user):
            demo =  InstalledDemo(self.user, demo['name'])
            if demo.has_apache_link:
                demo._a2dissite(reload=False)
        # shutdown supervisor and all demos
        subprocess.Popen([join(PATH, 'bin', 'supervisorctl'),
                          '-c', PATHS['supervisor'], 'shutdown']).wait()


def daemon(user, name, command='restart'):
    """function that start, stop or restart the demo.
    We read the command in the apps config file
    """
    demos = installed_demos(user)
    if not demos.has_key(name) or not demos[name].has_key(command):
        print 'command %s not found for %s' % (command, name)
        return

    demopath = demos[name]['path']

    # if we don't have a stop command, kill the app
    if (command == 'stop'
      and demos[name]['command'].strip() == ''
      and os.path.exists(join(demopath, 'pid'))):
        cmd = "kill %s" % open(join(demopath, 'pid')).read()
    else:
        cmd = join(demopath, demos[name]['command'])


    if cmd.strip() == '':
        print "unable to %s %s" % (name, command)
        return
    else:
        LOG.warn('%sing %s: %s', command, name, cmd)
        pid = subprocess.Popen(cmd.split(), cwd=demopath).pid
        if pid and command == 'start':
            with open(join(demopath, 'pid'), 'w') as pidfile:
                pidfile.write(str(pid))
                return pid


def available_demos(user=None):
    """ return a dict containing all available demos
    and their respective commands defined in config file.

    >>> available_demos()['repoze.BFG']['params']
    ['name']
    """
    demos = {}
    for filename in [ filename for filename in os.listdir(PATHS['scripts'])
                      if filename.startswith('demo_')
                      and filename.endswith('.sh')]:
        params = []
        for line in open(join(PATHS['scripts'], filename)):
            if line.split(':')[0].strip() == '# PARAMS':
                # params looks like: ['name', 'version=6.26', 'plugins']
                params = map(string.strip, line.strip().split(':')[1].split(','))

        demos[(filename[5:-3])] = {'params':params}
    return demos


def installed_demos(user):
    """ return a dict with infos of deployed demos,
        or info of a single demo
    """
    demo_infos = []
    try:
        names = os.listdir(join(PATHS['demos'], user.username))
    except:
        return []
    for name in names:
        if not isdir(join(PATHS['demos'], user.username, name)):
            continue
        demo = InstalledDemo(user, name)
        demo_infos.append(dict(
            name=demo.name,
            port=demo.port,
            status = demo.get_status(),
            comment='',
            #comment=demo.get_comment()
        ))
    return demo_infos


class InstalledDemo(object):
    """object representing an installed demo
    """
    broken = False
    def __init__(self, user, name):
        self.user = user
        self.name = name
        if self.name == '':
            raise ValueError('empty demo name')
        self.path = join(PATHS['demos'], user.username, self.name)
        if not os.path.exists(self.path):
            raise Exception('this demo does not exist')
        self.start_script = join(self.path, 'start.sh')
        self.apache_config_file = join(self.path, 'apache2.conf')
        self.apache_config_link = join(PATHS['var'], 'apache2', 'demos', name + '.conf')
        self.popup = None
        self.popup_file = join(self.path, 'popup.html')
        if self.has_popup:
            with open(self.popup_file) as p:
                self.popup = p.read()
        # read the demo config
        self.democonf = SafeConfigParser()
        self.democonf_path = join(self.path, 'demo.conf')
        self.democonf.read(self.democonf_path)
        try:
            self.port = self.democonf.get('params', 'port')
        except:
            LOG.warning(u'Demo %s seems broken: no port' % self.name)
            self.port = ''
        # get the real name of the demo
        self.name = self.democonf.get('params', 'name')

        # init the supervisor
        self.supervisor = SuperVisor(self.user)

    has_startup_script = property(lambda self: os.path.exists(self.start_script))
    has_apache_link = property(lambda self: os.path.exists(self.apache_config_link))
    has_apache_conf = property(lambda self: os.path.exists(self.apache_config_file))
    has_popup = property(lambda self: os.path.exists(self.popup_file))

    @property
    def is_popup_displayed(self):
        """tells if the popup should be displayed
        """
        try:
            return self.democonf.getboolean('params', 'displaypopup')
        except Exception:
            return True

    def disable_popup(self):
        """disable the popup
        """
        self.democonf.set('params', 'displaypopup', '0')
        with open(self.democonf_path, 'w') as democonf_file:
            self.democonf.write(democonf_file)

    def get_status(self):
        """return the status of the demo
        We use the same status as supervisor
        """
        if not os.path.exists(self.path):
            return 'DESTROYED'
        app_conf_path = join(PATHS['demos'], self.user.username, self.name, 'demo.conf')
        if os.path.exists(app_conf_path):
            app_conf = SafeConfigParser()
            app_conf.read(app_conf_path)
            if app_conf.has_section('params') \
            and app_conf.has_option('params', 'status'):
                return app_conf.get('params', 'status')
        if self.port is '':
            return 'FATAL'

        statuses = set()
        democontent = os.listdir(self.path)
        
        # get the status of the process monitored by supervisor if any
        if 'supervisor.cfg' in democontent:
            try:
                status = self.supervisor.xmlrpc.supervisor.getProcessInfo(self.name)['statename']
            except:
                status = 'UNKNOWN'
            statuses.add(status)

        apache_links = os.listdir(join(PATHS['var'], 'apache2', 'demos'))

        # get the status of apache
        if 'apache2.conf' in democontent:
            # unless Apache is stopped
            try:
                status = self.supervisor.xmlrpc.supervisor.getProcessInfo('apache2')['statename']
            except:
                status = 'UNKNOWN'
            # consider apache running if we have a link
            if status == 'RUNNING':
                if self.name + '.conf' not in apache_links:
                    status = 'STOPPED'
            statuses.add(status)

        if len(statuses) == 1:
            # consistent state
            return statuses.pop()
        elif len(statuses) > 1 and 'RUNNING' in statuses:
            # half started!
            return 'PARTIAL'
        else:
            return 'FATAL'

    def start(self):
        """start the demo
        """
        if self.has_startup_script:
            self.supervisor.xmlrpc.supervisor.startProcess(self.name)
        if self.has_apache_conf:
            self._a2ensite()

    def stop(self):
        """stop the demo
        """
        if self.has_startup_script:
            try:
                self.supervisor.xmlrpc.supervisor.stopProcess(self.name)
            except:
                LOG.warning('Could not stop %s' % self.name)
        if self.has_apache_link:
            self._a2dissite()
        assert(self.get_status() != 'RUNNING'), "Stopping the demo failed"

    def _reload_apache(self):
        """reload apache config, or shutdown if it is not needed anymore
        """
        apache_confs = [conf
                        for conf in os.listdir(join(PATHS['var'], 'apache2', 'demos'))
                        if conf.endswith('.conf')]

        if len(apache_confs) == 0:
            # no more demos needing apache, we stop it
            self.supervisor.xmlrpc.supervisor.stopProcess('apache2')
        else:
            # reload the config or start Apache if needed (WITH supervisor!)
            a2status = self.supervisor.xmlrpc.supervisor.getProcessInfo('apache2')['statename']
            if a2status == 'RUNNING':
                subprocess.call(
                    ["/usr/sbin/apache2ctl",  "-f", PATHS['etc']+"/apache2/apache2.conf", "-k", "graceful"])
            else:
                self.supervisor.xmlrpc.supervisor.startProcess('apache2')


    def _a2ensite(self):
        """sandbox equivalent to the Apache a2ensite command
        """
        config_file = join(PATHS['demos'], self.user.username, self.name, 'apache2.conf')
        config_link = join(PATHS['var'], 'apache2', 'demos', self.name + '.conf')
        config_dir = join(PATHS['var'], 'apache2', 'demos')
        if os.path.exists(config_file) and not os.path.exists(config_link):
            if not os.path.exists(config_dir):
                os.mkdir(config_dir)
            os.link(config_file, config_link)
            # if apache doesn't restart because of us,
            # we should disable the new config and stop the app.
            # Supervisor should immediately try to restart apache
        self._reload_apache()
        time.sleep(0.5) # :( http://httpd.apache.org/docs/2.0/stopping.html
        try:
            urllib.urlopen('http://localhost:%s/server-status' % self.port)
        except Exception:
            self.stop()


    def _a2dissite(self, reload=True):
        """sandbox equivalent to the Apache a2dissite command
        """
        config_link = join(PATHS['var'], 'apache2', 'demos', self.name + '.conf')
        if os.path.exists(config_link):
            os.remove(config_link)
            if reload:
                self._reload_apache()

    def destroy(self):
        if not os.path.exists(self.path):
            raise DestructionError('this demo does not exist')
        if self.get_status() in ('RUNNING', 'STARTING'):
            self.stop()
        LOG.warn("removing demo %s" % self.name)
        had_startup_script = self.has_startup_script
        if isdir(self.path):
            subprocess.call(['chmod', '-R', '777', self.path])
            shutil.rmtree(self.path)

        userpath = dirname(self.path)
        if not os.listdir(userpath):
            os.unlink(userpath)

        if had_startup_script:
            try:
                self.supervisor.xmlrpc.supervisor.removeProcessGroup(self.name)
            except:
                LOG.warning(u'Got error trying to remove %s' % self.name)
            try:
                self.supervisor.xmlrpc.supervisor.reloadConfig()
            except:
                LOG.warning(u'Got error trying to reload supervisor config')


def get_available_port(request):
    """ return the first available port
    """
    demos = []
    users = os.listdir(PATHS['demos'])
    for user in users:
        demos += installed_demos(UserManager(request).get_by_username(user))
    ports = [int(demo['port']) for demo in demos if demo['port'].isdigit()]
    port = 20000
    while port in ports:
        port += 1
    return port


class DeploymentError(Exception):
    pass


class DestructionError(Exception):
    pass


def deploy(user, params):
    """deploy a demo of 'app_type' in the 'app_name' directory
    """
    app_name = params.pop('name')
    app_type = params.pop('app')
    if app_type not in available_demos():
        raise DeploymentError('this demo does not exist')

    if app_name in [d['name'] for d in installed_demos(user)]:
        raise DeploymentError('this demo already exists')

    # rebuild the name of the deployment script
    script = join(PATHS['scripts'], "demo_"+app_type+".sh")

    # *check the script* #FIXME move in a function

    # add environment variables for the deployment script
    env = os.environ.copy()
    env['name'] = app_name

    port = params.pop('port')
    env['PORT'] = str(port)
    # put the virtualenv path first
    env['PATH'] = os.path.abspath('bin') + ':' + env['PATH']
    env['HOST'] = ADMIN_HOST
    env.update(params)
    # add an http_proxy to manage a download cache
    env['http_proxy'] = 'http://%s:%s/' % (PROXY_HOST, PROXY_PORT)

    # create the directory for the demo
    userpath = join(PATHS['demos'], user.username)
    if not os.path.exists(userpath):
        os.mkdir(userpath)
    demopath = join(userpath, app_name)
    if not os.path.exists(demopath):
        os.mkdir(demopath)
    else:
        raise DeploymentError('this app already exists')

    # create a config file in the demo directory
    app_conf = SafeConfigParser()
    app_conf.add_section('params')
    app_conf.set('params', 'port', str(port))
    app_conf.set('params', 'name', app_name.encode('utf-8'))
    app_conf.set('params', 'status', 'DEPLOYING')
    for param_name, param_value in params.items():
        assert(param_name not in ('port', 'status'))
        app_conf.set('params', param_name, param_value.encode('utf-8'))
    app_conf_path = join(demopath, 'demo.conf')
    with open(app_conf_path, 'w+') as configfile:
        app_conf.write(configfile)
    LOG.info('section %s added', app_name)

    # check whether we already have a template available
    template_name = app_type + '_' + '_' + b64encode(
      ','.join(['%s=%s' % (n.strip(), '\n'.join([i.strip() for i in str(v).split('\n')]))
                for (n, v) in sorted(params.items()) if n not in ('name','login','user','password')]))
    template_path = join(PATHS['templates'], template_name)

    if os.path.exists(template_path):
        for item in os.listdir(template_path):
            # XXX replace this waste of space with a btrfs subvolume
            subprocess.call(['cp', '-r', join(template_path, item), demopath])
        # run the clone reconfiguration script
        old_demo = InstalledDemo(user, app_name)
        functions = join(PATHS['scripts'], 'functions.sh')
        retcode = subprocess.call(['bash', '-c', 'source "%s" && source "%s" && export -f reconfigure_clone && bash -xce "reconfigure_clone \"%s\" %s"' % (functions, script, old_demo.name, old_demo.port)], cwd=demopath, env=env)
        if retcode != 0:
            shutil.rmtree(demopath)
            raise DeploymentError('installation ended with an error')

    else:
        # run the deployment script
        LOG.debug(script)
        functions = join(PATHS['scripts'], 'functions.sh')
        retcode = subprocess.call(['bash', '-c', 'source "%s" && source "%s" && export -f first_install && bash -xce first_install' % (functions, script)], cwd=demopath, env=env)
        if retcode != 0:
            shutil.rmtree(demopath)
            raise DeploymentError('installation ended with an error')
    
    # set the start script to executable
    start_script = join(demopath, 'start.sh')
    if os.path.exists(start_script):
        os.chmod(start_script, 0744)
        # add a shebang and trap if forgotten
        with open(start_script, 'r+') as s:
            start = ''
            content = s.read()
            if (not content.startswith('#!')
                or all([not line.startswith('trap') for line in content.splitlines()[:5]])):
                start = '#!/bin/bash\ntrap "pkill -P \$\$" EXIT\n'
            content = start + content
            s.seek(0); s.truncate(); s.write(content)
    
    # add a supervisor include file for this program
    start_script = join(demopath, 'start.sh')
    if os.path.exists(start_script):
        supervisor_conf = SafeConfigParser()
        section = 'program:%s' % app_name
        supervisor_conf.add_section(section)
        supervisor_conf.set(section, 'command', start_script)
        supervisor_conf.set(section, 'directory', demopath)
        supervisor_conf.set(section, 'autostart', 'false')
        supervisor_conf.set(section, 'autorestart', 'false')
        supervisor_conf.set(section, 'startsecs', '2')
        with open(join(demopath, 'supervisor.cfg'), 'w') as supervisor_file:
            supervisor_conf.write(supervisor_file)
    
        # reload the supervisor config
        supervisor = SuperVisor(self.user)
        supervisor.xmlrpc.supervisor.reloadConfig()
        supervisor.xmlrpc.supervisor.addProcessGroup(app_name)

    app_conf = SafeConfigParser()
    app_conf.read(app_conf_path)
    app_conf.set('params', 'name', app_name.encode('utf-8'))
    app_conf.set('params', 'port', str(port))
    app_conf.remove_option('params', 'status')
    with open(app_conf_path, 'w+') as configfile:
        app_conf.write(configfile)
    LOG.info('Finished deploying %s', app_name)

    # now save this app in a template for cloning
    if not os.path.exists(template_path):
        shutil.copytree(demopath, template_path)


class WorkingDirectoryKeeper(object):
    """Context manager to get back to the previous working dir at exit
    """
    def __enter__(self):
        self.wd = os.getcwd()

    def __exit__(self, *exc_args):
        os.chdir(self.wd)

keep_working_dir = WorkingDirectoryKeeper()

