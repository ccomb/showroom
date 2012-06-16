# coding: utf-8
from os.path import join, abspath, dirname
from pyramid_signup.managers import UserManager
from pyramid.chameleon_zpt import get_template
from pyramid.request import Response
from pyramid.chameleon_zpt import render_template_to_response
from pyramid.exceptions import NotFound
from pyramid.security import authenticated_userid, forget, remember
from pyramid.url import route_url
from pyramid_signup.views import AuthController
from showroom.security import check_login
from urlparse import urlsplit, urlunsplit
from utils import ADMIN_HOST
from utils import keep_working_dir
from webob.exc import HTTPFound
import logging
import os
import subprocess
import utils

LOG = logging.getLogger(__name__)

def _flash_message(request, message, message_type='SUCCESS'):
    """send a message through the session to the next url
    """
    # TODO: remove and replace occurences with self.request.session.flash
    request.environ['beaker.session']['message_type'] = message_type
    request.environ['beaker.session']['message'] = message
    request.environ['beaker.session'].save()


def proxied_url(demo, request):
    """Give the url of the proxied demo
    """
    current_host = urlsplit(request.host_url)
    port = current_host.port
    if port is None:
        host = ADMIN_HOST
    else:
        host = ADMIN_HOST + ':' + str(current_host.port)
    return urlunsplit(
        (current_host.scheme, demo['name'] + '.' + host, '/', '', ''))


def direct_url(demo, request):
    """Give the direct url of the demo
    """
    if demo['port'] is '':
        return "#"
    current_host = urlsplit(request.host_url)
    return urlunsplit(
        (current_host.scheme, ADMIN_HOST + ':' + demo['port'], '/', '', ''))

def installed_demos(request):
    """ return the main page, with applications list, and actions.
    """
    # XXX this view is too slow

    logged_in = authenticated_userid(request)
    if logged_in is not None:
        logged_in = UserManager(request).get_by_pk(logged_in).username

    return render_template_to_response(
        join(abspath(dirname(__file__)), 'templates', 'demos.pt'),
        master=get_template('templates/master.pt'),
        request=request,
        apps=utils.available_demos(),
        proxied_url=proxied_url,
        direct_url=direct_url,
        demos=utils.installed_demos(),
        supervisor=utils.SuperVisor().is_running,
        logged_in=logged_in,
        )


def json_available_demos(request):
    """return a json view of all apps and their params/plugins
    """
    return utils.available_demos()


def json_installed_demos(request):
    """ return a json view of all installed apps and their statuses
    """
    return utils.installed_demos()


def OLDlogin(request): #XXX remove
    """ authenticate to do admin tasks.
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
        if check_login(login, password):
            headers = remember(request, login)
            return HTTPFound(location = came_from,
                             headers = headers)
        message = 'Failed login'
        _flash_message(request,
            u"%s" % message, 'ERROR')

    return dict(
        master=get_template('templates/master.pt'),
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        )


def forbidden(request):
    """View for the 401 Error: use the login
    """
    if not authenticated_userid(request):
        res = AuthController(request).login()
        if type(res) == dict:
            res.update(dict(
                master=get_template('templates/master.pt'),
                url = request.application_url + '/login',
            ))
        return res
    return Response('forbidden')


def deploy(request):
    """ deploy a demo
    """
    params = dict(request.params.copy())
    if 'app' not in params or 'name' not in params:
        raise NotFound
    name = params['name'] = params['name'].replace(' ', '_').lower() # FIXME
    if 'plugins' in params:
        params['plugins'] = ' '.join(params['plugins'].split())
    try:
        utils.deploy(params)
    except utils.DeploymentError, e:
        _flash_message(request,
            u"Error deploying %s : %s" % (name, e.message), 'ERROR')
        return HTTPFound(location='/')

    demo = utils.InstalledDemo(name)
    _flash_message(request,
        u"application %s created on port %s" % (demo.name, demo.port),
        'SUCCESS')
    return HTTPFound(location='/')


def start(request):
    """ view that starts the demo
    """
    name = request.params.get('name', '_')
    demo = utils.InstalledDemo(name)

    old_status = demo.get_status()
    message = u'Nothing changed'
    try:
        demo.start()
    except Exception, e:
        message = u'Error: %s' % e.message
        _flash_message(request, message, 'ERROR')
        return HTTPFound(location='/')
    new_status = demo.get_status()
    if new_status == 'RUNNING' and new_status != old_status:
        message = u'Demo "%s" succesfully started' % demo.name
    _flash_message(request, message, 'SUCCESS')
    return HTTPFound(location='/')


def stop(request):
    """ view that stops a demo
    """
    name = request.params.get('name', '_')
    demo = utils.InstalledDemo(name)

    old_status = demo.get_status()
    message = u'Nothing changed'
    try:
        demo.stop()
    except Exception, e:
        message = u'Error: %s' % e.message
        _flash_message(request, message, 'ERROR')
        return HTTPFound(location='/')
    new_status = demo.get_status()
    if new_status == 'STOPPED' and new_status != old_status:
        message = u'Demo "%s" succesfully stopped' % demo.name
    _flash_message(request, message, 'SUCCESS')
    return HTTPFound(location='/')


def start_all(request):
    """ view to start supervisor
    """
    try:
        utils.SuperVisor().start()
    except AssertionError:
        message = u'Could not start supervisor. Please retry in a few seconds.'
        _flash_message(request, message, 'ERROR')
    return HTTPFound(location='/')


def stop_all(request):
    """ view to stop supervisor and all demos
    """
    utils.SuperVisor().stop()
    return HTTPFound(location='/')


def destroy(request):
    """ Destroy a demo
    """
    name=request.params['name']
    try:
        utils.InstalledDemo(name).destroy()
    except Exception, e:
        message = 'Error: %s' % e.message
        _flash_message(request, message, 'ERROR')
        return HTTPFound(location='/')

    _flash_message(request, '%s demo successfully deleted!' % name, 'SUCCESS')
    return HTTPFound(location='/')


def app_params(request):
    """ return the params of a given demo, in a json list.
    This is used in the app creation form
    """
    available_demos = utils.available_demos()
    if 'app' in request.params and request.params['app'] in available_demos:
        return utils.available_demos()[request.params['app']]
    else:
        return ("No application name given or unknown application.",)

def app_script(request):
    """ return the script of a given demo, this is a link avaiable during the
    demo creation process
    """
    if 'app' in request.params and request.params['app'] in utils.available_demos():
        app = request.params['app']
        return render_template_to_response(
        join(abspath(dirname(__file__)), 'templates', 'script.pt'),
        master=get_template('templates/master.pt'),
        lines=enumerate(open(utils.scriptname(app)).readlines()),
        logged_in=authenticated_userid(request),
        )

    else:
        return ("No application name given or unknown application.",)

def postinstall(request):
    """ execute the postinstall script for a demo
    """
    if 'app' in request.params and request.params['app'] in [d['name'] for d in utils.installed_demos()]:
        app = request.params['app']
        demo = utils.InstalledDemo(app)
        script = join(demo.path, 'post_install.sh')
        with open(script, 'r+') as s:
            start = ''
            content = s.read()
            if not content.startswith('#!'):
                start = '#!/bin/bash\n'
            content = start + content
            s.seek(0); s.truncate(); s.write(content)
        with keep_working_dir:
            os.chdir(demo.path)
            subprocess.call(['chmod', '+x', script])
            subprocess.call([script])
        os.rename(script, script + '.executed')
    return HTTPFound(location=getattr(request, 'referrer', False) or '/')




