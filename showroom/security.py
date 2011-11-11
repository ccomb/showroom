from pyramid.security import Authenticated

from dataflake.ldapconnection.connection import LDAPConnection as ldap
from ldap import INVALID_CREDENTIALS as invalid_credentials

def ldaplogin(username, password):
    conn = ldap(
        host='ldap.alterway.fr',
        bind_dn="cn="+username+",ou=users,dc=alterway,dc=fr",
        bind_pwd=password
        )
    try:
        short_name = conn.search(
            base='dc=alterway,dc=fr',
            fltr='cn='+username
            )['results'][0]['uid'][0]

        return short_name in conn.search(
            base='dc=alterway,dc=fr',
            fltr='cn=allstaff'
            )['results'][0]['memberUid']

    except invalid_credentials:
        return False

