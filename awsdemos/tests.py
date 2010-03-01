from repoze.bfg import testing
from repoze.bfg.configuration import Configurator
from repoze.bfg.exceptions import NotFound
import unittest

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = Configurator()
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def test_app_list(self):
        from awsdemos.views import app_list
        request = testing.DummyRequest()
        info = app_list(request)
        self.assertEqual(info.status, '200 OK')

    def test_action(self):
        from awsdemos.views import action
        request = testing.DummyRequest()
        # action without argument should raise NotFound
        self.assertRaises(NotFound, action, request)


