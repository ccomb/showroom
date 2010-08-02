# -*- coding: utf-8 -*-
from restkit.ext.wsgi_proxy import Proxy
from webob import Request, exc
from awsdemos.utils import APPS_CONF
import urllib

class AppProxy(object):

    proxy = Proxy(allowed_methods=['GET', 'HEAD', 'POST'])

    def _rewrite(self, name, req):
        path_info = urllib.quote(req.path_info)
        app_type = APPS_CONF.get(name, 'type')
        if app_type == 'plone':
            host = req.host
            if ':' not in host:
                host = '%s:80' % host
            path_info = '/VirtualHostBase/http/%s/VirtualHostRoot/%s%s' % (host, name, path_info)
        else:
            path_info = '/%s%s' % (name, path_info)
        req.path_info = path_info
        return req

    def __call__(self, environ, start_response):
        req = Request(environ)
        name = req.path_info_pop().strip('/')
        if APPS_CONF.has_section(name):
            port = APPS_CONF.get(name, 'port')
            req.script_name = None
            req.content_length = len(req.body)
            self._rewrite(name, req)
            req.environ['SERVER_NAME'] = 'localhost'
            req.environ['SERVER_PORT'] = port
            resp = req.get_response(self.proxy)
            return resp(environ, start_response)
        else:
            return exc.HTTPNotFound()(environ, start_response)

def make_proxy(global_conf, **local_conf):
    return AppProxy()

