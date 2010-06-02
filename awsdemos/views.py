#!/usr/bin/env python
# -ø- coding:utf-8 -ø-
from ConfigObject import ConfigObject
from ConfigParser import ConfigParser
from awsdemos import config
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.testing import DummyRequest
from repoze.bfg.url import route_url
from shutil import rmtree
from webob.exc import HTTPFound
from awsdemos.security import ldaplogin
import logging
import os
import subprocess
import time
import utils
import webob
from repoze.bfg.security import (
    Allow,
    Everyone,
    Authenticated,
    authenticated_userid,
    has_permission,
    forget,
    remember,
    )

log = logging.getLogger(__name__)

def view_app_list(request, message=None):
    """
    return the main page, with applications list, and actions.
    """
    logged_in = authenticated_userid(request)
    master = get_template('templates/master.pt')
    return render_template_to_response(
        "templates/master.pt",
        request=request,
        message=message,
        apps=utils.load_app_list(),
        demos=utils.demos_list(),
        logged_in=authenticated_userid(request),
        )

def json_app_list(request):
    """
    return a json view of all apps and their params/plugins
    """
    return utils.load_app_list()

def app_params(request):
    """
    return the params of a given demo, in a json list.

    """
    app_list = utils.load_app_list()
    if 'app' in request.params and request.params['app'] in app_list:
        return utils.load_app_list()[request.params['app']][0]
    else:
        return ("No application name given or unknown application.",)

def app_plugins(request):
    """
    return the params of a given demo, in a json list.

    """
    app_list = utils.load_app_list()
    if 'app' in request.params and request.params['app'] in app_list:
        return utils.load_app_list()[request.params['app']][1]
    else:
        return ("No application name given or unknown application.",)

def login(request):
    """
    allow to login to the application to do admin tasks.

    """
    login_url = route_url('login', request)
    referrer = request.url
    if referrer == login_url:
        referrer = '/admin' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        if ldaplogin(login, password):
            print 'authenticated'
            headers = remember(request, login)
            return HTTPFound(location = came_from,
                             headers = headers)
        message = 'Failed login'

    print 'not authenticated'
    return dict(
            message = message,
            url = request.application_url + '/login',
            came_from = came_from,
            login = login,
            password = password,
            )

def logout(request):
    """
    Logout of the application.

    """
    headers = forget(request)
    return HTTPFound(location = '/admin', headers=headers)

def app_form(request):
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
            master=master,
            logged_in=authenticated_userid(request),
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
            "'"+request.params[x]+"'" for x in
            app_list[request.params['app']][0]
            ])
        env = os.environ.copy()
        env.update(request.params)
        name = request.params['NAME']
        app = utils.get_app(name)
        if app.port:
            log.warn('demo %s already exist. reusing port' % name)
            try:
                utils.daemon(name, 'stop')
            except:
                pass
            port = app.port
        else:
            port = utils.next_port()
        env['PORT'] = str(port)
        env['BIN'] = config.paths.bin
        env['SCRIPTS'] = config.paths.scripts
        env['DEMOS'] = config.paths.demos
        env['PLUGINS'] = ' '.join(app_list[request.params['app']][1])
        log.debug(command+' '+' '.join(params))
        subprocess.call(
            command+' '+' '.join(params).encode('utf-8'),
            shell=True,
            env=env
            )

        path = os.path.join(
                config.paths.demos,
                name,
                )
        kwargs = dict(path=path, name=name)

        apps = utils.get_apps()
        conf = ConfigObject()
        conf.read(config.paths.supervisor)

        if os.path.isfile(os.path.join(path, 'starter.sh')):
            section = 'program:%s' % name
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
            conf.write(open(config.paths.supervisor,'w'))
            apps[name] = dict(port=port, path=path,
                              type=request.params['app'],
                              daemon='supervisor')
        if os.path.isfile(os.path.join(path, 'daemon.sh')):
            apps[name] = dict(port=port, path=path,
                              type=request.params['app'],
                              daemon=os.path.join(path, 'daemon.sh'))
        else:
            #TODO: php?
            pass


        apps.write(open(config.paths.apps, 'w+'))

        log.info('section %s added', name)

        utils.daemon(name, 'start')

        return view_app_list(
            request,
            message="application %s created at port %s" % (name, port)
            )
    else:
        raise NotFound

def daemon(request):
    name = request.params.get('NAME', '_')
    command = request.params.get('COMMAND', 'restart')
    app = utils.get_app(name)
    if app.port:
        utils.daemon(name, command.lower())
        return view_app_list(
            request, message='demo %s successfully %sed' % (name, command.lower())
            )
    raise NotFound

def delete_demo(request):
    """
    If an application of the name NAME is deployed, we delete it

    """
    name=request.params['NAME']

    utils.daemon(name, 'stop')

    log.warn("removing demo "+name)
    apps = utils.get_apps()

    del apps[name]
    apps.write(open(config.paths.apps, 'w'))

    conf = ConfigObject()
    conf.read(config.paths.supervisor)
    del conf['program:'+name]
    conf.write(open(config.paths.supervisor,'w'))

    if os.path.isdir(os.path.join(config.paths.demos, name)):
        rmtree(os.path.join(config.paths.demos, name))
    else:
        log.error("demo "+name+"'s directory not found in demos.")

    return view_app_list(
        request, message='demo '+name+' successfully removed'
        )

