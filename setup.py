import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools',
    'pyramid',
    'pyramid_zcml',
    'WSGIProxy',
    'afpy.ldap',
    'python-ldap',
    'Beaker',
    'interlude',
#    'gunicorn',
]

setup(name='showroom',
      version='0.1dev',
      description='Deploy web app demos in 1 click',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: BFG",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="showroom",
      entry_points = """\
      [paste.app_factory]
      app = showroom.run:app
      [paste.filter_factory]
      proxy = showroom.proxy:make_filter
      """
      )

