from repoze.bfg import testing
from repoze.bfg.configuration import Configurator
from repoze.bfg.exceptions import NotFound
import unittest, doctest

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = Configurator()
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def test_view_app_list(self):
        """check that the app list don't fail
        """
        from awsdemos.views import view_app_list
        request = testing.DummyRequest()
        info = view_app_list(request)
        self.assertEqual(info.status, '200 OK')

    def test_action(self):
        """an action without argument should return NotFound
        """
        from awsdemos.views import action
        request = testing.DummyRequest()
        self.assertRaises(NotFound, action, request)

    def test_new_app(self):
        from awsdemos.views import action
        request = testing.DummyRequest(params={'app':'not_existing'},
                                       path='/new')
        self.assertRaises(NotFound, action, request)





def additional_tests():
    """Setuptools/Distribute looks for this additional function when searching
    tests through the 'test_suite' argument of setup()

    This is used to add doctests to the test suite
    """
    import awsdemos
    return doctest.DocTestSuite(awsdemos.views,
                                optionflags=doctest.ELLIPSIS)

