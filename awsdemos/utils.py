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
        cmd = [os.path.join(config.paths.bin, 'supervisorctl'), command, name]
    elif app.daemon:
        cmd = [app.daemon, command]
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
    if 'about.txt' in os.listdir(os.path.join(config.paths.demos, demo_name)):
        return open(
            os.path.join(config.paths.demos, demo_name, 'about.txt')
            ).read()
    else:
        return ''

def demos_list():
    """
    load the list of existing applications. with a boolean indicating if they
    are activated in supervisor conf.

    """
    conf = ConfigObject()
    conf.read(config.paths.supervisor)

    apps = get_apps()
    demos = []
    for name in apps.sections():
        app = apps[name]
        demos.append(dict(
            name=name,
            port=app.port,
            autostart= conf['program:%s' % name].autostart.as_bool('false'),
            comment=get_demo_comment(name)
        ))
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

