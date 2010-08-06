# coding: utf-8
from ConfigParser import SafeConfigParser, NoSectionError
from awsdemos.security import ldaplogin
from os.path import join, isfile, isdir
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.testing import DummyRequest
from repoze.bfg.url import route_url
from shutil import rmtree
from utils import PATHS, APPS_CONF, XMLRPC
from webob.exc import HTTPFound
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

LOG = logging.getLogger(__name__)



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
                message="Veuillez vous identifier pour accéder à cette page"
                )
    return decorated


def _flash_message(request, message):
    """send a message through the session to the next url
    """
    request.environ['beaker.session']['message'] = message
    request.environ['beaker.session'].save()

def view_app_list(request):
    """ return the main page, with applications list, and actions.
    """
    logged_in = authenticated_userid(request)
    master = get_template('templates/master.pt')
    return render_template_to_response(
        "templates/master.pt",
        request=request,
        apps=utils.available_demos(),
        demos=utils.installed_demos(request),
        logged_in=authenticated_userid(request),
        )

def json_app_list(request):
    """return a json view of all apps and their params/plugins
    """
    return utils.available_demos()


def json_installed_demos(request):
    """ return a json view of all installed apps and their statuses
    """
    return utils.installed_demos()

def app_params(request):
    """ return the params of a given demo, in a json list.
    """
    app_list = utils.available_demos()
    if 'app' in request.params and request.params['app'] in app_list:
        return utils.available_demos()[request.params['app']][0]
    else:
        return ("No application name given or unknown application.",)

def app_plugins(request):
    """
    return the plugins of a given demo, in a json list.

    """
    app_list = utils.available_demos()
    if 'app' in request.params and request.params['app'] in app_list:
        return utils.available_demos()[request.params['app']][1]
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
    FIXME: seems not used
    """
    master = get_template('templates/master.pt')
    app_list = utils.available_demos()
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
    params = request.params.copy()
    params['NAME'] = params['NAME'].replace(' ', '_') # FIXME
    if 'app' not in params:
        raise NotFound
    app_list = utils.available_demos()
    if params['app'] in app_list:
        # rebuild the name of the deployment script
        script = join(PATHS['scripts'], "demo_"+params['app']+".sh")

        # *check the script* #FIXME move in a function
        # our script should contain the command to start the demo
        start_command = None
        for line in open(script).readlines():
            if line.strip().startswith('#') and 'START' in line:
                start_command = line.split(':', 1)[1].strip()
                break
        if start_command is None:
            message = u'The deployment script lacks a START command!'
            _flash_message(request, message)
            return HTTPFound(location='/')

        # add environment variables for the deployment script
        env = os.environ.copy()
        env.update(params)
        app_name = params['NAME']
        try:
            port = APPS_CONF.get(app_name, 'port')
        except NoSectionError:
            port = utils.next_port()
        else:
            LOG.warn('demo %s already exist. reusing port' % app_name)
            XMLRPC.supervisor.stopProcess(app_name)
            port = utils.next_port()
        env['PORT'] = str(port)
        # put the virtualenv path first
        env['PATH'] = os.path.abspath('bin') + ':' + env['PATH']

        # create the directory for the demo
        demopath = join(PATHS['demos'], app_name)
        if not os.path.exists(demopath):
            os.mkdir(demopath)
        else:
            message = u"this app already exists"
            _flash_message(request, message)
            return HTTPFound(location='/')

        # run the deployment script
        LOG.debug(script)
        subprocess.call(script, shell=True, cwd=demopath, env=env)

        # add our new application in the apps config file
        APPS_CONF.add_section(app_name)
        APPS_CONF.set(app_name, 'start', start_command)
        APPS_CONF.set(app_name, 'port', str(port))
        APPS_CONF.set(app_name, 'path', demopath)
        APPS_CONF.set(app_name, 'type', params['app'])

        with open(PATHS['apps'], 'w+') as configfile:
            APPS_CONF.write(configfile)

        LOG.info('section %s added', app_name)

        # add a supervisor include file for this program
        supervisor_conf = SafeConfigParser()
        section = 'program:%s' % app_name
        supervisor_conf.add_section(section)
        supervisor_conf.set(section, 'command', join(demopath, APPS_CONF.get(app_name, 'start')))
        supervisor_conf.set(section, 'directory', demopath)
        with open(join(demopath, 'supervisor.cfg'), 'w') as supervisor_file:
            supervisor_conf.write(supervisor_file)


        # reload the config and start the process
        XMLRPC.supervisor.reloadConfig()
        XMLRPC.supervisor.addProcessGroup(app_name)

        _flash_message(request,
            u"application %s created at port %s" % (app_name, port))
        return HTTPFound(location='/')
    else:
        raise NotFound


def daemon(request):
    """ view that starts, stops or restarts the demo
    """
    name = request.params.get('NAME', '_')
    command = request.params.get('COMMAND', 'restart').lower()
    state = XMLRPC.supervisor.getProcessInfo(name)['statename']
    message = u'Nothing changed'

    if state == 'RUNNING' and command in ('stop', 'restart'):
        XMLRPC.supervisor.stopProcess(name)
        message = u'%s stopped!' % (name)

    state = XMLRPC.supervisor.getProcessInfo(name)['statename']

    if state == 'STOPPED' and command in ('start', 'restart'):
        XMLRPC.supervisor.startProcess(name)
        message = u'%s started!' % (name)

    _flash_message(request, message)
    return HTTPFound(location='/')


def delete_demo(request):
    """ If an application of the name NAME is deployed, we delete it
    """
    name=request.params['NAME']

    state = XMLRPC.supervisor.getProcessInfo(name)['statename']
    if state == 'RUNNING':
        XMLRPC.supervisor.stopProcess(name)
        XMLRPC.supervisor.removeProcessGroup(name)

    LOG.warn("removing demo "+name)

    APPS_CONF.remove_section(name)
    with open(PATHS['apps'], 'w') as configfile:
        APPS_CONF.write(configfile)

    conf = SafeConfigParser()
    conf.remove_section('program:'+name)

    if isdir(join(PATHS['demos'], name)):
        rmtree(join(PATHS['demos'], name))
    else:
        LOG.error("directory not found for %s in demos." % name)

    _flash_message(request, '%s deleted!' % name)
    return HTTPFound(location='/')

