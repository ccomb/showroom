from ConfigParser import ConfigParser
from ConfigObject import ConfigObject
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.testing import DummyRequest
from awsdemos import config
import logging
import subprocess
import os
from shutil import rmtree
import time
import webob
from repoze.bfg.security import (
    Allow,
    Everyone,
    Authenticated,
    authenticated_userid,
    has_permission,
    )

log = logging.getLogger(__name__)

if not os.path.isdir(config.paths.demos):
    os.makedirs(config.paths.demos)
    log.info('%s created.', config.paths.demos)

def load_app_list():
    """
    return a dict containing all apps and their respective commands defined in
    config file.

    >>> load_app_list()
    {'repoze.bfg': ['NAME', 'COMMENT']}
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


def app_list(request):
    """
    return the main page, with applications list, and actions.
    """
    master = get_template('templates/master.pt')
    return render_template_to_response(
        "templates/app_list.pt",
        request=request,
        demos=load_app_list(),
        master=master
        )

def demo_form(request):
    """
    return the form to create a demo
    """
    master = get_template('templates/master.pt')
    if 'app' in request.params and request.params['app'] in load_app_list():
        return render_template_to_response(
            "templates/new_app.pt",
            request=request,
            paramlist=load_app_list()[request.params['app']],
            demo=request.params['app'],
            master=master
        )
    else:
        return webob.Response(str(
            "No application name given or unknown application."
            ))


def action(request):
    """
    Execute the action bound to the name passed and return when the action is
    finished.
    FIXME: should verify if the user has access to the command.

    If we don't specify an app, or we specify a non existing app, we get a 404:

    >>> action(DummyRequest())
    Traceback (most recent call last):
    ...
    NotFound
    >>> action(DummyRequest({'app':'toto'}))
    Traceback (most recent call last):
    ...
    NotFound

    >>> action(DummyRequest({'app':'repoze.bfg',
    ...                      'NAME':'foobar',
    ...                      'COMMENT': 'commentaire'}))
    <Response at ... 200 OK>

    """
    if 'app' not in request.params:
        raise NotFound
    if request.params['app'] in load_app_list():
        command = "scripts/demo_"+request.params['app']+".sh"
        params = tuple([
            "'"+request.params[x]+"'" for x in load_app_list()[request.params['app']]
            ])
        env = os.environ.copy()
        env['DEMOS'] = config.paths.demos
        env['NAME'] = request.params['NAME']
        env['COMMENT'] = request.params['COMMENT']
        log.debug(command+' '+' '.join(params))
        conf = ConfigObject()
        conf.read(config.paths.supervisor)
        process = subprocess.Popen(command+' '+' '.join(params), shell=True,
        stdout=subprocess.PIPE, env=env)
        stdout, stderr = process.communicate()

        section = 'program:%s' % env['NAME']
        path = os.path.join(
                config.paths.demos,
                env['NAME'],
                )
        kwargs = dict(path=path, name=env['NAME'])

        if os.path.isfile(os.path.join(path, 'starter.sh')):
            conf[section] = {
                'command': os.path.join(path, 'starter.sh') % kwargs,
                'process_name': name,
                'directory': path,
                'priority': '10',
                'redirect_stderr': 'false',
                'comment': request.params['COMMENT'],
                'port': stdout.split('\n')[-2].split(':')[-1][:-1],
                'stdout_logfile': os.path.join(path, 'std_out.log'),
                'stderr_logfile': os.path.join(path, 'std_err.log'),
                'stdout_logfile_maxbytes': '1MB',
                'stderr_logfile_maxbytes': '1MB',
                'stdout_capture_maxbytes': '1MB',
                'stderr_capture_maxbytes': '1MB',
                'stderr_logfile_backups': '10',
                'stderr_logfile_backups': '10',
            }
        else:
            #TODO: php?
            pass

        log.info('section %s added', env['NAME'])

        conf.write(open(config.paths.supervisor,'w'))
        return view_demos_list(
            request,
            message="application "+env['NAME']+" created: "+stdout.split('\n')[-2]
            )
    else:
        raise NotFound


def demos_list():
    """
    load the list of existing applications. with a boolean indicating if they
    are activated in supervisor conf.

    """
    conf = ConfigObject()
    conf.read(config.paths.supervisor)
    return [
        (
            d,
            conf['program:%s' % d].autostart.as_bool('false'),
            conf['program:'+d].port,
            conf['program:'+d].comment
        )
        for d in os.listdir(config.paths.demos) if not os.path.isfile(os.path.join(config.paths.demos, d))
        ]

def view_demos_list(request, message=None):
    master = get_template('templates/master.pt')
    return render_template_to_response(
            'templates/demos_list.pt',
            request=request,
            message=message,
            demos=demos_list(),
            master=master
            )

def delete_demo(request):
    """
    If an application of the name NAME is deployed, we delete it

    """
    name=request.params['NAME']

    log.warn("removing demo "+name)
    conf = ConfigParser()
    conf.read(config.paths.supervisor)
    if not conf.remove_section('program:'+name):
        log.debug("remove of "+name+"abborted, demo not found in conf")
        raise ValueError(
            "application "+name+" doesn't exists in configuration"
        )
    conf.write(open(config.paths.supervisor,'w'))

    if os.path.isdir(os.path.join(config.paths.demos, name)):
        rmtree(os.path.join(config.paths.demos, name))
    else:
        log.error("demo "+name+"'s directory not found in demos.")

    return view_demos_list(
        request, message='demo '+name+' successfully removed'
        )

