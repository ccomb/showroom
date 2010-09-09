# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
from os.path import isdir, join, dirname
from xmlrpclib import ServerProxy
import logging
import os
import shutil
import socket
import string
import subprocess

LOG = logging.getLogger(__name__)

CONFIG = SafeConfigParser()
PATH = dirname(dirname(__file__))

CONFIG.read(join(PATH, 'deploy.ini'))
# XXX don't use this file for that
PATHS = {
  'bin' : join(PATH, CONFIG.get('paths', 'bin')),
  'scripts' : join(PATH, CONFIG.get('paths', 'scripts')),
  'demos' : join(PATH, CONFIG.get('paths', 'demos')),
  'var' : join(PATH, CONFIG.get('paths', 'var')),
  'etc' : join(PATH, CONFIG.get('paths', 'etc')),
  'supervisor' : join(PATH, CONFIG.get('paths', 'supervisor')),
}
ADMIN_HOST = CONFIG.get('DEFAULT', 'hostname')
del CONFIG

if not isdir(PATHS['demos']):
    os.makedirs(PATHS['demos'])
    LOG.info('%s created.', PATHS['demos'])

XMLRPC = None

def connect_supervisor():
    # connect to supervisor
    supervisor_conf = SafeConfigParser()
    supervisor_conf.read(PATHS['supervisor'])
    global XMLRPC
    XMLRPC = ServerProxy(supervisor_conf.get('supervisorctl', 'serverurl'))

    # if not started, start supervisor in daemon mode
    try:
        XMLRPC.supervisor.getPID()
        LOG.info(u'OK, supervisor was already running.')
    except socket.error:
        LOG.info(u'Starting supervisor...')
        subprocess.Popen([join(PATH, 'bin', 'supervisord'),
                          '-c', PATHS['supervisor']]).wait()
    # try again
    XMLRPC.supervisor.getPID()

from awsdemos import currently_testing
if not currently_testing:
    connect_supervisor()

#@atexit.register
#def stop_supervisor():
#    subprocess.call("bin/supervisorctl -c supervisord.cfg shutdown", shell=True)


def daemon(name, command='restart'):
    """function that start, stop or restart the demo.
    We read the command in the apps config file
    """
    demos = installed_demos()
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


def available_demos():
    """ return a dict containing all available demos
    and their respective commands defined in config file.

    >>> available_demos()['repoze.BFG']['params']
    ['NAME', 'COMMENT', 'TEST']
    >>> available_demos()['repoze.BFG']['plugins']
    []
    """
    demos = {}
    for filename in [ filename for filename in os.listdir(PATHS['scripts'])
                      if filename.startswith('demo_')
                      and filename.endswith('.sh')]:
        params = []
        plugins = []
        for line in open(join(PATHS['scripts'], filename)):
            if line.split(':')[0].strip() == '# PARAMS':
                params = map(string.strip, line.strip().split(':')[1].split(','))
            elif line.split(':')[0].strip() == '# PLUGINS':
                plugins = map(string.strip, line.strip().split(':')[1].split(','))

        demos[(filename[5:-3])] = {'params':params, 'plugins':plugins}
    return demos


def get_demo_comment(demo_name):
    """ return the content of "about.txt" in the directory of the application,
    if it exists.
    """
    if 'about.txt' in os.listdir(join(PATHS['demos'], demo_name)):
        return open(
            join(PATHS['demos'], demo_name, 'about.txt')
            ).read()
    else:
        return ''


def installed_demos():
    """ return a dict with infos of deployed demos,
        or info of a single demo
    """
    demo_infos = []
    demo_names = os.listdir(PATHS['demos'])
    for name in demo_names:
        demo = InstalledDemo(name)
        demo_infos.append(dict(
            name=demo.name,
            port=demo.get_port(),
            status = demo.get_status(),
            comment='',
            #comment=demo.get_comment()
        ))
    return demo_infos


class InstalledDemo(object):
    """object representing an installed demo
    """
    def __init__(self, name):
        self.name = name
        if self.name == '':
            raise ValueError('empty demo name')
        self.path = join(PATHS['demos'], self.name)
        self.start_script = join(PATHS['demos'], name, 'start.sh')
        self.apache_config_file = join(PATHS['demos'], name, 'apache2.conf')
        self.apache_config_link = join(PATHS['var'], 'apache2', 'demos', name + '.conf')

    has_startup_script = property(lambda self: os.path.exists(self.start_script))
    has_apache_link = property(lambda self: os.path.exists(self.apache_config_link))
    has_apache_conf = property(lambda self: os.path.exists(self.apache_config_file))

    def get_port(self):
        conf = SafeConfigParser()
        conf.read(join(PATHS['demos'], self.name, 'demo.conf'))
        return conf.get(self.name, 'port')

    def get_status(self):
        """return the status of the demo
        We use the same status as supervisor
        """
        status = 'STOPPED'
        if not os.path.exists(self.path):
            return 'DESTROYED'
        democontent = os.listdir(self.path)
        if 'supervisor.cfg' in democontent:
            try:
                status = XMLRPC.supervisor.getProcessInfo(self.name)['statename']
            except:
                status = 'STOPPED'
        apache_links = os.listdir(join(PATHS['var'], 'apache2', 'demos'))

        if 'apache2.conf' in democontent:
            if self.name + '.conf' in apache_links:
                status = 'RUNNING'
        return status

    def start(self):
        """start the demo
        """
        if self.has_startup_script:
            XMLRPC.supervisor.startProcess(self.name)
        if self.has_apache_conf:
            self._a2ensite(self.name)
            retcode = _reload_apache()
            # if apache doesn't restart because of us,
            # we should disable the new config
            # BUT we should let supervisor restart the app!!
            if retcode != 0:
                self._a2dissite()
                self.stop()

    def stop(self):
        """stop the demo
        """
        if self.has_startup_script:
            XMLRPC.supervisor.stopProcess(self.name)
        if self.has_apache_link:
            self._a2dissite()
            _reload_apache()

    def _a2ensite(self):
        """sandbox equivalent to the a2ensite command
        """
        config_file = join(PATHS['demos'], self.name, 'apache2.conf')
        config_link = join(PATHS['var'], 'apache2', 'demos', self.name + '.conf')
        config_dir = join(PATHS['var'], 'apache2', 'demos')
        if os.path.exists(config_file) and not os.path.exists(config_link):
            if not os.path.exists(config_dir):
                os.mkdir(config_dir)
            os.link(config_file, config_link)


    def _a2dissite(self):
        """sandbox equivalent to the a2dissite command
        """
        config_link = join(PATHS['var'], 'apache2', 'demos', self.name + '.conf')
        if os.path.exists(config_link):
            os.remove(config_link)

    def destroy(self):
        if self.name not in [d['name'] for d in installed_demos()]:
            raise DestructionError('this demo does not exist')
        start_script = join(PATHS['demos'], self.name, 'start.sh')
        if os.path.exists(start_script):
            try:
                status = XMLRPC.supervisor.getProcessInfo(self.name)['statename']
            except:
                status = 'STOPPED'
            if status == 'RUNNING':
                XMLRPC.supervisor.stopProcess(self.name)
            XMLRPC.supervisor.removeProcessGroup(self.name)

        LOG.warn("removing demo %s" % self.name)

        if os.path.isdir(self.path):
            shutil.rmtree(self.path)
        self._a2dissite()
        _reload_apache()


def _reload_apache():
    """reload apache config, or shutdown if it is not needed anymore
    """
    apache_confs = [conf
                    for conf in os.listdir(join(PATHS['var'], 'apache2', 'demos'))
                    if conf.endswith('.conf')]
    a2status = XMLRPC.supervisor.getProcessInfo('apache2')['statename']

    if len(apache_confs) == 0:
        if a2status == 'RUNNING':
            XMLRPC.supervisor.stopProcess('apache2')
    else:
        # reload the config or start Apache if needed (WITH supervisor!)
        a2status = XMLRPC.supervisor.getProcessInfo('apache2')['statename']
        if a2status == 'RUNNING':
            retcode = subprocess.call(
                ["apache2ctl",  "-f", "etc/apache2/apache2.conf", "-k", "graceful"])
            return retcode
        else:
            XMLRPC.supervisor.startProcess('apache2')





def get_available_port():
    """ return the first available port
    """
    demos = installed_demos()
    ports = [int(demo['port']) for demo in demos]
    port = 9000
    while port in ports:
        port += 1
    return port


class DeploymentError(Exception):
    pass


class DestructionError(Exception):
    pass


def deploy(app_type, app_name):
    """deploy a demo of 'app_type' in the 'app_name' directory
    """
    if app_type not in available_demos():
        raise DeploymentError('this demo does not exist')

    if app_name in [d['name'] for d in installed_demos()]:
        raise DeploymentError('this demo already exists')

    # rebuild the name of the deployment script
    script = join(PATHS['scripts'], "demo_"+app_type+".sh")

    # *check the script* #FIXME move in a function

    # add environment variables for the deployment script
    env = os.environ.copy()
    env['NAME'] = app_name

    port = get_available_port()
    env['PORT'] = str(port)
    # put the virtualenv path first
    env['PATH'] = os.path.abspath('bin') + ':' + env['PATH']
    env['HOST'] = ADMIN_HOST

    # create the directory for the demo
    demopath = join(PATHS['demos'], app_name)
    if not os.path.exists(demopath):
        os.mkdir(demopath)
    else:
        raise DeploymentError('this app already exists')

    # run the deployment script
    LOG.debug(script)
    retcode = subprocess.call('"'+script+'"', shell=True, cwd=demopath, env=env)
    if retcode != 0:
        shutil.rmtree(demopath)
        raise DeploymentError('installation ended with an error')

    # set the start script to executable
    start_script = join(demopath, 'start.sh')
    if os.path.exists(start_script):
        os.chmod(start_script, 0744)
        # add the shebang if forgotten
        with open(start_script, 'r+') as s:
            content = s.read()
            if not content.startswith('#!'):
                content = '#!/bin/bash\n' + content
                s.seek(0); s.truncate(); s.write(content)

        # add a supervisor include file for this program
        supervisor_conf = SafeConfigParser()
        section = 'program:%s' % app_name
        supervisor_conf.add_section(section)
        supervisor_conf.set(section, 'command', start_script)
        supervisor_conf.set(section, 'directory', demopath)
        supervisor_conf.set(section, 'autostart', 'false')
        supervisor_conf.set(section, 'autorestart', 'false')
        with open(join(demopath, 'supervisor.cfg'), 'w') as supervisor_file:
            supervisor_conf.write(supervisor_file)

        # reload the supervisor config
        XMLRPC.supervisor.reloadConfig()
        XMLRPC.supervisor.addProcessGroup(app_name)

    # create a config file in the demo directory
    app_conf = SafeConfigParser()
    app_conf.add_section(app_name)
    app_conf.set(app_name, 'port', str(port))
    with open(join(PATHS['demos'], app_name, 'demo.conf'), 'w+') as configfile:
        app_conf.write(configfile)
    LOG.info('section %s added', app_name)





