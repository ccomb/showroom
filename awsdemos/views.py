# coding: utf-8
from ConfigParser import SafeConfigParser, NoSectionError
from awsdemos.security import ldaplogin
from os.path import join
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.url import route_url
from shutil import rmtree
from utils import PATHS, APPS_CONF, XMLRPC, ADMIN_HOST
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


def _reload_apache(demo):
    """reload apache config, or shutdown if it is not needed anymore
    """
    apache_confs = [conf
                    for conf in os.listdir(join(PATHS['var'], 'apache2', 'demos'))
                    if conf.endswith('.conf')]
    a2status = XMLRPC.supervisor.getProcessInfo('apache2')['statename']

    if len(apache_confs) == 0:
        if a2status == 'RUNNING':
            XMLRPC.supervisor.stopProcess('apache2')
    else:
        # reload the config or start Apache if needed (WITH supervisor!)
        a2status = XMLRPC.supervisor.getProcessInfo('apache2')['statename']
        if a2status == 'RUNNING':
            retcode = subprocess.call(
                ["apache2ctl",  "-f", "etc/apache2/apache2.conf", "-k", "graceful"])
            # if the graceful command fails, we should disable the new config
            # BUT we should let supervisor restart the app!!
            if retcode != 0:
                _a2dissite(demo)
        else:
            XMLRPC.supervisor.startProcess('apache2')





def _a2ensite(demo):
    """sandbox equivalent to the a2ensite command
    """
    config_file = join(PATHS['demos'], demo, 'apache2.conf')
    config_link = join(PATHS['var'], 'apache2', 'demos', demo + '.conf')
    config_dir = join(PATHS['var'], 'apache2', 'demos')
    if os.path.exists(config_file) and not os.path.exists(config_link):
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)
        os.link(config_file, config_link)


def _a2dissite(demo):
    """sandbox equivalent to the a2dissite command
    """
    config_link = join(PATHS['var'], 'apache2', 'demos', demo + '.conf')
    if os.path.exists(config_link):
        os.remove(config_link)


def action(request):
    """
    Execute the action bound to the name passed and return when the action is
    finished.
    FIXME: should verify if the user has access to the command.

    If we don't specify an app, or we specify a non existing app, we get a 404:
    """
    params = request.params.copy()
    if 'app' not in params or 'NAME' not in params:
        raise NotFound
    params['NAME'] = params['NAME'].replace(' ', '_').lower() # FIXME
    app_list = utils.available_demos()
    if params['app'] in app_list:
        # rebuild the name of the deployment script
        script = join(PATHS['scripts'], "demo_"+params['app']+".sh")

        # *check the script* #FIXME move in a function

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
        env['HOST'] = ADMIN_HOST

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
        subprocess.call('"'+script+'"', shell=True, cwd=demopath, env=env)

        # set the start script to executable
        start_script = join(demopath, 'start.sh')
        if os.path.exists(start_script):
            os.chmod(start_script, 0744)
            # add the shebang if forgotten
            with open(start_script, 'r+') as s:
                content = s.read()
                if not content.startswith('#!'):
                    content = '#!/bin/bash\n' + content
                    s.seek(0); s.write(content)

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

            # reload the config
            XMLRPC.supervisor.reloadConfig()
            XMLRPC.supervisor.addProcessGroup(app_name)

        # add our new application in the apps config file
        # TODO: move that in the demo directory
        APPS_CONF.add_section(app_name)
        APPS_CONF.set(app_name, 'port', str(port))
        APPS_CONF.set(app_name, 'path', demopath)
        APPS_CONF.set(app_name, 'type', params['app'])
        with open(PATHS['apps'], 'w+') as configfile:
            APPS_CONF.write(configfile)
        LOG.info('section %s added', app_name)

        _flash_message(request,
            u"application %s created at port %s" % (app_name, port))
        return HTTPFound(location='/')
    else:
        raise NotFound


def daemon(request):
    """ view that starts, stops or restarts the demo
    TODO : move the startup and stop in a function
    """
    name = request.params.get('NAME', '_')
    command = request.params.get('COMMAND', 'restart').lower()
    start_script = join(PATHS['demos'], name, 'start.sh')
    apache_config_link = join(PATHS['var'], 'apache2', 'demos', name + '.conf')
    apache_config_file = join(PATHS['demos'], name, 'apache2.conf')

    # get the state
    has_startup_script = os.path.exists(start_script)
    has_apache_conf = os.path.exists(apache_config_file)
    has_apache_link = os.path.exists(apache_config_link)
    state = 'STOPPED'
    if has_apache_link:
        state = 'RUNNING'
    if has_startup_script:
        state = XMLRPC.supervisor.getProcessInfo(name)['statename']
    message = u'Nothing changed'

    # stop if asked
    if state == 'RUNNING' and command in ('stop', 'restart'):
        if has_startup_script:
            XMLRPC.supervisor.stopProcess(name)
        if has_apache_link:
            _a2dissite(name)
            _reload_apache(name)
        message = u'%s stopped!' % (name)

    # get the state again
    has_startup_script = os.path.exists(start_script)
    has_apache_conf = os.path.exists(apache_config_file)
    has_apache_link = os.path.exists(apache_config_link)
    state = 'STOPPED'
    if has_apache_link:
        state = 'RUNNING'
    if has_startup_script:
        state = XMLRPC.supervisor.getProcessInfo(name)['statename']

    # start if asked
    if state == 'STOPPED' and command in ('start', 'restart'):
        if has_startup_script:
            XMLRPC.supervisor.startProcess(name)
        if has_apache_conf:
            _a2ensite(name)
            _reload_apache(name)
        message = u'%s started!' % (name)

    _flash_message(request, message)
    return HTTPFound(location='/')


def delete_demo(request):
    """ If an application of the name NAME is deployed, we delete it
    """
    name=request.params['NAME']

    start_script = join(PATHS['demos'], name, 'start.sh')
    if os.path.exists(start_script):
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

    if os.path.isdir(join(PATHS['demos'], name)):
        rmtree(join(PATHS['demos'], name))
    else:
        LOG.error("directory not found for %s in demos." % name)

    _a2dissite(name)
    _reload_apache(name)

    _flash_message(request, '%s deleted!' % name)
    return HTTPFound(location='/')

