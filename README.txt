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
  mysql-server php5 php5-mysql php5-gd wv poppler-utils zlib1g-dev

Then you can install the development trunk of Showroom with::

  $ hg clone https://bitbucket.org/alterway/aws.demos
  $ cd aws.demos
  $ virtualenv --no-site-packages --distribute sandbox
  $ sandbox/bin/python bootstrap.py
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

* arreter automatiquement le supervisor si zero demo
* pouvoir visualiser les scripts
* afficher le nombre de lignes du script
* calculer le temps de déploiement
* (tracer des courbes avec toutes ces valeurs)
* mettre un bouton "ajouter la prise en charge d'une nouvelle démo" qui explique
  comment faire et donne le squelette du script 
* lancer les déploiements en asynchrone, et afficher un gif animé pour montrer
  que ça tourne.
* Eventuellement faire ça avec zc.async.
* pouvoir sauvegarder un déploiement pour le reproduire (sauf le port)
* stopper les demos si aucune requete n'est faite pendant 5min. proposer de
  redémarrer si on essaye d'y accéder quand-même.
* ajouter un indicateur vert/rouge pour apache et supervisor
* ajouter un proxy de téléchargement pour accélérer les déploiements
