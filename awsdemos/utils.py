# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
from os.path import isdir, isfile, join, abspath
import logging
import os
import subprocess
import sys

log = logging.getLogger(__name__)

config = SafeConfigParser()
PATH = os.path.dirname(abspath(sys.argv[-1]))
config.read(join(PATH, 'aws.demos.ini'))
PATHS = {
  'bin' : join(PATH, config.get('paths', 'bin')),
  'scripts' : join(PATH, config.get('paths', 'scripts')),
  'demos' : join(PATH, config.get('paths', 'demos')),
  'port' : join(PATH, config.get('paths', 'port')),
  'apps' : join(PATH, config.get('paths', 'apps')),
  'supervisor' : join(PATH, config.get('paths', 'supervisor')),
}

if not isdir(PATHS['demos']):
    os.makedirs(PATHS['demos'])
    log.info('%s created.', PATHS['demos'])

APPS_CONF = SafeConfigParser()
APPS_CONF.read(PATHS['apps'])


def daemon(name, command='restart'):
    daemon = APPS_CONF.get(name, 'daemon')
    if daemon == 'supervisor':
        cmd = [join(PATHS['bin'], 'supervisorctl'), command, name]
    elif daemon:
        cmd = [daemon, command]
    else:
        cmd = None
    if cmd:
        log.warn('%sing %s: %s', command, name, ' '.join(cmd))
        p = subprocess.Popen(cmd)
        ret = p.wait()
        try:
            p.terminate()
        except OSError:
            pass
        return ret
    else:
        log.error('no such demo %s', name)
        return -1


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
        for line in open('scripts'+os.sep+file):
            if line.split(':')[0] == '# PARAMS':
                params = line.split('\n')[0].split(':')[1].split(',')
                break
        demos[(file[5:-3])] = params
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
    load the list of existing applications. with a boolean indicating if they
    are activated in supervisor conf.
    """
    conf = SafeConfigParser()
    conf.read(PATHS['supervisor'])

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

