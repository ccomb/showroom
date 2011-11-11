from pyramid.configuration import Configurator
from showroom.models import RootFactory
import pyramid_zcml

def app(global_config, **settings):
    """ This function returns a WSGI application.

    It is usually called by the PasteDeploy framework during
    ``paster serve``.
    """
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include(pyramid_zcml)
    config.begin()
    config.load_zcml(zcml_file)
    config.end()
    return config.make_wsgi_app()
