Showroom
========

Overview
--------

Deploy demos of popular web applications in 1 click.

Showroom is a web application which allows you to deploy/start/stop/destroy
sandboxed *demos* of other web applications in one click. Currently supported
applications are:

- Plone 3, 4
- Drupal 5, 6, 7
- Karl 3
- OpenERP 5, 6

It can also deploy some web frameworks or environments, though it is of limited
interest from a user point of view:

- repoze.bfg
- django
- BlueBream
- PHP

Installing
----------

Showroom is currently tested only on Debian and Ubuntu. There are some system
requirements, which can be fullfilled by installing the following packages::

sudo aptitude install subversion mercurial build-essential python-virtualenv \
  python-dev libldap2-dev libsasl2-dev libssl-dev libpq-dev postgresql \
  libxml2-dev libxslt1-dev apache2 libapache2-mod-php5 libapache2-mod-python \
  mysql-server php5 php5-mysql php5-gd wv poppler-utils zlib1g-dev curl

Then you can install the development trunk of Showroom with::

  $ hg clone https://bitbucket.org/ccomb/showroom
  $ cd showroom
  $ virtualenv --no-site-packages --distribute sandbox
  $ sandbox/bin/python bootstrap.py
  $ mkdir src
  $ ./bin/buildout

Starting
--------

Start in foreground::

  $ bin/paster serve deploy.ini

Or in foreground::

  $ bin/paster serve --daemon deploy.ini

When started, Showroom will launch a Supervisor daemon to handle demos. You can
stop and restart showroom itself without affecting running demos.

Once started, you can access Showroom at http://localhost:6543/

TODO :

* automatically stop supervisor if no demo
* being able to visualize scripts
* show script LOC wheight
* calculate deployment time
* generate graphics with those data
* add a button "add a new demo script", which explain how to do it and provide
  a script template
* make deployments asynchronouss, add a small animated gif to show it's running
  zc.async can help
* being able to save a deployment to be able to reproduce it (except the port)
* stop demos if no request are done in 5 minutes, propose to restart if someone try to access
* add an indication green/red for apache and supervisord
* add a download proxy to accelerate deployments
* makes application tweet deployments
