
USERS = {'admin':'admin'}
GROUPS = {'admin':['groups.admin']}

def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])

