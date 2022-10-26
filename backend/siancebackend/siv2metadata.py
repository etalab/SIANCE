"""

Parse information extracted from SiV2 and store them in the SiV2 metadata SIANCE TABLE

"""
from typing import Dict, Union, List, Tuple, Iterable
import logging
import requests
from datetime import date, timedelta
import pandas as pd

from siancebackend.interlocutors import get_or_create_interlocutor

from siancebackend.letter_management.letter_cleaning import (
    extract_inspection,
)

from siancedb.models import (
    Session,
    SessionWrapper,
    SiancedbLetter,
    SiancedbSIv2LettersMetadata,
    SiancedbInterlocutor,
)
from siancedb.config import get_config
from siancedb.pandas_writer import chunker
from siancebackend.pipe_logger import update_log_state

from siancebackend.consolidate_metadata import (
    build_smart_response,
    consolidate_smart_response,
    pick_field_metadata,
    SIv2SmartResponse,
    SIv2EnrichedResponse,
)

SIV2 = get_config()["siv2"]
logger = logging.getLogger("siancebackend")


if SIV2["mock"]:
    try:
        mock = pd.read_pickle(SIV2["mock"])
        logger.info(f"Using mock extracted from {SIV2['mock']}")
    except:
        raise ValueError("Impossible to load the mockfile for SIV2")

def safe_fetch_siv2(name: str, text: str) -> Tuple[Dict, str]:
    """
    Tries to fetch the letter with the given name.
    Returns:
         None or a pair (siv2 response, real_name)
    """
    # if there was an error in the letter filename

    if SIV2["mock"]:
        try:
            return mock[mock.object_name == name].iloc[0], name
        except:
            return dict(), ""

    simeta = fetch_siv2(name)

    if simeta is None or not len(simeta):
        new_name = extract_inspection(text)
        if new_name != name:
            logger.error(
                f"There was an error in the filename {name}. The proper letter name was {new_name}"
            )
            new_simeta = fetch_siv2(new_name)
            if new_simeta is None or not len(simeta):
                logger.error(
                    f"Even under the name {new_name}, there was no entry in the SIv2"
                )
                return dict(), new_name
            simeta = new_simeta
            name = new_name
        else:
            logger.error(
                f"The name of the letter {name} was exact, but there is no entry in the SIv2"
            )
            return dict(), new_name

    return simeta, name


def fetch_siv2(name: str) -> (Dict or None):
    """
    Returns either None or the successful result extracted
    """
    params = {"instructName": name}
    try:
        logger.debug(f"Requesting the SIV2 with {name}")
        response = requests.post(
            url=f"{SIV2['url']}/asn-rest/rest/api/searchInstruct",
            headers={"Content-Type": "application/json"},
            json=params,
        ).json()
        if not response["successful"]:
            return dict()
        logger.debug(f"Sucessful SIV2 retrieval for {name}: {response}")
        return response["result"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Impossible to fetch SIV2 {name} due to network error {e}")
    except KeyError as v:
        logger.error(f"Impossible to fetch SIV2 {name}: {v}")



def build_siv2metadata_one_letter(
    letter: SiancedbLetter,
) -> Tuple[SiancedbSIv2LettersMetadata, SiancedbInterlocutor]:
    # if there is already siv2metadata or interlocutor in database, replace them
    siv2_response, correct_name = safe_fetch_siv2(letter.name, letter.text)
    id_letter = letter.id_letter
    try:
        with SessionWrapper() as db:
            letter.name = correct_name
            db.add(letter)
            db.commit()
    except:
        pass
    # siv2 object cannot be None, but interlocutor can be None (if no siret)
    siv2metadata, interlocutor = prepare_siv2metadata_interlocutor_one_letter(
        siv2_response
    )
    siv2metadata.id_metadata = id_letter
    return siv2metadata, interlocutor


def build_siv2metadata(db: Session):
    """
    Build metadata and interlocutors for all letters. Slow function for a complete rebuilding of database

    Args:
        db (Session): a Session to connect to the database

    """

    letters = db.query(SiancedbLetter).all()

    for letter in letters:
        try:
            siv2metadata, interlocutor = build_siv2metadata_one_letter(letter)
            db.add(siv2metadata)
            if interlocutor is not None:
                db.add(interlocutor)
            db.commit()
        except:
            pass




def refresh_metadata(db: Session):
    today = date.today()
    letters = db.query(SiancedbLetter).all()
    refresh_interval = timedelta(days=10)
    for letter in letters:
        if letter.last_touched + refresh_interval >= today:
            pass
        # if a letter has not been touched for `refresh_interval` days, request the SIv2 again
        else:
            siv2_response, correct_name = safe_fetch_siv2(letter.name, letter.text)
            print(interlocutor)
            si_meta, interlocutor = prepare_siv2metadata_interlocutor_one_letter(
                siv2_response
            )
            letter.name = correct_name
            if interlocutor is not None:
                letter.interlocutor = interlocutor
            db.add(letter)
            db.add(si_meta)
    db.commit()


def prepare_siv2metadata_interlocutor_one_letter(
    siv2_response: Dict,
) -> Tuple[SiancedbSIv2LettersMetadata, Union[SiancedbInterlocutor, None]]:

    # if the letter has no info in SIv2 (basically letters before 2010), save only the available info
    assert (
        siv2_response is not None
    ), "`prepare_siv2metadata_interlocutor_one_letter` can not parse empty siv2 "

    smart_response = build_smart_response(siv2_response)
    enriched_response = consolidate_smart_response(smart_response)

    def select_if_unique(x):
        if x is not None and len(x) == 1:
            return x[0]
        else:
            return None

    # Only consider fields we know the value with
    # absolute certainty !
    # -> this means some fields will become none due to « too many » values
    unique_smart = {
        key: select_if_unique(getattr(smart_response, key, None))
        for key in SIv2SmartResponse.__fields__.keys()
    }

    unique_enriched = {
        key: select_if_unique(getattr(enriched_response, key, None))
        for key in SIv2EnrichedResponse.__fields__.keys()
    }
    si_metadata = SiancedbSIv2LettersMetadata(
        theme=unique_enriched.get("theme", unique_smart.get("themes")),
        date_ins_end=unique_smart.get("date_fin_inspection"),
        date_mail=unique_smart.get("date_env_let_suite"),
        nb_days=0,  # TODO: calculate this ? useful ?
        responsible_entity=unique_smart.get("entite_resp"),
        pilot_entity=unique_smart.get("pilot_entity"),
        pilot_agents=smart_response.agent_pilotes,
        copilot_agents=smart_response.agent_copilotes,
        inspection_type=unique_smart.get("type_inspect"),
        was_programmed=unique_smart.get("inspect_prog"),
        was_unexpected=unique_smart.get("inspect_inop"),
        sectors=enriched_response.sectors,
        domains=enriched_response.domains,
        was_local=unique_smart.get("priorite"),
        priority=0,
        cnpe_name=unique_enriched.get("cnpe_name"),
        inb_name=unique_enriched.get("inb_name"),
        inb_num=unique_enriched.get("inb_num"),
        cnpe_palier=unique_enriched.get("palier"),
        ludd_criticity=unique_enriched.get("criticity"),
        inb_nature=unique_enriched.get("inb_nature"),
        site=unique_enriched.get("site", unique_smart.get("site")),
        doc_id=unique_smart.get("r_object_id"),
    )

    original_siret_siv2 = pick_field_metadata(
        siv2_response, "siret"
    )  # is a list (possibly empty)
    if not original_siret_siv2:
        original_siret_siv2 = None
    else:
        original_siret_siv2 = original_siret_siv2[0]
    # if there is not siret in consolidated data ("unique_enriched"), take the one of "siv2_response"
    return si_metadata, get_or_create_interlocutor(
        unique_enriched.get("siret", original_siret_siv2)
    )
