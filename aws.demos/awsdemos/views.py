import webob
from repoze.bfg.chameleon_zpt import get_template
from repoze.bfg.chameleon_zpt import render_template_to_response
import time

def my_view(request):
    return {'project':'aws.demos'}

def load_app_list():
    demos = {}
    last = ""
    file = open("awsdemos/demos.cfg")
    for line in file.readlines():
        line = line[:-1]
        if line[:4] == 4*' ':
            demos[last][line[4:].split(':')[0]] = line.split(':')[1]
        else:
            demos[line]= {}
            last = line
    file.close()
    return demos

def app_list(context, request):
    demos = {}
    last = ""
    file = open("awsdemos/demos.cfg")
    for line in file.readlines():
        line = line[:-1]
        if line[:4] == 4*' ':
            demos[last][line[4:].split(':')[0]] = line.split(':')[1]
        else:
            demos[line]= {}
            last = line
    file.close()
    return render_template_to_response(
                "templates/app_list.pt",
                context=context,
                request=request,
                demos=demos
                )

def action(context, request):
    print load_app_list()[request.params['app']][request.params['action']]
    time.sleep(3)
    return webob.Response(str("action started"))
