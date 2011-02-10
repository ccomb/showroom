# coding: utf-8
from awsdemos.security import ldaplogin
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.security import authenticated_userid, forget, remember
from repoze.bfg.url import route_url
from urlparse import urlsplit, urlunsplit
from os.path import join, abspath, dirname
from utils import ADMIN_HOST
from webob.exc import HTTPFound
import logging
import utils
import webob

LOG = logging.getLogger(__name__)


def _flash_message(request, message):
    """send a message through the session to the next url
    """
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
    current_host = urlsplit(request.host_url)
    return urlunsplit(
        (current_host.scheme, ADMIN_HOST + ':' + demo['port'], '/', '', ''))

def installed_demos(request):
    """ return the main page, with applications list, and actions.
    """
    return render_template_to_response(
        join(abspath(dirname(__file__)), 'templates', 'demos.pt'),
        master=get_template('templates/master.pt'),
        request=request,
        apps=utils.available_demos(),
        proxied_url=proxied_url,
        direct_url=direct_url,
        demos=utils.installed_demos(),
        logged_in=authenticated_userid(request),
        )


def json_available_demos(request):
    """return a json view of all apps and their params/plugins
    """
    return utils.available_demos()


def json_installed_demos(request):
    """ return a json view of all installed apps and their statuses
    """
    return utils.installed_demos()


def login(request):
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
        if ldaplogin(login, password):
            headers = remember(request, login)
            return HTTPFound(location = came_from,
                             headers = headers)
        message = 'Failed login'

    return dict(
        master=get_template('templates/master.pt'),
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        )


def logout(request):
    """ Get out of the application.
    """
    headers = forget(request)
    return HTTPFound(location = '/', headers = headers)


def deploy(request):
    """ deploy a demo
    """
    params = request.params.copy()
    if 'app' not in params or 'name' not in params:
        raise NotFound
    name = params['name'].replace(' ', '_').lower() # FIXME
    if 'plugins' in params:
        params['plugins'] = ' '.join(params['plugins'].split())
    try:
        utils.deploy(params, name)
    except utils.DeploymentError, e:
        _flash_message(request,
            u"Error : %s" % e.message)
        return HTTPFound(location='/')

    demo = utils.InstalledDemo(name)
    _flash_message(request,
        u"application %s created on port %s" % (demo.name, demo.get_port()))
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
        _flash_message(request, message)
        return HTTPFound(location='/')
    new_status = demo.get_status()
    if new_status == 'RUNNING' and new_status != old_status:
        message = u'Demo "%s" succesfully started' % demo.name
    _flash_message(request, message)
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
        _flash_message(request, message)
        return HTTPFound(location='/')
    new_status = demo.get_status()
    if new_status == 'STOPPED' and new_status != old_status:
        message = u'Demo "%s" succesfully stopped' % demo.name
    _flash_message(request, message)
    return HTTPFound(location='/')


def destroy(request):
    """ Destroy a demo
    """
    name=request.params['name']
    try:
        utils.InstalledDemo(name).destroy()
    except utils.DestructionError, e:
        message = 'Error: %s' % e.message
        _flash_message(request, message)
        return HTTPFound(location='/')

    _flash_message(request, '%s demo successfully deleted!' % name)
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
    if 'app' in request.params and request.params['app'] in available_demos:
        return render_template_to_response(
        join(abspath(dirname(__file__)), 'templates', 'script.pt'),
        master=get_template('templates/master.pt'),
        lines=enumerate(open(utils.scriptname(app)).readlines()),
        logged_in=authenticated_userid(request),
        )

    else:
        return ("No application name given or unknown application.",)

