import pydantic

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError, ExpiredSignatureError
import ldap3

from datetime import datetime, timedelta

import sqlalchemy
from siancedb.models import SessionWrapper, SiancedbUser, log_action, SiancedbActionLog
from siancedb.config import get_config
import logging

from ..schemes import User, UserToken, DownloadToken

logger = logging.getLogger("siance-api-log")


# Defines the type of authentication to be used in this
# rest api
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Extracts configuration from the `config.json`
# file using the local `config` module
LDAP = get_config()["ldap"]
JWT = get_config()["jwt"]
DEBUG = get_config()["local"]

# Builds a router for the "auth" functionnality
auth_router = APIRouter()

####
# Credentials Checking / LDAP
####
def check_credentials(username, password):
    """
    Verifies the cerdentials for username/password
    using the ActiveDirectory from the ASN

    returns a boolean corresponding to the log
    status
    """
    if username in LDAP["superusers"]:
        logger.info(f"Superuser {username} has been logged in")
        return True

    ldap_server = f"{LDAP['host']}:{LDAP['port']}"
    ldap_user = f"{username}@domasn.local"

    try:
        server = ldap3.Server(ldap_server, get_info=ldap3.ALL)
        conn = ldap3.Connection(server, ldap_user, password, auto_bind=True)
        if conn.bind():
            return True
        else:
            return False
    except ldap3.core.exceptions.LDAPPasswordIsMandatoryError:
        logger.warning(f"Login failed for user {username}")
        return False
    except ldap3.core.exceptions.LDAPBindError:
        logger.warning(f"Login failed for user {username}")
        return False


def generate_token(user: User, duration: int = 120, **kwargs):
    """
    Generates a JWT token for a given user
    """
    current_time = datetime.utcnow()
    expire_time = current_time + timedelta(minutes=duration)

    return jwt.encode(
        {
            "username": user.username,
            "id_user": user.id_user,
            "fullname": user.fullname,
            "is_admin": user.is_admin,
            "exp": expire_time,
            **kwargs,
        },
        JWT["secret"],
        algorithm="HS256",
    )


##
# This function should be used as a Depends
# to obtain the user from the JWT token
# passed as a Bearer authentication token.
##
def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    From a given token (in string format),
    find the user concerned, or error out
    if the JWT token is invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    outdated_exception = credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The token provided is outdated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT["secret"], algorithms="HS256")

        return User(
            username=payload.get("username"),
            id_user=payload.get("id_user"),
            fullname=payload.get("fullname"),
            is_admin=payload.get("is_admin"),
        )
    except ExpiredSignatureError:
        raise outdated_exception
    except JWTClaimsError:
        raise credentials_exception
    except JWTError:
        raise credentials_exception
    except pydantic.error_wrappers.ValidationError:
        raise credentials_exception


def check_download_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The download token is invalid",
    )

    outdated_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The download token is outdated",
    )
    try:
        current_time = datetime.utcnow()
        payload = jwt.decode(token, JWT["secret"], algorithms="HS256")
        expiration = datetime.fromtimestamp(payload.get("exp"))
        if current_time >= expiration:
            raise ExpiredSignatureError
        else:
            print(f"{current_time} is LOWER than {expiration}", flush=True)
            return True
    except ExpiredSignatureError:
        raise outdated_exception
    except JWTClaimsError:
        raise credentials_exception
    except JWTError:
        raise credentials_exception
    except pydantic.error_wrappers.ValidationError:
        raise credentials_exception


def ask_full_name(username, password):
    """
    Request the LDAP Directory for the full name
    of the given user.
    """
    try:
        ldap_server = f"{LDAP['host']}:{LDAP['port']}"
        ldap_user = f"{username}@domasn.local"

        logger.debug(f"Requesting ldap fullname for {username}")
        server = ldap3.Server(ldap_server, get_info=ldap3.ALL)
        conn = ldap3.Connection(server, ldap_user, password, auto_bind=True)

        conn.search(
            search_base="DC=domasn,DC=local",
            search_filter=f"(&(objectClass=person)(sAMAccountName={username}))",
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
        )
        fullname = f"{conn.response[0]['raw_attributes']['name'][0]}"
        return fullname[2:-1]
    except ldap3.core.exceptions.LDAPPasswordIsMandatoryError:
        logger.warning(f"Full name finding failed for user {username}")
        return username
    except ldap3.core.exceptions.LDAPBindError:
        logger.warning(f"Full name finding failed for failed for user {username}")
        return username


user_example = User(
    id_user=1,
    username="admin",
    fullname="Administrator of Siance",
    is_admin=True,
)


@auth_router.post("/token", response_model=UserToken)
def post_authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
    if DEBUG:
        new_token = generate_token(user_example)
        return {"access_token": new_token, "user": user_example, "token_type": "bearer"}

    auth = check_credentials(form_data.username, form_data.password)

    if not auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        try:
            with SessionWrapper() as db:
                dbuser = (
                    db.query(SiancedbUser)
                    .filter(SiancedbUser.username == form_data.username)
                    .one()
                )
                user = User(
                    id_user=dbuser.id_user,
                    username=dbuser.username,
                    fullname=dbuser.fullname,
                    is_admin=dbuser.is_admin,
                )

            new_token = generate_token(user)

            log_action(
                SiancedbActionLog(id_user=user.id_user, action="USER_CONNECTION")
            )

            return {"access_token": new_token, "user": user, "token_type": "bearer"}

        except sqlalchemy.orm.exc.NoResultFound:
            logger.debug(f"Creating new user for {form_data.username}")
            fullname = ask_full_name(form_data.username, form_data.password)

            with SessionWrapper() as db:
                newUser = SiancedbUser(
                    username=form_data.username,
                    is_admin=False,
                    fullname=fullname,
                    creation_date=datetime.now(),
                )
                db.add(newUser)
                db.commit()

                user = User(
                    id_user=newUser.id_user,
                    username=newUser.username,
                    is_admin=newUser.is_admin,
                    fullname=newUser.fullname,
                )

            new_token = generate_token(user)
            log_action(SiancedbActionLog(id_user=user.id_user, action="USER_CREATION"))

            log_action(
                SiancedbActionLog(id_user=user.id_user, action="USER_CONNECTION")
            )

            return {"access_token": new_token, "user": user, "token_type": "bearer"}

        except sqlalchemy.orm.exc.MultipleResultsFound:
            logger.error(f"The username {form_data.username} is not unique ?!")
            raise HTTPException(
                status_code=401, detail="Multiple users with the same name"
            )


@auth_router.get("/download_token", response_model=DownloadToken)
def download_token(user: User = Depends(get_current_user)):
    return {"download_token": generate_token(user, 2, download=True)}


@auth_router.get("/me", response_model=UserToken)
def post_authenticate_refresh(user: User = Depends(get_current_user)):
    if DEBUG:
        return {
            "access_token": generate_token(user_example),
            "user": user_example,
            "token_type": "bearer",
        }

    logger.debug(f"Refreshing token for {user.username}")
    response = {
        "access_token": generate_token(user),
        "user": user,
        "token_type": "bearer",
    }

    log_action(SiancedbActionLog(id_user=user.id_user, action="USER_REFRESH"))
    return response
