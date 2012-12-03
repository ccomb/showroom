# coding: utf-8
from os.path import join, abspath, dirname
from pyramid.chameleon_zpt import get_template, render_template_to_response
from pyramid.exceptions import NotFound
from pyramid.i18n import TranslationStringFactory
from pyramid.request import Response
from pyramid.security import authenticated_userid
from pyramid_signup.managers import UserManager
from urlparse import urlsplit, urlunsplit
from webob.exc import HTTPFound
import os, deform, logging, subprocess
import pyramid_signup.views
import utils

LOG = logging.getLogger(__name__)
_ = TranslationStringFactory('showroom')

def proxied_url(demo, request):
    """Give the url of the proxied demo
    """
    user = authenticated_userid(request)
    if user is not None:
        user = UserManager(request).get_by_pk(user)

    current_host = urlsplit(request.host_url)
    port = current_host.port
    if port is None:
        host = utils.ADMIN_HOST
    else:
        host = utils.ADMIN_HOST + ':' + str(current_host.port)
    return urlunsplit(
        (current_host.scheme, demo['name'] + '.' + user.username + '.' + host, '/', '', ''))


def direct_url(demo, request):
    """Give the direct url of the demo
    """
    if demo['port'] is '':
        return "#"
    current_host = urlsplit(request.host_url)
    return urlunsplit(
        (current_host.scheme, utils.ADMIN_HOST + ':' + demo['port'], '/', '', ''))

def installed_demos(request):
    """ return the main page, with applications list, and actions.
    """
    # XXX this view is too slow

    user = authenticated_userid(request)
    if user is not None:
        user = UserManager(request).get_by_pk(user)
        return render_template_to_response(
            join(abspath(dirname(__file__)), 'templates', 'demos.pt'),
            master=get_template('templates/master.pt'),
            request=request,
            apps=utils.available_demos(),
            proxied_url=proxied_url,
            direct_url=direct_url,
            demos=utils.installed_demos(user.username),
            supervisor=utils.SuperVisor(user.username).is_running,
            logged_in=user,
            )
    else:
        return render_template_to_response(
            join(abspath(dirname(__file__)), 'templates', 'home.pt'),
            master=get_template('templates/master.pt'),
            request=request,
            apps=utils.available_demos(),
            supervisor=None,
            logged_in=None,
            )



def json_available_demos(request):
    """return a json view of all apps and their params/plugins
    """
    user = authenticated_userid(request)
    if user is not None:
        user = UserManager(request).get_by_pk(user)
    return utils.available_demos(user.username)


def json_installed_demos(request):
    """ return a json view of all installed apps and their statuses
    """
    user = authenticated_userid(request)
    if user is not None:
        user = UserManager(request).get_by_pk(user)
    return utils.installed_demos(user.username)


class AuthController(pyramid_signup.views.AuthController):
    """ Inherit from horus just to add macros
    """
    def login(self):
        """modified from horus
        """
        if self.request.method == 'GET':
            if self.request.user:
                return HTTPFound(location=self.login_redirect_view)

            return {'form': self.form.render(),
                    'master': get_template('templates/master.pt'),
                    }
        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = self.form.validate(controls)
            except deform.ValidationFailure, e:
                return {'form': e.render(), 'errors': e.error.children,
                        'master': get_template('templates/master.pt'),
                        }

            username = captured['Username']
            password = captured['Password']

            mgr = UserManager(self.request)

            user = mgr.get_user(username, password)

            if user:
                if not user.activated:
                    self.request.session.flash(_(u'Your account is not active, please check your e-mail.'), 'error')
                    return {'form': self.form.render(),
                            'master': get_template('templates/master.pt'),
                            }
                else:
                    return self.authenticated(self.request, user.pk)

            self.request.session.flash(_('Invalid username or password.'), 'error')

            return {'form': self.form.render(appstruct=captured),
                    'master': get_template('templates/master.pt'),
                    }


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


class DemoController(object):
    """controller for demos
    """
    def __init__(self, request):
        self.request = request
        self.user = authenticated_userid(self.request)
        self.name = self.request.params.get('name', '').replace(' ', '_').lower() # FIXME?
        if self.user is not None:
            self.user = UserManager(request).get_by_pk(self.user)

    def deploy(self):
        """ deploy a demo
        """
        params = dict(self.request.params.copy())
        if 'app' not in params or 'name' not in params:
            raise NotFound
        name = params['name'] = self.name
        if 'plugins' in params:
            params['plugins'] = ' '.join(params['plugins'].split())
        try:
            params['port'] = utils.get_available_port()
            utils.deploy(self.user.username, params)
        except utils.DeploymentError, e:
            self.request.session.flash(u"Error deploying %s : %s" % (name, e.message), 'error')
            return HTTPFound(location='/')
    
        demo = utils.InstalledDemo(self.user.username, name)
        self.request.session.flash(u"application %s created on port %s" % (demo.name, demo.port), 'success')
        return HTTPFound(location='/')
    
    
    def start(self):
        """ view that starts the demo
        """
        demo = utils.InstalledDemo(self.user.username, self.name)
    
        old_status = demo.get_status()
        message = u'Nothing changed'
        try:
            demo.start()
        except Exception, e:
            message = u'Error: %s' % e.message
            self.request.session.flash(message, 'error')
            return HTTPFound(location='/')
        new_status = demo.get_status()
        if new_status == 'RUNNING' and new_status != old_status:
            message = u'Demo "%s" succesfully started' % demo.name
        self.request.session.flash(message, 'success')
        return HTTPFound(location='/')
    
    
    def stop(self):
        """ view that stops a demo
        """
        demo = utils.InstalledDemo(self.user.username, self.name)
    
        old_status = demo.get_status()
        message = u'Nothing changed'
        try:
            demo.stop()
        except Exception, e:
            message = u'Error: %s' % e.message
            self.request.session.flash(message, 'error')
            return HTTPFound(location='/')
        new_status = demo.get_status()
        if new_status == 'STOPPED' and new_status != old_status:
            message = u'Demo "%s" succesfully stopped' % demo.name
        self.request.session.flash(message, 'success')
        return HTTPFound(location='/')
    
    
    def destroy(self):
        """ Destroy a demo
        """
        try:
            utils.InstalledDemo(self.user.username, self.name).destroy()
        except Exception, e:
            message = 'Error: %s' % e.message
            self.request.session.flash(message, 'error')
            return HTTPFound(location='/')
    
        self.request.session.flash('%s demo successfully deleted!' % self.name, 'success')
        return HTTPFound(location='/')


    def app_params(self):
        """ return the params of a given demo, in a json list.
        This is used in the app creation form
        """
        available_demos = utils.available_demos()
        if 'app' in self.request.params and self.request.params['app'] in available_demos:
            return utils.available_demos()[self.request.params['app']]
        else:
            return ("No application name given or unknown application.",)
    
    
    def app_script(self):
        """ return the script of a given demo, this is a link avaiable during the
        demo creation process
        """
        if 'app' in self.request.params and self.request.params['app'] in utils.available_demos(self.user.username):
            app = self.request.params['app']
            return render_template_to_response(
            join(abspath(dirname(__file__)), 'templates', 'script.pt'),
            master=get_template('templates/master.pt'),
            lines=enumerate(open(utils.scriptname(app)).readlines()),
            logged_in=self.user,
            )
    
        else:
            return ("No application name given or unknown application.",)

    def postinstall(self):
        """ execute the postinstall script for a demo
        """
        if 'app' in self.request.params and self.request.params['app'] in [d['name'] for d in utils.installed_demos(self.user.username)]:
            app = self.request.params['app']
            demo = utils.InstalledDemo(self.user.username, app)
            script = join(demo.path, 'post_install.sh')
            with open(script, 'r+') as s:
                start = ''
                content = s.read()
                if not content.startswith('#!'):
                    start = '#!/bin/bash\n'
                content = start + content
                s.seek(0); s.truncate(); s.write(content)
            with utils.keep_working_dir:
                os.chdir(demo.path)
                subprocess.call(['chmod', '+x', script])
                subprocess.call([script])
            os.rename(script, script + '.executed')
        return HTTPFound(location=getattr(self.request, 'referrer', False) or '/')

    def howto(self):
        """Display the howto for the demo
        """
        demo = utils.InstalledDemo(self.user.username, self.name)
        return render_template_to_response(
            join(abspath(dirname(__file__)), 'templates', 'demo.pt'),
            master=get_template(join('templates', 'master.pt')),
            request=self.request,
            proxied_url=proxied_url,
            howto=demo.howto(),
            demo=demo,
            supervisor=utils.SuperVisor(self.user).is_running,
            logged_in=self.user,
            )


class MainController(object):
    def __init__(self, request):
        self.request = request
        self.user = authenticated_userid(self.request)
        if self.user is not None:
            self.user = UserManager(request).get_by_pk(self.user)

    def start_all(self):
        """ view to start supervisor
        """
        try:
            utils.SuperVisor(self.user.username).start()
        except AssertionError:
            message = u'Could not start supervisor. Please retry in a few seconds.'
            self.request.session.flash(message, 'error')
        return HTTPFound(location='/')
    
    
    def stop_all(self):
        """ view to stop supervisor and all demos
        """
        utils.SuperVisor(self.user.username).stop()
        return HTTPFound(location='/')


def add_macro(result, request):
    """ Add master macro to the dict result
    """
    if hasattr(result, 'update'):
        logged_in = authenticated_userid(request)
        if logged_in is not None:
            logged_in = UserManager(request).get_by_pk(logged_in)

        result.update({'master': get_template('templates/master.pt'),
                        'logged_in': logged_in})


class RegisterController(pyramid_signup.views.RegisterController):
    """ Inherit from horus just to add macros
    """
    def register(self):
        result = super(RegisterController, self).register()
        add_macro(result, self.request)
        return result


class ForgotPasswordController(pyramid_signup.views.ForgotPasswordController):
    """ Inherit from horus just to add macros
    """
    def forgot_password(self):
        result = super(ForgotPasswordController, self).forgot_password()
        add_macro(result, self.request)
        return result


class ProfileController(pyramid_signup.views.ProfileController):
    """ Inherit from horus just to add macros
    """
    def profile(self):
        result = super(ProfileController, self).profile()
        add_macro(result, self.request)
        return result

    def edit_profile(self):
        result = super(ProfileController, self).edit_profile()
        add_macro(result, self.request)
        return result


