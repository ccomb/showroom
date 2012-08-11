# -*- coding: utf-8 -*-
from os.path import join, dirname, abspath
from webob import Request, Response
from webob.exc import HTTPFound
from wsgiproxy.exactproxy import proxy_exact_request
import logging
import urllib

from showroom.utils import PATHS, ADMIN_HOST, InstalledDemo, UnknownDemo

#logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

CSS = '''
<link href="/showroom_static/jquery/css/showroom/jquery-ui-1.8.16.custom.css" type="text/css" rel="stylesheet" />
<link href="/showroom_static/popup.css" type="text/css" rel="stylesheet" />
'''

JS = '''
<script type="text/javascript" src="/showroom_static/jquery/js/jquery-1.6.2.min.js"></script>
<script type="text/javascript" src="/showroom_static/jquery/js/jquery-ui-1.8.16.custom.min.js"></script>
<script type="text/javascript">
    $.noConflict();
    jQuery(document).ready(function($) {
        $("#showroompopup").dialog({width: "40%%", title: 'Installation instructions'}).parents(".ui-dialog:eq(0)").wrap('<div id="showroomscope"></div>');
        $('#showroompopup_hide form input').click(
            function() {
                $.get(window.location.protocol + '//' + window.location.host + '/?showroompopup_hide');
                $("#showroompopup").parent().hide();
            }
        );
    })
</script>
'''

class Proxy(object):
    """ wsgi middleware that acts as a proxy, or redirects to the admin
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        global ADMIN_HOST
        request = Request(environ)

        if ADMIN_HOST is None:
            ADMIN_HOST = request.host

        # We parse this from the right : ['a.b.c', 'user', 'showroom', 'io']
        splitted_host = request.host.split(':')[0].rsplit('.', 3)

        # bad domain?
        if splitted_host.pop(-2) + '.' + splitted_host.pop() != ADMIN_HOST:
            # redirect to the configured hostname
            hostname = request.host.split(':')[0]
            url = request.url.replace(hostname, ADMIN_HOST)
            response = HTTPFound(location=url)
            return response(environ, start_response)

        # 'user.showroom' or 'showroom.io'
        if len(splitted_host) <= 1:
            # go to the admin interface
            return self.app(environ, start_response)

        demo_name, user_name = splitted_host

        # for a domain "a.b.c.com", first try "a.b.c", then "a.b" and "a" as a demo_name
        for i in range(1, len(splitted_host)):
            try_this_name = '.'.join(splitted_host[:-i])
            if try_this_name in PATHS['demos']:
                demo_name = try_this_name
                break

        # get the user for this demo
        admin_url = request.host_url.replace(demo_name+'.'+user_name+'.', '')
        try:
            demo = InstalledDemo(user_name, demo_name)
        except UnknownDemo:
            message = (u'<html><body>'
                       u'This demo does not exist. You can create it though the '
                       u'<a href="%s">admin interface</a>'
                       u'</body></html>') % admin_url
            return Response(message)(environ, start_response)
            
        # XXX possibly do an auth on the demo

        # if the app is not running, tell it
        if demo.get_status() != 'RUNNING':
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
        request.environ['SERVER_PORT'] = demo.port
        # disable compression to be able to insert the js popup
        request.environ['HTTP_ACCEPT_ENCODING'] = ''
        response = request.get_response(proxy_exact_request)

        # disable the popup if asked
        if 'showroompopup_hide' in environ['QUERY_STRING']:
            demo.disable_popup()

        # inject the information popup
        content = demo.popup
        if content is not None and demo.is_popup_displayed:
            popup = open(join(abspath(dirname(__file__)),
                              'templates', 'popup.html')).read() % content

            if 'html' in (response.content_type or ''):
                if '</body>' in response.body and '<head>' in response.body:
                    response.body = response.body.replace('</head>', CSS + JS + '</head>')
                    response.body = response.body.replace('</body>', popup + '</body>')
                else:
                    response.body = CSS + JS + response.body + popup

        return response(environ, start_response)


def make_filter(global_conf, **local_conf):
    """factory for the [paste.filter_factory] entry-point
    (see setup.py)
    """
    def filter(app):
        return Proxy(app)
    return filter

