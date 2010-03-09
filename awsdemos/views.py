from ConfigParser import ConfigParser
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
from repoze.bfg.testing import DummyRequest
import subprocess
import os
import time
import webob
from repoze.bfg.security import (
    Allow,
    Everyone,
    Authenticated,
    authenticated_userid,
    has_permission,
    )



def load_app_list():
    """
    return a dict containing all apps and their respective commands defined in
    config file.

    >>> load_app_list()
    {'repoze.bfg': ['NAME', 'COMMENT']}
    """
    demos = {}
    for file in (
                    i for i in os.listdir('scripts')
                    if i.startswith('demo_') and i.endswith('.sh')
                ):
        for line in open('scripts'+os.sep+file):
            if line.split(':')[0] == '# PARAMS':
                params = line.split('\n')[0].split(':')[1].split(',')
        demos[(file[5:-3])] = params
    return demos


def app_list(request):
    """
    return the main page, with applications list, and actions.
    """
    return render_template_to_response(
        "templates/app_list.pt",
        request=request,
        demos=load_app_list()
        )

def LOG(string):
    print 'LOG: '+string
    file = open('commands_demos.log', 'a+')
    file.write(time.asctime(time.localtime())+'\n')
    file.write(string+'\n')
    file.close()

def demo_form(request):
    """
    return the form to create a demo
    """
    if 'app' in request.params and request.params['app'] in load_app_list():
        return render_template_to_response(
            "templates/new_app.pt",
            request=request,
            paramlist=load_app_list()[request.params['app']],
            demo=request.params['app']
        )
    else:
        return webob.Response(str(
            "No application name given or unknown application."
            ))


def action(request):
    """
    Execute the action bound to the name passed and return when the action is
    finished.
    FIXME: should verify if the user has access to the command.

    If we don't specify an app, or we specify a non existing app, we get a 404:

    >>> action(DummyRequest())
    Traceback (most recent call last):
    ...
    NotFound
    >>> action(DummyRequest({'app':'toto'}))
    Traceback (most recent call last):
    ...
    NotFound

    >>> action(DummyRequest({'app':'repoze.bfg',
    ...                      'NAME':'foobar',
    ...                      'COMMENT': 'commentaire'}))
    LOG: scripts/demo_repoze.bfg.sh 'foobar' 'commentaire'
    <Response at ... 200 OK>

    """
    if 'app' not in request.params:
        raise NotFound
    if request.params['app'] in load_app_list():
        command = "scripts/demo_"+request.params['app']+".sh"
        params = tuple([
            "'"+request.params[x]+"'" for x in load_app_list()[request.params['app']]
            ])
        LOG(command+' '+' '.join(params))
        process = subprocess.Popen(command+' '+' '.join(params), shell=True)
        stdout, stderr = process.communicate()
        return webob.Response(str("action finished"+str(stdout))+str(stderr))
    else:
        raise NotFound



