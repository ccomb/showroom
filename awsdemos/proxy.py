# -*- coding: utf-8 -*-
from wsgiproxy.exactproxy import proxy_exact_request
from webob import Request, Response
from webob.exc import HTTPFound
import urllib
from ConfigParser import ConfigParser
from os.path import join, dirname

from awsdemos.utils import PATHS, ADMIN_HOST, InstalledDemo

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
        for i in range(1, len(splitted_host)):
            try_this_name = '.'.join(splitted_host[:-i])
            if try_this_name in PATHS['demos']:
                demo_name = try_this_name
                break

        demo = InstalledDemo(demo_name)

        # if the app is not running, tell it
        if demo.get_status() != 'RUNNING':
            admin_url = request.url.replace(demo_name+'.', '')
            message = (u'<html><body>'
                       u'This demo is not running. You can start it from the '
                       u'<a href="%s">admin interface</a>'
                       u'</body></html>') % admin_url
            return Response(message)(environ, start_response)

        # otherwise, redirect to the demo with the correct port
        request.script_name = None
        request.content_length = len(request.body)
        path_info = urllib.quote(request.path_info)
        request.path_info = path_info
        request.environ['SERVER_NAME'] = 'localhost'
        request.environ['SERVER_PORT'] = demo.get_port()
        response = request.get_response(proxy_exact_request)
        return response(environ, start_response)


def make_filter(global_conf, **local_conf):
    """factory for the [paste.filter_factory] entry-point
    (see setup.py)
    """
    def filter(app):
        return Proxy(app)
    return filter

