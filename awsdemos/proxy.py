# -*- coding: utf-8 -*-
from restkit.ext.wsgi_proxy import Proxy
from awsdemos import utils
from webob import Request, exc

class AppProxy(object):

    proxy = Proxy(allowed_methods=['GET', 'HEAD', 'POST'])

    def rewrite(self, name, app, req):
        if app.type == 'repoze.bfg':
            path_info = '/%s%s' % (name, req.path_info)
        elif app.type == 'plone':
            host = req.host
            if ':' not in host:
                host = '%s:80' % host
            path_info = '/VirtualHostBase/http/%s/VirtualHostRoot/%s%s' % (host, name, req.path_info or '/')
        req.path_info = path_info.replace(' ', '%20')
        return req

    def __call__(self, environ, start_response):
        req = Request(environ)
        name = req.path_info_pop().strip('/')
        app = utils.get_app(name)
        if app.port:
            req.script_name = None
            req.content_length = len(req.body)
            self.rewrite(name, app, req)
            req.environ['SERVER_NAME'] = '127.0.0.1'
            req.environ['SERVER_PORT'] = app.port
            resp = req.get_response(self.proxy)
            return resp(environ, start_response)
        return exc.HTTPNotFound()(environ, start_response)

def make_proxy(global_conf, **local_conf):
    return AppProxy()

