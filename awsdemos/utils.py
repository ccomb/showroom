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
        conf = SafeConfigParser()
        conf.read(join(PATHS['demos'], name, 'demo.conf'))
        port=conf.get(name, 'port')
        state = 'STOPPED'
        if 'supervisor.cfg' in os.listdir(join(PATHS['demos'], name)):
            try:
                state = XMLRPC.supervisor.getProcessInfo(name)['statename']
            except:
                state = 'STOPPED'
        if 'apache2.conf' in os.listdir(join(PATHS['demos'], name)):
            if name + '.conf' in os.listdir(join(PATHS['var'], 'apache2', 'demos')):
                state = 'RUNNING'

        demo_infos.append(dict(
            name=name,
            port=port,
            state = state,
            comment=get_demo_comment(name)
        ))
    return demo_infos


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


def destroy(name):
    if name not in [d['name'] for d in installed_demos()]:
        raise DestructionError('this demo does not exist')
    start_script = join(PATHS['demos'], name, 'start.sh')
    if os.path.exists(start_script):
        try:
            state = XMLRPC.supervisor.getProcessInfo(name)['statename']
        except:
            state = 'STOPPED'
        if state == 'RUNNING':
            XMLRPC.supervisor.stopProcess(name)
        XMLRPC.supervisor.removeProcessGroup(name)

    LOG.warn("removing demo %s" % name)

    demopath = join(PATHS['demos'], name)
    if os.path.isdir(demopath):
        shutil.rmtree(demopath)


