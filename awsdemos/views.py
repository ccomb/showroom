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
import utils
from repoze.bfg.security import (
    Allow,
    Everyone,
    Authenticated,
    authenticated_userid,
    has_permission,
    )

log = logging.getLogger(__name__)


def app_list(request):
    """
    return the main page, with applications list, and actions.
    """
    master = get_template('templates/master.pt')
    return render_template_to_response(
        "templates/app_list.pt",
        request=request,
        demos=utils.load_app_list(),
        master=master
        )

def demo_form(request):
    """
    return the form to create a demo
    """
    master = get_template('templates/master.pt')
    app_list = utils.load_app_list()
    if 'app' in request.params and request.params['app'] in app_list:
        return render_template_to_response(
            "templates/new_app.pt",
            request=request,
            paramlist=app_list[request.params['app']],
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
    ...                      'COMMENT': 'commentaire'})) #doctest: +ELLIPSIS
    <Response at ... 200 OK>

    """
    if 'app' not in request.params:
        raise NotFound
    app_list = utils.load_app_list()
    if request.params['app'] in app_list:
        command = os.path.join(config.paths.scripts, "demo_"+request.params['app']+".sh")
        params = tuple([
            "'"+request.params[x]+"'" for x in app_list[request.params['app']]
            ])
        env = os.environ.copy()
        env.update(request.params)
        name = request.params['NAME']
        port = utils.next_port()
        env['PORT'] = str(port)
        env['DEMOS'] = config.paths.demos
        log.debug(command+' '+' '.join(params))
        conf = ConfigObject()
        conf.read(config.paths.supervisor)
        process = subprocess.Popen(command+' '+' '.join(params), shell=True,
        stdout=subprocess.PIPE, env=env)
        stdout, stderr = process.communicate()

        section = 'program:%s' % name
        path = os.path.join(
                config.paths.demos,
                name,
                )
        kwargs = dict(path=path, name=name)

        if os.path.isfile(os.path.join(path, 'starter.sh')):
            conf[section] = {
                'command': os.path.join(path, 'starter.sh') % kwargs,
                'process_name': name,
                'directory': path,
                'priority': '10',
                'redirect_stderr': 'false',
                'comment': request.params.get('COMMENT', '-'),
                'port': port,
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

        conf.write(open(config.paths.supervisor,'w'))

        apps = utils.get_apps()
        apps[name] = dict(port=port, path=path,
                          type=request.params['app'])
        apps.write(open(config.paths.apps, 'w+'))

        log.info('section %s added', name)

        return view_demos_list(
            request,
            message="application %s created at port %s" % (name, port)
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

    apps = utils.get_apps()
    demos = []
    for name in apps.sections():
        app = apps[name]
        demos.append(dict(
            name=name,
            comment=app.comment,
            port=app.port,
            autostart= conf['program:%s' % name].autostart.as_bool('false'),
        ))
    return demos

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
    apps = utils.get_apps()

    del apps[name]
    apps.write(open(config.paths.apps, 'w'))

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

