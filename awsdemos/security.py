USERS = {'admin':'admin'}
GROUPS = {'admin':['group.admin']}

def groupfinder(userid, request):
    """
    return the different groups the user belong to.

    """
    if userid in USERS:
        return GROUPS.get(userid, [])

