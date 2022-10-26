import time
import sqlalchemy
from siancedb.models import SiancedbInterlocutor, SessionWrapper
import requests
import logging

logger = logging.getLogger("interlocutors")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/interlocutors.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


def get_latlon_interlocutor(zip_code):
    """
    Request GEO.API.GOUV.FR to get city name and geojson coordinates from French code postal
    """
    zip_code = str(zip_code)
    url = "https://geo.api.gouv.fr/communes?codePostal={}&fields=centre,codeRegion&format=json&geometry=centre".format(
        zip_code
    )
    response = requests.get(url).json()[0]
    return {
        "city": response["nom"],
        "region": response["codeRegion"],
        "geojson": response["centre"],
    }


def get_insee_information(siret: str):
    """
    Request INSEE API SIRENE to get `etablissement` siren, siret, name, zip code

    Args:
        siret (str): a string giving the SIRET of a local company office (French: "établissement")

    Returns:
        dict: commercial (SIREN, name, main site) and geographical (zip code) information about the company
    """
    def get_api_response(siret: str, token: str):
        url = "https://api.insee.fr/entreprises/sirene/V3/siret/{}".format(siret)
        return requests.get(url, headers={"Authorization": "Bearer {}".format(token)})

    token = get_memoized_token("token")
    response = get_api_response(siret, token)
    if response.status_code == 401: # unauthorized token
        token  = get_token("token")
        get_memoized_token.set("token", token)
        response = get_api_response(siret, token)
        
    # in case of error 429 (too many requests in a timelapse), wait a bit before requesting again
    while response.status_code == 429:
        time.sleep(5)
        response = get_api_response(siret, token)

    logger.debug(f"In request {siret}, response is {response}.")

    if response.status_code == 404:
        logger.debug(
            f"The siret {siret} is not registered at INSEE. This interlocutor is unknown "
        )
        return None

    try:
        # gather information about the local company office (French: établissement) matching the SIRET
        response = response.json()["etablissement"]
    except KeyError:
        logger.error(
            f"The format of INSEE API appears to have changed. Please look at INSEE doc to fix it quickly"
        )
        return None

    insee_information = {
        "siren": response["siren"],
        "siret": response["siret"],
        "name": response["uniteLegale"]["denominationUniteLegale"],
        "postal_code": response["adresseEtablissement"]["codePostalEtablissement"],
    }
    # if the most recent `etablissement` in INSEE response (etablissement with index 0)
    # is the current `etablissement` (no end date, ie "dateFin" is None), then save the `etablissement` name
    if (
        "periodesEtablissement" in response
        and response["periodesEtablissement"][0]["dateFin"] is None
    ):
        main_site = response["periodesEtablissement"][0]["enseigne1Etablissement"]
        insee_information["main_site"] = main_site
    return insee_information


def memoize(f):
    """
    Useful function used as decorator to "memoize" objets (to avoid request the same objects too often)

    In pratice, used to memorize and return an `interlocutor` instance thanks to a SIRET while filling the interlocutors table
    TODO: add limit in time of the memoization so that it does not return too long the old info
    about a company if its info changes

    Args:
        f (function): The function where to apply memoization

    Returns:
        [type]: [description]
    """
    memo = {}

    def helper(*x):
        if not x[0] in memo:
            memo[x[0]] = f(*x)
        return memo[x[0]]

    return helper


class MemoizeToken:
    def __init__(self, f) -> None:
        self.f = f
        self.memo = {}
        
    def __call__(self, *args):
        if not args in self.memo:
            self.memo[args] = self.f(*args)
        #Warning: You may wish to do a deepcopy here if returning objects
        return self.memo[args]
    
    def set(self, args, value):
        self.memo[args] = value

def get_token(desc: str="token"):
    # our credentials on INSEE API website
    credentials = "ZThrZzRsaVpXdzlXQlA4NFZmWEg0amUySmFFYTpCU2FYTGZZZWVreUZfaTlkbDBoWmhJZTlxTFVh"
    # ask a token to request SIRENE
    token = requests.post(
        "https://api.insee.fr/token",
        data={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {credentials}"},
        verify=True,
    ).json()["access_token"]

    return token

get_memoized_token = MemoizeToken(get_token)

@memoize
def get_or_create_interlocutor(siret: str):
    """
    Giving the SIRET of a company, load useful information about it (name, address, zip code, etc.),
    and create and save in database a `SiancedbInterlocutor` instance. If such an instance already exists, simply return it

    Args:
        siret (str): a string giving the SIRET of a local company office (French: "établissement")
        db (Session): a Session to connect to the database

    Raises:
        ValueError: if there is several interlocutors for the same SIRET.
           If interlocutors are created through this function, such an inconsistency cannot occur.

    Returns:
        SiancedbInterlocutor: an interlocutor instance whose SIRET matches the input
    """
    siret = str(siret)
    try:
        with SessionWrapper() as db:
            return (
                db.query(SiancedbInterlocutor)
                .filter(SiancedbInterlocutor.siret == siret)
                .one()
            )
    except sqlalchemy.orm.exc.NoResultFound:
        interlocutor = prepare_interlocutor(siret)
        if interlocutor is not None:
            with SessionWrapper() as db:
                obj = SiancedbInterlocutor(**interlocutor)
                db.add(obj)
                db.commit()
                return obj
        else:
            return None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        raise ValueError(f"The database is inconsistent: multiple fields for {siret}")


def prepare_interlocutor(siret: str):
    """
    For a given siret, gather the interlocutor information using the API from `insee` and the API from `geo.api.gouv.fr`.
    The gathered information is returned in a dictionary

    In the case the company site is not in France, the API does not work, and the location fields remain at None

    Args:
        siret (str): a string giving the SIRET of a local company office (French: "établissement")

    Returns:
        dict: commercial (SIREN, name, main site) and geographical (city, zip code, GPS coords) information about the company
    """
    siret = str(siret)
    interlocutor = get_insee_information(siret)
    if interlocutor is None:
        return None
    else:
        try:
            latlon = get_latlon_interlocutor(interlocutor["postal_code"])
            interlocutor["city"] = latlon["city"]
            interlocutor["lat"] = latlon["geojson"]["coordinates"][1]
            interlocutor["lon"] = latlon["geojson"]["coordinates"][0]
            interlocutor["region"] = latlon["region"]
        except Exception:  # exception a bit broad to catch exception from KeyError and from api.gouv.fr API
            logger.info(
                f"There is no valid French postal code for the company with siret {siret}"
            )
            interlocutor["city"] = None
            interlocutor["lat"] = None
            interlocutor["lon"] = None
            interlocutor["postal_code"] = None
            interlocutor["region"] = None
        return interlocutor
