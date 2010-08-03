# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
from os.path import isdir, isfile, join, abspath
import logging
import os
import subprocess
import sys

LOG = logging.getLogger(__name__)

CONFIG = SafeConfigParser()
PATH = os.path.dirname(abspath(sys.argv[-1]))

CONFIG.read(join(PATH, 'aws.demos.ini'))
PATHS = {
  'bin' : join(PATH, CONFIG.get('paths', 'bin')),
  'scripts' : join(PATH, CONFIG.get('paths', 'scripts')),
  'demos' : join(PATH, CONFIG.get('paths', 'demos')),
  'port' : join(PATH, CONFIG.get('paths', 'port')),
  'apps' : join(PATH, CONFIG.get('paths', 'apps')),
}

if not isdir(PATHS['demos']):
    os.makedirs(PATHS['demos'])
    LOG.info('%s created.', PATHS['demos'])

# FIXME global variable
APPS_CONF = SafeConfigParser()
APPS_CONF.read(PATHS['apps'])


def daemon(name, command='restart'):
    """function that start, stop or restart the demo.
    We read the command in the apps config file
    """
    if (not APPS_CONF.has_section(name)
        or not APPS_CONF.has_option(name, command)):
        print 'command %s not found for %s' % (command, name)
        return

    demopath = APPS_CONF.get(name, 'path')

    # if we don't have a stop command, kill the app
    if (command == 'stop'
      and APPS_CONF.get(name, command).strip() == ''
      and os.path.exists(join(demopath, 'pid'))):
        cmd = "kill %s" % open(join(demopath, 'pid')).read()
    else:
        cmd = join(demopath, APPS_CONF.get(name, command))


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


def load_app_list():
    """
    return a dict containing all apps and their respective commands defined in
    config file.

    >>> load_app_list()['repoze.bfg']
    ['NAME', 'COMMENT']
    """
    demos = {}
    for file in (
            i for i in os.listdir('scripts')
            if i.startswith('demo_') and i.endswith('.sh')
            ):
        params = []
        plugins = []
        for line in open('scripts'+os.sep+file):
            if line.split(':')[0] == '# PARAMS':
                params = line.split('\n')[0].split(':')[1].split(',')
            elif line.split(':')[0] == '# PLUGINS':
                plugins = line.split('\n')[0].split(':')[1].split(',')

        demos[(file[5:-3])] = (params, plugins)
    return demos


def get_demo_comment(demo_name):
    """
    return the content of "about.txt" in the directory of the application, if
    it exists.

    """
    if 'about.txt' in os.listdir(join(PATHS['demos'], demo_name)):
        return open(
            join(PATHS['demos'], demo_name, 'about.txt')
            ).read()
    else:
        return ''


def demos_list():
    """
    load the list of existing applications.
    """
    demos = []
    for name in APPS_CONF.sections():
        demos.append(dict(
            name=name,
            port=APPS_CONF.get(name, 'port'),
            autostart=APPS_CONF.has_option(name, 'autostart') and APPS_CONF.getboolean(name, 'autostart'),
            comment=get_demo_comment(name)
        ))
    return demos


def next_port():
    """
    store the last used port in a file and return the next one
    FIXME : do the same without storing a file

    >>> port = next_port()
    >>> next_port() == port +1
    True
    """
    path = PATHS['port']
    if isfile(path):
        port = int(open(path).read())
        port += 1
    else:
        port = 9000
    fd = open(path, 'wb')
    fd.write(str(port))
    fd.close()
    return port

