# -*- coding: utf-8 -*-
import os
import sys
import logging
import subprocess
from awsdemos import config
from ConfigObject import ConfigObject

log = logging.getLogger(__name__)

if not os.path.isdir(config.paths.demos):
    os.makedirs(config.paths.demos)
    log.info('%s created.', config.paths.demos)

def get_apps():
    conf = ConfigObject()
    conf.read(config.paths.apps)
    return conf

def get_app(name):
    return get_apps()[name]

def daemon(name, command='restart'):
    app = get_app(name)
    if app.daemon == 'supervisor':
        cmd = '%s %s %s' % (os.path.join(config.paths.bin, 'supervisorctl'), command, name)
    elif app.daemon:
        cmd = '%s %s' % (app.daemon, command)
    log.warn('%sing %s: %s', command, name, cmd)
    subprocess.call(cmd, shell=True)

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
        demos[(file[5:-3])] = params
    return demos

def next_port():
    """
    >>> port = next_port()
    >>> next_port() == port +1
    True
    """
    path = config.paths.port
    if os.path.isfile(path):
        port = int(open(path).read())
        port += 1
    else:
        port = 9000
    fd = open(path, 'wb')
    fd.write(str(port))
    fd.close()
    return port

