"""
Update the user’s table
by adding their full-name
based on the answers from ldap3
"""
import ldap3
from typing import List
from siancedb.models import SessionWrapper, SiancedbUser
from siancedb.config import get_config

PG = get_config()["postgres"]
LDAP = get_config()["ldap"]


def ask_full_names(username, password, db, users: List[SiancedbUser]):
    ldap_server = f"{LDAP['host']}:{LDAP['port']}"
    ldap_user = f"{username}@domasn.local"

    server = ldap3.Server(ldap_server, get_info=ldap3.ALL)
    conn = ldap3.Connection(server, ldap_user, password, auto_bind=True)

    for user in users:
        print(user.username)
        fullname = ask_full_name(user.username, conn)

        user.fullname = fullname

    db.commit()


def ask_full_name(username, conn):
    try:
        conn.search(
            search_base="DC=domasn,DC=local",
            search_filter=f"(&(objectClass=person)(sAMAccountName={username}))",
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
        )
        fullname = f"{conn.response[0]['raw_attributes']['name'][0]}"
        return fullname[2:-1]
    except:
        return username


def add_full_names_to_users(user: str, password: str):
    """ Does the migration """
    with SessionWrapper() as db:
        # pylint: disable=maybe-no-member
        users = db.query(SiancedbUser).all()
        ask_full_names(user, password, db, list(users))
