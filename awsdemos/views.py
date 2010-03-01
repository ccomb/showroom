from ConfigParser import ConfigParser
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.exceptions import NotFound
import subprocess
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
    conf = ConfigParser()
    conf.readfp(open('supervisor.cfg'))
    demos = {}
    #last = ""
    #file = open("awsdemos/demos.cfg")
    #for line in file.readlines():
        #line = line[:-1]
        #if line[:4] == 4*' ':
            #demos[last][line[4:].split(':')[0]] = line.split(':')[1]
        #else:
            #demos[line]= {}
            #last = line
    #file.close()
    for k in conf.sections():
        demos[k] = {}
        for i in conf.items(k):
            demos[k][i[0]] = i[1]
    print demos
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
    app_list = load_app_list()
    try:
        app = request.params['app']
        action = request.params['action']
        command = app_list[app][action]
    except KeyError:
        raise NotFound
    LOG(command)
    process = subprocess.Popen(command, shell=True)
    process.wait()
    return webob.Response(str("action finished"))


