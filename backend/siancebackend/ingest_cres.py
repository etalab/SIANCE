"""

Process CRES events

"""
import json

from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from siancebackend import siv2metadata


from sqlalchemy.sql import func

from siancedb.config import get_config

from siancedb.models import (
    SessionWrapper,
    SiancedbCres,
    SiancedbDocument,
    SiancedbInterlocutor,
    UNKNOWN,
    UNKNOWN_DATE,
    SiancedbLabel,
    SiancedbLetter,
    SiancedbSIv2LettersMetadata,
)

from siancedb.elasticsearch.schemes import ECres
from siancedb.elasticsearch.management import bulk_insert

from siancebackend.letter_management.letter_cleaning import (
    process_french_date,
    is_nullable,
)


from siancebackend.consolidate_metadata import (
    smart_eta,
    smart_flatten,
    pick_fields_metadata,
    pick_field_metadata,
    fix_common_errors_cnpe_siret,
)

from siancebackend.interlocutors import get_or_create_interlocutor

##
# STEP 1:
#   Producing consistent output from unreliable data source (SIv2)
##


class SIv2SmartCres(BaseModel):
    """
    A model for the _ideal scheme_
    of a SIV2 CRES response.
    """

    r_object_id: List[str]
    r_object_name: List[str]
    r_folder_path: List[str]

    date: List[date]
    description: List[str]
    interlocuteur: List[str]
    natures: List[str]
    inbs: List[str]


SinkToSources = {
    "r_object_name": ["object_name"],
    "r_object_id": ["r_object_id"],
    "r_folder_path": ["r_folder_path"],
    "interlocuteur": [
        "etablissement",
        "site_concerne",
        "autre_site",
        "exploitant",
    ],
    "inbs": ["num_nom_inb", "unit_react_atelier"],
    "natures": [
        "nature_activite_esnp",
        "nat_act_imp",
        "nature_src_imp",
        "systeme_impact",
        "domaine_concerne",
        "fonction_impact",
    ],
    "description": [
        "description",
        "subject",
        "cres_action_comm",
        "critere_declaration",
        "observations",
    ],
    "date": [
        "date_comm",
        "date_deb_evenement",
        "date_rec_declaration",
        "date_rec_cres",
        "date_alerte_nat",
        "date_cloture",
        "date_detection",
        "date_info_asn",
        "date_fin_evenement",
        "date_declaration",
    ],
}

Transforms = {"date": lambda x: process_french_date(x, default=None)}


Defaults = {"description": "Aucune description", "date": UNKNOWN_DATE}


def build_smart_cres(siv2response: Dict) -> SIv2SmartCres:
    """
    This nice function takes a SIV2 response and
    extracts into a usable form all the metadata that we need.

    It uses the scheme SIv2SmartCres and dictionaries
    SinkToSources/Transforms/Defaults to merge fields,
    process their values and put defaults where needed.
    """
    new_dict = {}

    for key in SIv2SmartCres.__fields__.keys():

        # STEP 1: get values
        values = []
        if key in SinkToSources:
            values = pick_fields_metadata(siv2response, SinkToSources[key])
        else:  # unique source of truth for this field
            values = pick_field_metadata(siv2response, key)

        # STEP 2: transform them
        transform = Transforms.get(key, lambda x: x)
        values = [transform(value) for value in values]

        # STEP 3: flatten everything and put defaults
        flat = smart_flatten([value for value in values if not is_nullable(value)])
        if len(flat) == 0:
            new_dict[key] = smart_eta(Defaults.get(key, UNKNOWN))
        else:
            new_dict[key] = list(set(flat))
    return SIv2SmartCres(**new_dict)


##
#  STEP 2:
#     Enriching from consistent output using SiancedbInterlocutor
##


class SIv2EnrichedCres(BaseModel):
    siret: List[str]


def build_enriched_cres(
    cres: SIv2SmartCres,
    interlocutor_file="asn_interlocuteur.txt",
) -> SIv2EnrichedCres:
    p = cres.r_folder_path

    test_match = lambda x: any(
        ps.startswith(tuple(x.get("r_folder_path", []))) for ps in p
    )

    with open(interlocutor_file, "r") as content:
        jsons = (json.loads(line) for line in content.readlines())
        matchers = filter(test_match, jsons)
        potential_sirets = map(lambda x: x.get("siret", None), matchers)
        sirets = filter(lambda x: x, potential_sirets)
        c_sirets = map(fix_common_errors_cnpe_siret, sirets)
        first_3_sirets = (x for x, _ in zip(c_sirets, range(3)))

        return SIv2EnrichedCres(siret=list(first_3_sirets))


##
#  STEP 3:
#     Putting it all together to build one single CRES.
##


def select_first_date(dates: List[date]) -> date:
    if len(dates) > 0:
        return min(dates)
    else:
        return UNKNOWN_DATE.date()


def find_potential_interlocutor(sirets: List[str]):
    if len(sirets) == 0:
        raise ValueError("Expected at least one siret !")

    with SessionWrapper() as db:
        interlocutors = (
            db.query(SiancedbInterlocutor)
            .filter(SiancedbInterlocutor.siret.in_(sirets))
            .all()
        )

        for interlocutor in interlocutors:
            return interlocutor

        interlocutor = get_or_create_interlocutor(sirets[0])


def find_potential_cres(r_object_ids: List[str]):
    with SessionWrapper() as db:
        potential_cres = (
            db.query(SiancedbCres).filter(SiancedbCres.siv2.in_(r_object_ids)).all()
        )
        for cres in potential_cres:
            return cres
        return SiancedbCres()


def build_one_cres(
    siv2response: Dict,
    interlocutor_file="asn_interlocuteur.txt",
) -> Tuple[SiancedbCres, SiancedbInterlocutor]:

    smart_cres = build_smart_cres(siv2response)
    enriched_cres = build_enriched_cres(smart_cres, interlocutor_file=interlocutor_file)

    interlocutor = find_potential_interlocutor(enriched_cres.siret)
    site = None
    with SessionWrapper() as db:
        siv2_metadata, _ = db.query(
            SiancedbSIv2LettersMetadata, 
            SiancedbLetter
        )\
        .filter(SiancedbSIv2LettersMetadata.id_metadata == SiancedbLetter.id_letter)\
        .filter(SiancedbLetter.id_interlocutor == interlocutor.id_interlocutor)\
        .first()
        site = siv2_metadata.site
    cres = find_potential_cres(smart_cres.r_object_id)
    cres.site = site
    cres.id_interlocutor = interlocutor.id_interlocutor
    cres.siv2 = smart_cres.r_object_id[0]
    cres.name = smart_cres.r_object_name[0]
    cres.summary = " ### ".join(smart_cres.description)
    cres.date = select_first_date(smart_cres.date)
    cres.natures = smart_cres.natures
    cres.inb_information = smart_cres.inbs
    cres.last_touched = datetime.now()

    return (cres, interlocutor)


##
#  STEP 4:
#     Reading a dump file and figure out all the
#     updates that are necessary.
##
def last_update_time() -> date:
    with SessionWrapper() as db:
        rows = db.query(func.max(SiancedbCres.last_touched).label("last_touched")).all()
        for row in rows:
            if len(row) > 0 and row[0]:
                return row[0]
        return UNKNOWN_DATE.date()


def select_updatable_from_dump(dump_file: str) -> List[Dict]:
    last_touched = last_update_time()

    with open(dump_file, "r") as content:
        jsons = (json.loads(line) for line in content.readlines())

        return [
            cres
            for cres in jsons
            if last_touched == UNKNOWN_DATE
            or process_french_date(cres.get("r_modify_date")).date() >= last_touched
        ]


###
#  STEP 5:
#     document indexing
###
def index_cres(id_cres: List[int]):
    with SessionWrapper() as db:
        cres_res = (
            db.query(SiancedbCres).filter(SiancedbCres.id_cres.in_(id_cres)).all()
        )

        return bulk_insert(
            ECres(
                id_cres=cres.id_cres,
                id_interlocutor=cres.interlocutor.id_interlocutor,
                name=cres.name,
                siv2=cres.siv2,
                summary=cres.summary,
                natures=cres.natures,
                inb_information=cres.inb_information,
                date=cres.date,
                siret=cres.interlocutor.siret,
                interlocutor_name=cres.interlocutor.name,
                site_name=cres.interlocutor.main_site,
            )
            for cres in cres_res
            if cres.interlocutor is not None
        )
