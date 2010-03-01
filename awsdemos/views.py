from ConfigParser import ConfigParser
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
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
    """
    demos = []
    for file in (i for i in os.listdir('scripts') if 'demo_' in i and '.sh' in i):
        demos.append(file[5:-3])
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


def action(request):
    """
    execute the action bound to the name passed and return when the action is
    finished.
    FIXME: should verify if the user has access to the command.
    """
    if request.params['app'] in load_app_list():
        command = "demo_"+request.params['app']+".sh"
        LOG(command)
        process = subprocess.Popen(command, shell=True)
        stdout, stderr = process.communicate()
        return webob.Response(str("action finished"+str(stdout))+str(stderr))
    else:
        return webob.Response(str("unknown action"))


