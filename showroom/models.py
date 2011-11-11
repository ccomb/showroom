from pyramid.security import Allow, Authenticated

class RootFactory(object):
    """
    this class allow us to setup security policies in the application.

    """
    __acl__ = [ (Allow, Authenticated, 'edit'), ]
    def __init__(self, request):
        self.__dict__.update(getattr(request, 'matchdict', {}))
