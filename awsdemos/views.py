#!/usr/bin/env python
# coding: utf-8
from ConfigParser import SafeConfigParser, NoSectionError
from os.path import join, isfile, isdir
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.testing import DummyRequest
from repoze.bfg.url import route_url
from shutil import rmtree
from utils import PATHS, APPS_CONF
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


def admin(view):
    """ decorator used to limit views to logged user (admin).
    """
    def decorated(request):
        if authenticated_userid(request):
            return view(request)
        else:
            return render_template_to_response(
                'templates/login.pt',
                request=request,
                message="veuillez vous identifier pour accéder à cette page"
                )
    return decorated


def view_app_list(request, message=None):
    """ return the main page, with applications list, and actions.
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
    """ return the params of a given demo, in a json list.
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
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        if ldaplogin(login, password):
            headers = remember(request, login)
            return HTTPFound(location = came_from,
                             headers = headers)
        message = 'Failed login'

    return dict(
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        )


def logout(request):
    """ Logout of the application.
    """
    headers = forget(request)
    return HTTPFound(location = route_url('view_wiki', request),
                     headers = headers)


def app_form(request):
    """ return the form to create a demo
    """
    master = get_template('templates/master.pt')
    app_list = utils.load_app_list()
    if 'app' in request.params and request.params['app'] in app_list:
        return render_template_to_response(
            "templates/new_app.pt",
            request=request,
            paramlist=app_list[request.params['app']],
            logged_in=authenticated_userid(request),
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
        command = join(PATHS['scripts'], "demo_"+request.params['app']+".sh")
        params = tuple([
            "'"+request.params[x]+"'" for x in app_list[request.params['app']][0]
            ])
        env = os.environ.copy()
        env.update(request.params)
        name = request.params['NAME']
        try:
            port = APPS_CONF.get(name, 'port')
        except NoSectionError:
            port = utils.next_port()
        else:
            log.warn('demo %s already exist. reusing port' % name)
            utils.daemon(name, 'stop')
            port = utils.next_port()
        env['PORT'] = str(port)
        env['BIN'] = PATHS['bin']
        env['SCRIPTS'] = PATHS['scripts']
        env['DEMOS'] = PATHS['demos']
        log.debug(command+' '+' '.join(params))
        subprocess.call(
            command+' '+' '.join(params).encode('utf-8'),
            shell=True,
            env=env
            )

        path = join(
                PATHS['demos'],
                name,
                )
        kwargs = dict(path=path, name=name)

        conf = SafeConfigParser()
        conf.read(PATHS['supervisor'])

        if isfile(join(path, 'starter.sh')):
            section = 'program:%s' % name
            conf.add_section(section)
            conf.set(section, 'command', join(path, 'starter.sh') % kwargs)
            conf.set(section, 'process_name', name)
            conf.set(section, 'directory', path)
            conf.set(section, 'priority', '10')
            conf.set(section, 'redirect_stderr', 'false')
            conf.set(section, 'comment', request.params.get('COMMENT', '-'))
            conf.set(section, 'port', port)
            conf.set(section, 'stdout_logfile', join(path, 'std_out.log'))
            conf.set(section, 'stderr_logfile', join(path, 'std_err.log'))
            conf.set(section, 'stdout_logfile_maxbytes', '1MB')
            conf.set(section, 'stderr_logfile_maxbytes', '1MB')
            conf.set(section, 'stdout_capture_maxbytes', '1MB')
            conf.set(section, 'stderr_capture_maxbytes', '1MB')
            conf.set(section, 'stderr_logfile_backups', '10')
            conf.set(section, 'stderr_logfile_backups', '10')

            with open(PATHS['supervisor'],'w') as configfile:
                conf.write(configfile)
        APPS_CONF.add_section(name)
        APPS_CONF.set(name, 'port', str(port))
        APPS_CONF.set(name, 'path', path)
        APPS_CONF.set(name, 'type', request.params['app'])
        APPS_CONF.set(name, 'daemon', 'supervisor')
        if isfile(join(path, 'daemon.sh')):
            APPS_CONF.set(name, 'daemon', join(path, 'daemon.sh'))
        else:
            #TODO: php?
            pass

        with open(PATHS['apps'], 'w+') as configfile:
            APPS_CONF.write(configfile)

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
    if APPS_CONF.get(name, 'port'):
        utils.daemon(name, command.lower())
        return view_app_list(
            request, message='demo %s successfully %sed' % (name, command.lower())
            )
    raise NotFound


def delete_demo(request):
    """ If an application of the name NAME is deployed, we delete it
    """
    name=request.params['NAME']

    utils.daemon(name, 'stop')

    log.warn("removing demo "+name)

    APPS_CONF.remove_section(name)
    with open(PATHS['apps'], 'w') as configfile:
        APPS_CONF.write(configfile)

    conf = SafeConfigParser()
    conf.read(PATHS['supervisor'])
    conf.remove_section('program:'+name)
    with open(PATHS['supervisor'], 'w') as configfile:
        conf.write(configfile)

    if isdir(join(PATHS['demos'], name)):
        rmtree(join(PATHS['demos'], name))
    else:
        log.error("demo "+name+"'s directory not found in demos.")

    return view_app_list(
        request, message='demo '+name+' successfully removed'
        )

