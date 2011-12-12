# -*- coding: utf-8 -*-
from os.path import join, dirname, abspath, basename, exists, splitext
from webob import Request, Response
from webob.exc import HTTPFound
from wsgiproxy.exactproxy import proxy_exact_request
import urllib
import logging
import os

from showroom.utils import PATHS, ADMIN_HOST, InstalledDemo

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

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
            css = ('<link href="/showroomstatic/jquery/css/showroom/jquery-ui-1.8.16.custom.css" type="text/css" rel="stylesheet" />\n'
                   '<link href="/showroomstatic/popup.css" type="text/css" rel="stylesheet" />\n')
            js = ('<script type="text/javascript" src="/showroomstatic/jquery/js/jquery-1.6.2.min.js"></script>\n'
                  '<script type="text/javascript" src="/showroomstatic/jquery/js/jquery-ui-1.8.16.custom.min.js"></script>\n')

            if 'html' in (response.content_type or ''):
                if '</body>' in response.body and '<head>' in response.body:
                    response.body = response.body.replace('<head>', '<head>' + js)
                    response.body = response.body.replace('</head>', css + '</head>')
                    response.body = response.body.replace('</body>', popup + '</body>')
                else:
                    response.body = css + js + response.body + popup

        return response(environ, start_response)


class StreamingIterator(object):
    """Iterator used during streaming
    infile : the file being read by chunks (cache file or download)
    outfile : the file being written (cache file)
    """
    def __init__(self, infile, outfile=None):
        self.infile = infile
        self.outfile = outfile

    def __iter__(self):
        return self

    def next(self):
        chunk = self.infile.read(2**16) #64k
        LOG.info('Reading chunk')
        if self.outfile is not None:
            LOG.info('Saving cache chunk')
            self.outfile.write(chunk)
        if len(chunk) == 0:
            self.infile.close()
            if self.outfile is not None:
                LOG.info('Finished saving cache')
                self.outfile.close()
            LOG.info('Finished reading chunks')
            raise StopIteration
        return chunk



class DownloadCacheProxy(object):
    """wsgi proxy that caches downloads
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        # test whether we're trying to download something
        host = environ.get('paste.httpserver.proxy.host', '')
        scheme = environ.get('paste.httpserver.proxy.scheme', '')
        path_info = environ.get('PATH_INFO', '')

        # do nothing if we're not acting as a proxy
        if host is '' or scheme is '':
            return self.app(environ, start_response)

        # do nothing if we're not handling this type of file
        extensions_to_cache = ('.gz', '.zip', '.egg', '.tar') #TODO move to the conf
        filename = join(PATHS['downloads'], host, basename(path_info))
        extension = splitext(filename)[1].lower()
        if extension not in extensions_to_cache:
            response = Response()
            response.app_iter = StreamingIterator(urllib.urlopen(request.url))
            return response(environ, start_response)

        # If we already have the file, stream it
        if exists(filename):
            LOG.info('Found in the download cache: %s' % filename)
            response = Response()
            response.app_iter = StreamingIterator(open(filename))
            return response(environ, start_response)

        # We don't have the file, download and stream
        if not exists(dirname(filename)):
            os.mkdir(dirname(filename))
        response = Response()
        response.app_iter = StreamingIterator(
                urllib.urlopen(request.url),
                outfile=open(filename, 'wb'))
        return response(environ, start_response)


def make_filter(global_conf, **local_conf):
    """factory for the [paste.filter_factory] entry-point
    (see setup.py)
    """
    def filter(app):
        return DownloadCacheProxy(Proxy(app))
    return filter

