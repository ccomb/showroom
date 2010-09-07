# keep this at the top:
import awsdemos
awsdemos.currently_testing = True
###
from os import mkdir, chdir
from os.path import abspath, dirname, join
from repoze.bfg import testing
from repoze.bfg.configuration import Configurator
from repoze.bfg.exceptions import NotFound
import awsdemos.utils
import awsdemos.views
import subprocess
import tempfile, shutil
import unittest, doctest

PATHS = awsdemos.utils.PATHS

def setUp(self):
    # For the tests, we change the location of the demos
    base_dir = dirname(dirname(abspath(__file__)))
    self.tempdir = tempfile.mkdtemp()
    # copy etc
    etc = join(dirname(dirname(abspath(__file__))), 'etc')
    shutil.copytree(etc, join(self.tempdir, 'etc'))
    # create empty var
    var = join(self.tempdir, 'var')
    mkdir(var)
    mkdir(join(var, 'apache2'))
    mkdir(join(var, 'apache2', 'demos'))
    # copy the test scripts
    self.scripts = PATHS['scripts']
    scripts = join(self.tempdir, 'scripts')
    shutil.copytree(join(PATHS['scripts'], 'test'), scripts)
    # copy the supervisor file
    shutil.copy(join(base_dir, 'supervisord.cfg'), self.tempdir)
    # create a demo directory
    demos = join(self.tempdir, 'demos')
    mkdir(demos)

    # we modify the original supervisor file
    self.supervisor = join(self.tempdir, 'supervisord.cfg')
    with open(self.supervisor, 'r+') as s:
        content = s.read()
        content = content.replace('8001', '8002')
        content = content.replace('../demos', 'demos')
        s.seek(0); s.truncate(); s.write(content)

    # update the PATHS
    PATHS['var'] = var
    PATHS['etc'] = etc
    PATHS['demos'] = demos
    PATHS['scripts'] = scripts
    PATHS['supervisor'] = self.supervisor

    # we start supervisor again with the new config
    chdir(base_dir)
    subprocess.call(PATHS['bin'] + "/supervisord -c " + self.supervisor, shell=True)
    awsdemos.utils.connect_supervisor()


def tearDown(self):
    # we restore the scripts path
    PATHS['scripts'] = self.scripts
    # we stop our custom supervisor
    subprocess.call(PATHS['bin'] + "/supervisorctl -c %s shutdown" % self.supervisor,
                    shell=True)
    shutil.rmtree(self.tempdir)


class ViewTests(unittest.TestCase):
    def setUp(self):
        setUp(self)
        self.config = Configurator()
        self.config.begin()


    def tearDown(self):
        tearDown(self)
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


def test_suite():
    optionflags = doctest.NORMALIZE_WHITESPACE+doctest.ELLIPSIS
    suite = unittest.TestSuite([
        unittest.makeSuite(ViewTests),
        doctest.DocFileSuite('views.txt', optionflags=optionflags, setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('utils.txt', optionflags=optionflags, setUp=setUp, tearDown=tearDown),
        doctest.DocTestSuite(awsdemos.views, optionflags=optionflags),
        doctest.DocTestSuite(awsdemos.utils, optionflags=optionflags),
    ])
    return suite

