from os import mkdir, chdir, getcwd
from os.path import abspath, dirname, join
from pyramid import testing
from pyramid.configuration import Configurator
from pyramid.exceptions import NotFound
import showroom.utils
import showroom.views
import tempfile, shutil
import unittest, doctest

PATHS = showroom.utils.PATHS

def setUp(self):
    # For the tests, we change the location of the demos
    base_dir = dirname(dirname(abspath(__file__)))
    self.tempdir = tempfile.mkdtemp(dir=getcwd())
    # copy etc
    etc = join(self.tempdir, 'etc')
    shutil.copytree(join(dirname(dirname(abspath(__file__))), 'etc'), etc)
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
    shutil.copy(join(base_dir, 'etc', 'supervisord.cfg'), self.tempdir)
    # create a demo directory
    demos = join(self.tempdir, 'demos')
    mkdir(demos)

    # we modify the original supervisor file
    self.supervisor = join(self.tempdir, 'supervisord.cfg')
    with open(self.supervisor, 'r+') as s:
        content = s.read()
        content = content.replace('8002', '8003')
        content = content.replace('../../demos', 'demos')
        content = content.replace('etc/apache2', join(etc, 'apache2'))
        s.seek(0); s.truncate(); s.write(content)

    # we modify the original apache file
    self.apache = join(etc, 'apache2', 'apache2.conf')
    with open(self.apache, 'r+') as s:
        content = s.read()
        content = content.replace('../../var', var)
        content = content.replace('etc', etc)
        s.seek(0); s.truncate(); s.write(content)

    # update the PATHS
    PATHS['var'] = var
    PATHS['etc'] = etc
    PATHS['demos'] = demos
    PATHS['scripts'] = scripts
    PATHS['supervisor'] = self.supervisor

    # we start supervisor again with the new config
    self.cwd = getcwd()
    chdir(base_dir)
    supervisor = showroom.utils.SuperVisor(self.supervisor)
    self.globs = {'supervisor': supervisor}


def tearDown(self):
    # we restore the scripts path
    PATHS['scripts'] = self.scripts
    # we stop our custom supervisor
    showroom.utils.SuperVisor(self.supervisor).stop()
    shutil.rmtree(self.tempdir)
    chdir(self.cwd)


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
        from showroom.views import installed_demos
        request = testing.DummyRequest()
        info = installed_demos(request)
        self.assertEqual(info.status, '200 OK')

    def test_deploy(self):
        """a deploy without argument should return NotFound
        """
        from showroom.views import deploy
        request = testing.DummyRequest()
        self.assertRaises(NotFound, deploy, request)

    def test_new_app(self):
        from showroom.views import deploy
        request = testing.DummyRequest(params={'app':'not_existing'},
                                       path='/new')
        self.assertRaises(NotFound, deploy, request)


def test_suite():

    optionflags = doctest.NORMALIZE_WHITESPACE+doctest.ELLIPSIS
    suite = unittest.TestSuite([
        unittest.makeSuite(ViewTests),
        doctest.DocFileSuite('utils.txt', optionflags=optionflags, setUp=setUp, tearDown=tearDown),
        doctest.DocTestSuite(showroom.utils, optionflags=optionflags),
        doctest.DocFileSuite('views.txt', optionflags=optionflags, setUp=setUp, tearDown=tearDown),
        doctest.DocTestSuite(showroom.views, optionflags=optionflags),
    ])
    return suite

