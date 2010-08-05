# -*- coding: utf-8 -*-
from awsdemos.utils import APPS_CONF
from restkit.ext.wsgi_proxy import Proxy
from webob import Request, exc
import urllib

class AppProxy(object):
    """ wsgi middleware that acts as a proxy, or directs to the admin
    """
    proxy = Proxy(allowed_methods=['GET', 'HEAD', 'POST'])

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)

        # get the demo name from the url (1st part of the domain)
        demo_name = None
        if '.' in request.host:
            demo_name = request.host.split('.')[0]

        # redirect to the correct port, or redirect to the admin
        if APPS_CONF.has_section(demo_name):
            port = APPS_CONF.get(demo_name, 'port')
            request.script_name = None
            request.content_length = len(request.body)
            path_info = urllib.quote(request.path_info)
            app_type = APPS_CONF.get(demo_name, 'type')
            request.path_info = path_info
            request.environ['SERVER_NAME'] = 'localhost'
            request.environ['SERVER_PORT'] = port
            response = request.get_response(self.proxy)
            return response(environ, start_response)
        else:
            return self.app(environ, start_response)
            return exc.HTTPFound(location='admin')

def make_filter(global_conf, **local_conf):
    """factory for the [paste.filter_factory] entry-point
    (see setup.py)
    """
    def filter(app):
        return AppProxy(app)
    return filter

