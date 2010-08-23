# -*- coding: utf-8 -*-
from wsgiproxy.exactproxy import proxy_exact_request
from webob import Request, Response
from webob.exc import HTTPFound
import urllib
from ConfigParser import ConfigParser
from os.path import join, dirname

from awsdemos.utils import APPS_CONF, ADMIN_HOST, installed_demos

class Proxy(object):
    """ wsgi middleware that acts as a proxy, or directs to the admin
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        global ADMIN_HOST
        if ADMIN_HOST is None:
            ADMIN_HOST = request.host

        # we'll get the demo name from the url
        request = Request(environ)
        splitted_host = request.host.split(':')[0].split('.')
        hostname = request.host.split(':')[0]

        if hostname == ADMIN_HOST:
            # go to the admin interface
            return self.app(environ, start_response)

        if ADMIN_HOST not in hostname:
            # redirect to the configured hostname
            url = request.url.replace(hostname, ADMIN_HOST)
            response = HTTPFound(location=url)
            return response(environ, start_response)

        demo_name = hostname[:-len(ADMIN_HOST)][:-1]
        # for a domain "a.b.c.com", first try "a.b.c", then "a.b" and "a" as a demo_name
        for i in range(len(splitted_host), 1, -1):
            try_this_name = '.'.join(splitted_host[1:i])
            if APPS_CONF.has_section(try_this_name):
                demo_name = try_this_name


        # if the app is not running, tell it
        if installed_demos(request, demo_name=demo_name)[0]['state'] != 'RUNNING':
            admin_url = request.url.replace(demo_name+'.', '')
            message = (u'<html><body>'
                       u'This demo is not running. You can start it from the '
                       u'<a href="%s">admin interface</a>'
                       u'</body></html>') % admin_url
            return Response(message)(environ, start_response)
        # otherwise, redirect to the demo with the correct port
        port = APPS_CONF.get(demo_name, 'port')
        request.script_name = None
        request.content_length = len(request.body)
        path_info = urllib.quote(request.path_info)
        app_type = APPS_CONF.get(demo_name, 'type')
        request.path_info = path_info
        request.environ['SERVER_NAME'] = 'localhost'
        request.environ['SERVER_PORT'] = port
        response = request.get_response(proxy_exact_request)
        return response(environ, start_response)


def make_filter(global_conf, **local_conf):
    """factory for the [paste.filter_factory] entry-point
    (see setup.py)
    """
    def filter(app):
        return Proxy(app)
    return filter

