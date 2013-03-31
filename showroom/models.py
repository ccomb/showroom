import utils
from urlparse import urlsplit, urlunsplit

class RootFactory(object):
    """ root object factory for the whole app
    """
    def __init__(self, request):
        self.request = request
        current_host = urlsplit(request.host_url)
        admin_url = urlunsplit((current_host.scheme,
                                utils.ADMIN_HOST, '/', '', ''))
        self.request['admin_url'] = admin_url
        self.is_root = True

