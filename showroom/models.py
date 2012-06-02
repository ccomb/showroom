from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS

class RootFactory(object):
    """ root object factory for the whole app
    """
    def __init__(self, request):
        self.request = request
        self.is_root = True

    @property
    def __acl__(self):
        defaultlist = [
            (Allow, 'group:admin', ALL_PERMISSIONS),
            (Allow, Authenticated, 'view'),
            (Allow, Authenticated, 'edit'),
        ]
        return defaultlist

