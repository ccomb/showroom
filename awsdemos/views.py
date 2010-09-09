# coding: utf-8
from awsdemos.security import ldaplogin
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.security import authenticated_userid, forget, remember
from repoze.bfg.url import route_url
from urlparse import urlsplit, urlunsplit
from utils import ADMIN_HOST
from webob.exc import HTTPFound
import logging
import utils
import webob

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


def proxied_url(demo, request):
    current_host = urlsplit(request.host_url)
    return urlunsplit(
        (current_host.scheme, ADMIN_HOST + ':' + demo.get_port(), '/', '', ''))


def direct_url(demo, request):
    current_host = urlsplit(request.host_url)
    return urlunsplit(
        (current_host.scheme, demo.name + '.' + ADMIN_HOST + ':' + str(current_host.port), '/', '', ''))

def view_app_list(request):
    """ return the main page, with applications list, and actions.
    """
    return render_template_to_response(
        "templates/master.pt",
        request=request,
        apps=utils.available_demos(),
        proxied_url=proxied_url,
        direct_url=direct_url,
        demos=utils.installed_demos(),
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
    available_demos = utils.available_demos()
    if 'app' in request.params and request.params['app'] in available_demos:
        return utils.available_demos()[request.params['app']][0]
    else:
        return ("No application name given or unknown application.",)

def app_plugins(request):
    """
    return the plugins of a given demo, in a json list.

    """
    available_demos = utils.available_demos()
    if 'app' in request.params and request.params['app'] in available_demos:
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
    available_demos = utils.available_demos()
    if 'app' in request.params and request.params['app'] in available_demos:
        return render_template_to_response(
            "templates/new_app.pt",
            request=request,
            paramlist=available_demos[request.params['app']],
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
    """
    params = request.params.copy()
    if 'app' not in params or 'NAME' not in params:
        raise NotFound
    name = params['NAME'].replace(' ', '_').lower() # FIXME
    try:
        utils.deploy(params['app'], name)
    except utils.DeploymentError, e:
        _flash_message(request,
            u"Error : %s" % e.message)
        return HTTPFound(location='/')

    demo = utils.InstalledDemo(name)
    _flash_message(request,
        u"application %s created at port %s" % (demo.name, demo.port))
    return HTTPFound(location='/')


def daemon(request):
    """ view that starts, stops or restarts the demo
    TODO : move the startup and stop in a function
    """
    name = request.params.get('NAME', '_')
    command = request.params.get('COMMAND', 'restart').lower()
    demo = utils.InstalledDemo(name)

    # get the state
    state = demo.get_state()
    message = u'Nothing changed'

    # stop if asked
    if state == 'RUNNING' and command in ('stop', 'restart'):
        demo.stop()
        message = u'%s stopped!' % (name)

    # get the state again
    state = demo.get_state()

    # start if asked
    if state == 'STOPPED' and command in ('start', 'restart'):
        demo.start()
        message = u'%s started!' % (name)

    _flash_message(request, message)
    return HTTPFound(location='/')


def delete_demo(request):
    """ If an application of the name NAME is deployed, we delete it
    """
    name=request.params['NAME']
    try:
        utils.InstalledDemo(name).destroy()
    except utils.DestructionError, e:
        message = 'Error: %s' % e.message
        _flash_message(request, message)
        return HTTPFound(location='/')

    _flash_message(request, '%s demo successfully deleted!' % name)
    return HTTPFound(location='/')

