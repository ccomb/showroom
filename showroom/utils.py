# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
from os.path import isdir, join, dirname, exists
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
        with open(join(PATHS['scripts'], filename)) as script:
            for line in script:
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
        names = os.listdir(join(PATHS['demos'], user))
    except:
        return []
    for name in names:
        if not isdir(join(PATHS['demos'], user, name)):
            continue
        demo = InstalledDemo(user, name)
        demo_infos.append(dict(
            name=demo.name,
            port=demo.port,
            ip=demo.ip,
            mac=demo.mac,
            status = demo.get_status(),
            comment='',
            #comment=demo.get_comment()
        ))
    return demo_infos


class InstalledDemo(object):
    """object representing an installed demo
    the "user" argument should be a string
    """
    broken = False
    def __init__(self, user, name):
        self.user = user
        self.name = name
        if self.name == '':
            raise ValueError('empty demo name')
        self.path = join(PATHS['demos'], user, self.name)
        if not os.path.exists(self.path):
            raise UnknownDemo('this demo does not exist')
        self.start_script = join(self.path, 'start.sh')
        self.apache_config_file = join(self.path, 'apache2.conf')
        self.apache_config_dir = join(PATHS['var'], 'apache2', 'demos')
        self.apache_config_link = join(self.apache_config_dir,
                                       user + '.' + name + '.conf')

        self.howto_file = join(self.path, 'howto.html')
        # read the demo config
        self.democonf = SafeConfigParser()
        self.democonf_path = join(self.path, 'demo.conf')
        self.democonf.read(self.democonf_path)
        try:
            self.mac = self.democonf.get('params', 'mac')
        except:
            LOG.warning(u'Demo %s seems broken: no mac' % self.name)
            self.mac = ''
        try:
            self.ip = self.democonf.get('params', 'ip')
        except:
            LOG.warning(u'Demo %s seems broken: no ip' % self.name)
            self.ip = ''
        try:
            self.port = self.democonf.get('params', 'port')
        except:
            LOG.warning(u'Demo %s seems broken: no port' % self.name)
            self.port = ''
        # get the real name of the demo
        self.name = self.democonf.get('params', 'name')
        if self.democonf.has_option('params', 'type'):
            self.type = self.democonf.get('params', 'type')
        else:
            self.type = 'Unknown'
        if self.democonf.has_option('params', 'version'):
            self.version = self.democonf.get('params', 'version')
        else:
            self.version = ''
        self.container_name = '_'.join([self.user, self.name])

    has_startup_script = property(lambda self: os.path.exists(self.start_script))
    has_apache_link = property(lambda self: os.path.exists(self.apache_config_link))
    has_apache_conf = property(lambda self: os.path.exists(self.apache_config_file))
    has_howto = property(lambda self: os.path.exists(self.howto_file))

    def get_status(self):
        """return the status of the demo
        We use the same status as lxc
        """
        # get the status of the lxc container if any
        status = subprocess.check_output(
            ['lxc-info', '-n', self.container_name]
            ).splitlines()[0].split(':')[1].strip()
        return status


    def howto(self):
        """retrieve the howto
        """
        if self.has_howto:
            with open(join(self.path, 'howto.html')) as howto_file:
                return howto_file.read()
        else:
            return 'No specific instructions'

    def start(self):
        """start the demo
        """
        if self.has_startup_script:
            subprocess.Popen(
                ['lxc-execute',
                 '-n', self.container_name,
                 '-f', 'lxc.conf',
                 './start.sh'],
                cwd=self.path)
        if self.has_apache_conf:
            self._a2ensite()

    def stop(self):
        """stop the demo
        """
        if self.get_status() == 'RUNNING':
            subprocess.Popen(['lxc-kill', '-n', self.container_name])
        if self.has_apache_link:
            self._a2dissite()

    def _reload_apache(self):
        """reload apache config, or shutdown if it is not needed anymore
        """
        apache_confs = [conf for conf in os.listdir(self.apache_config_dir)
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
        self.garbage_collect_apache_confs()
        if self.has_apache_conf and not self.has_apache_link:
            if not os.path.exists(self.apache_config_dir):
                os.mkdir(self.apache_config_dir)
            os.link(self.apache_config_file, self.apache_config_link)
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
        self.garbage_collect_apache_confs()
        if os.path.exists(self.apache_config_link):
            os.remove(self.apache_config_link)
            if reload:
                self._reload_apache()

    def destroy(self):
        if not os.path.exists(self.path):
            raise DestructionError('this demo does not exist')
        if self.get_status() in ('RUNNING', 'STARTING'):
            self.stop()
        LOG.warn("removing demo %s" % self.name)
        if isdir(self.path):
            subprocess.call(['chmod', '-R', '777', self.path])
            shutil.rmtree(self.path)

        userpath = dirname(self.path)
        if not os.listdir(userpath):
            os.rmdir(userpath)


    def garbage_collect_apache_confs(self):
        """delete apache config hard links if there is no associated demo
        (ie. a hard link ref count of 1)
        """
        apache_conf_dir = join(PATHS['var'], 'apache2', 'demos')
        for apache_conf_name in os.listdir(apache_conf_dir):
            if not apache_conf_name.endswith('.conf'): continue
            apache_conf_path = join(apache_conf_dir, apache_conf_name)
            if os.stat(apache_conf_path).st_nlink == 1:
                os.remove(apache_conf_path)

def get_available_ip():
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


class UnknownDemo(Exception):
    pass


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
    userpath = join(PATHS['demos'], user)
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
    app_conf.set('params', 'type', app_type.encode('utf-8'))
    app_conf.set('params', 'status', 'DEPLOYING')
    for param_name, param_value in params.items():
        assert(param_name not in ('port', 'status'))
        app_conf.set('params', param_name, unicode(param_value).encode('utf-8'))
    app_conf_path = join(demopath, 'demo.conf')
    with open(app_conf_path, 'w+') as configfile:
        app_conf.write(configfile)
    LOG.info('section %s added', app_name)

    # check whether we already have a template available
    template_name = app_type + '_' + '_' + b64encode(
      ','.join(['%s=%s' % (n.strip(), '\n'.join([i.strip() for i in str(v).split('\n')]))
                for (n, v) in sorted(params.items())
                if n not in ('name','login','user','password','admin_passwd')]))
    template_path = join(PATHS['templates'], template_name)

    if os.path.exists(template_path):
        for item in os.listdir(template_path):
            # XXX replace this waste of space with a btrfs subvolume
            subprocess.call(['cp', '-r', join(template_path, item), demopath])
        # run the demo reconfiguration script
        old_demo = InstalledDemo(user, app_name)
        old_user = old_demo.democonf.get('params', 'user')
        functions = join(PATHS['scripts'], 'functions.sh')
        retcode = subprocess.call(['bash', '-c', 'source "%s" && source "%s" && export -f reconfigure_demo && bash -xce "reconfigure_demo \"%s\" %s \"%s\""' % (functions, script, old_demo.name, old_demo.port, old_user)], cwd=demopath, env=env)
        if retcode != 0:
            shutil.rmtree(demopath)
            raise DeploymentError('installation ended with an error')

    else:
        # run the deployment script
        LOG.debug(script)
        functions = join(PATHS['scripts'], 'functions.sh')
        retcode = subprocess.call(['bash', '-c', 'source "%s" && source "%s" && export -f create_template && bash -xce create_template' % (functions, script)], cwd=demopath, env=env)
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

    # write the demo config file
    app_conf = SafeConfigParser()
    app_conf.read(app_conf_path)
    app_conf.set('params', 'name', app_name.encode('utf-8'))
    app_conf.set('params', 'port', str(port))
    app_conf.set('params', 'user', user.encode('utf-8'))
    app_conf.remove_option('params', 'status')
    with open(app_conf_path, 'w+') as configfile:
        app_conf.write(configfile)

    LOG.info('Finished deploying %s', app_name)

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

