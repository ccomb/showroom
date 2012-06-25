from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.configuration import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid_signup import groupfinder
from pyramid_signup.interfaces import ISUSession
from showroom.models import RootFactory
from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
import pyramid_zcml


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def showroom(global_config, **settings):
    """ This function returns a WSGI application.

    It is usually called by the PasteDeploy framework during
    ``paster serve``.
    """
    config = Configurator(settings=settings)
    config.begin()

    # authorization
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)

    # authentication
    authn_policy = AuthTktAuthenticationPolicy('secret', callback=groupfinder)
    config.set_authentication_policy(authn_policy)

    config.include('pyramid_tm')

    # allow some ZCML configuration
    config.include(pyramid_zcml)
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    config.load_zcml(zcml_file)

    # for sessions (signup, etc.)
    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

    # for db
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)

    # for signup
    if settings.get('su.require_activation', True):
        config.include('pyramid_mailer')
    config.registry.registerUtility(DBSession, ISUSession)
    config.include('pyramid_signup')
    config.add_view('showroom.views.ForgotPasswordController',
                    attr='forgot_password',
                    route_name='forgot_password',
                    renderer='templates/forgot_password.pt')
    config.add_view('showroom.views.AuthController',
                    attr='login',
                    route_name='login',
                    renderer='templates/login.pt')
    config.add_view('showroom.views.ProfileController',
                    attr='profile',
                    route_name='profile',
                    renderer='templates/profile.pt')
    config.add_view('showroom.views.ProfileController',
                    attr='edit_profile',
                    route_name='edit_profile',
                    renderer='templates/edit_profile.pt')
    config.override_asset(to_override='pyramid_signup:templates/reset_password.mako',
                          override_with='showroom:templates/reset_password.mako')
    config.add_view('showroom.views.RegisterController',
                    attr='register',
                    route_name='register',
                    renderer='templates/register.pt')
    # override pyramid_signup root factory
    config.set_root_factory(RootFactory)

    config.end()
    return config.make_wsgi_app()
