from dataflake.ldapconnection.connection import LDAPConnection as ldap
from ldap import INVALID_CREDENTIALS as invalid_credentials
#from pyramid.security import Authenticated
from showroom.utils import CONFIG
import hashlib

def invalid_method(username, password):
    """fallback function to raise an error if config is invalid
    """
    raise Exception('Bad login_method in showroom.ini')

def auth_ldap(username, password):

    host = CONFIG.get('auth_ldap', 'host')
    bind_dn = CONFIG.get('auth_ldap', 'bind_dn')
    base = CONFIG.get('auth_ldap', 'base')
    fltr = CONFIG.get('auth_ldap', 'fltr')
    uid = CONFIG.get('auth_ldap', 'uid')

    conn = ldap(
        host=host,
        bind_dn=bind_dn % username,
        bind_pwd=password
        )
    try:
        short_name = conn.search(
            base=base,
            fltr='cn=%s' % username
            )['results'][0]['uid'][0]

        return short_name in conn.search(
            base=base,
            fltr=fltr
            )['results'][0][uid]

    except invalid_credentials:
        return False


def encrypted_password(password):
    password_type = CONFIG.get('global', 'password_type')
    if password_type == 'plain':
        return password
    if password_type == 'sha1':
        return hashlib.sha1(password).hexdigest()


def auth_static(username, password):
    if not CONFIG.has_option('auth_static', username):
        return False
    stored_password = CONFIG.get('auth_static', username)
    if stored_password != encrypted_password(password):
        return False
    return True

# select login method according to the config
check_login = CONFIG.get('global', 'login_method')
if check_login in dir() and check_login.startswith('auth_'):
    check_login = eval(check_login)
else:
    check_login = invalid_method

