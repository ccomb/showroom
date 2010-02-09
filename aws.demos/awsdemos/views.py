def my_view(request):
    return {'project':'aws.demos'}

def app_list(request):
    return repr(request)
