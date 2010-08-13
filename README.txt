The goal is to create a management application for aws demos. The application is
a minimalistic repoze.bfg application.


Basic usage:

- we launch the aws.demos buildout (python bootstrap.py && ./bin/buildout)
- we launch the application (bin/paster serve deploy.ini)
- we can access a web page with the list of preconfigured demos (created
  dynamically from deployment scripts)
- In the list, each demo item contains :
    - the name of the demo
    - a status indicator (green = online and running, red: offline or broken)
    - a button to reset the demo (clean the database)
- if we click on the button, the demo is built, and the status becomes green
- we get a link to the demo

Admin usage:

- We can click on an admin link.
- We are asked for the admin password
- the home page now contains additional things:
    - a "new" button to create a new demo
    - a "clone" button to clone a preconfigured demo
- We click on the "new" button.
- We get a new page with a form, with the following fields
    - demo name
    - url of the repository
    - others fields? (for Plone demos, we need to be able to add a list of
      products in the instance)
    - (the user/password of the new instance?)


TODO :

• arreter automatiquement le supervisor si zero demo
• pouvoir visualiser les scripts
• afficher le nombre de lignes du script
• calculer le temps de déploiement
• (tracer des courbes avec tout ces valeurs)
• mettre un bouton "ajouter la prise en charge d'une nouvelle démo" qui explique
comment faire et donne le squelette du script 
• si la démo n'est pas démarrée, intercepter les requetes dans le proxy et
afficher une page disant que l'appli est pas démarrée.
• lancer les déploiements en asynchrone, et afficher un gif animé pour montrer
que ça tourne.
• Eventuellement faire ça avec zc.async.
• pouvoir sauvegarder un déploiement pour le reproduire (sauf le port)
• si une nouvelle conf apache fait planter apache, la virer et redémarrer apache
• stopper les demos si aucune requete n'est faite pendant 5min. proposer de
redémarrer si on essaye d'y accéder quand-même.
• ajouter un indicateur vert/rouge pour apache et les DB
• ne pas démarrer apache automatiquement
