"""

Consolidate information extracted from SiV2 using referential tables

"""
from siancedb.models import SiancedbThemeValorisation
from typing import Dict, Optional, List, Tuple, Iterable
import logging
import requests
from datetime import datetime, date, timedelta
import pandas as pd
import json
import unidecode


from pydantic import BaseModel

from siancebackend.letter_management.letter_cleaning import (
    process_french_yes_no,
    process_french_date,
    process_inspection_type,
    is_nullable,
    process_french_priority,
    process_string_array_safe,
    clean_entities,
)

from siancedb.models import (
    UNKNOWN,
    UNKNOWN_DATE,
)
from siancedb.config import get_config
from siancedb.pandas_writer import chunker
from siancebackend.pipe_logger import update_log_state

logger = logging.getLogger("siancebackend")



class SIv2SmartResponse(BaseModel):
    """
    A model for the _ideal string_ format
    of SIv2 Responses.
    As you can guess, it is NOT the format given
    by the API.
    """

    r_object_id: List[Optional[str]]
    exploitant: List[str]
    siret: List[str]
    nom_ura: List[str]
    site: List[str]
    num_nom_inb: List[str]
    inb_type_rep_ludd: List[str]
    natures: List[str]
    themes: List[str]
    date_env_let_suite: List[datetime]
    date_fin_inspect: List[datetime]
    date_deb_inspect: List[datetime]
    type_inspect: List[str]
    priorite: List[int]
    inspect_prog: List[bool]
    inspect_inop: List[bool]
    agent_pilotes: List[str]
    agent_copilotes: List[str]
    entite_resp: List[str]
    entite_pilote: List[str]


SIV2SinkToSources = {
    "themes": [
        "theme_principal",
        "theme_secondaire",
        "theme_complement",
        "theme_insp",
        "theme_inspect",
        "categorie_activite",
    ],
    "agent_copilotes": ["agent_copilotes", "agent_copilote"],
    "agent_pilotes": ["agent_charge", "agent_pilotes", "agent_charge_resp"],
    "entite_pilote": ["entite_pilote", "entite_pilotes", "entite_copilote", "entite_copilotes"],
    "entite_resp": ["entite_resp", "entite_responsable"],
    "priorite": ["inspect_priorite"],
    "natures": [
        "nature_activite",
        "domaines_activite",
        "domaine_activite",
        "nature_activite",
    ],
    "site": ["site", "raison_sociale_associee", "etablissement", "nom_usuel"],
    "inb_type_rep_ludd": ["inb_type_rep_ludd", "inb_type"],
}

SIV2Transforms = {
    "themes": process_string_array_safe,
    "date_env_let_suite": process_french_date,
    "date_fin_inspect": process_french_date,
    "date_deb_inspect": process_french_date,
    "agent_pilotes": process_string_array_safe,
    "agent_copilotes": process_string_array_safe,
    "entite_resp": clean_entities,
    "entite_pilote": clean_entities,
    "priorite": process_french_priority,
    "inspect_prog": process_french_yes_no,
    "inspect_inop": process_french_yes_no,
    "type_inspect": process_inspection_type
}

SIV2Defaults = {
    "date_env_let_suite": UNKNOWN_DATE,
    "date_fin_inspect": UNKNOWN_DATE,
    "date_deb_inspect": UNKNOWN_DATE,
    "priorite": False,
    "r_object_id": None,
    "inspect_prog": False,
    "inspect_inop": False,
}


def smart_eta(e):
    """
    Transforms SIv2 values into lists
    for uniform processing
    """
    if is_nullable(e):
        return []
    elif isinstance(e, str):
        return [e]
    elif isinstance(e, Iterable):
        return list(e)
    else:
        return [e]


def pick_field_metadata(siv2_metadata: Dict, field: str):
    answer = siv2_metadata.get(field, None)

    if is_nullable(answer) and "asn_interlocuteur" in siv2_metadata:
        answer = siv2_metadata["asn_interlocuteur"].get(field, None)

    if is_nullable(answer) and "asn_service" in siv2_metadata:
        answer = siv2_metadata["asn_service"].get(field, None)

    return smart_eta(answer)


def pick_fields_metadata(siv2_metadata: Dict, fields: List[str]):
    return [x for field in fields for x in pick_field_metadata(siv2_metadata, field)]


def smart_flatten(list_of_elems):
    l = []
    for e in list_of_elems:
        if isinstance(e, list):
            l.extend(e)
        else:
            l.append(e)
    return l


def build_smart_response(siv2response: Dict) -> SIv2SmartResponse:
    """
    This nice function takes a SIV2 response and
    extracts into a usable form all the metadata that we need.

    It uses the scheme SIv2SmartResponse and dictionaries
    SIV2SinkToSource/SIV2Transforms/SIV2Defaults to merge fields,
    process their values and put defaults where needed.
    """
    new_dict = {}

    for key in SIv2SmartResponse.__fields__.keys():

        # STEP 1: get values
        values = []
        # TODO: check again every field for metadata picking is the good one
        if key in SIV2SinkToSources:
            values = pick_fields_metadata(siv2response, SIV2SinkToSources[key])
        else:  # unique source of truth for this field
            values = pick_field_metadata(siv2response, key)

        # STEP 2: transform them
        transform = SIV2Transforms.get(key, lambda x: x)
        values = [
            transform(value) for value in values if value is not None
        ]  # value is None when the field was not found

        # STEP 3: flatten everything and put defaults
        flat = smart_flatten([value for value in values if not is_nullable(value)])
        if len(flat) == 0:
            new_dict[key] = smart_eta(SIV2Defaults.get(key, UNKNOWN))
        else:
            new_dict[key] = list(set(flat))
    return SIv2SmartResponse(**new_dict)


INB_SITE_COLUMN = "Nom du Site"
INB_CODE_COLUMN = "Code INB"
INB_NAME_COLUMN = "Nom INB"
INB_NATURE_COLUMN = "Nature INB"
LUDD_LEVEL_COLUMN = "Niveau LUDD"
CNPE_PALIER_COLUMN = "Palier CNPE"
CLASSIFICATION_COLUMN = "Classification"
OLD_CLASSIFICATION_COLUMN = "Classification précédente"
EXPLOITANT_COLUMN = "Exploitant"
USUAL_CNPE_NAME_COLUMN = "Nom usuel CNPE"
HOSPITAL_SITE_COLUMN = "Nom du Site"
SIRET_COLUMN = "Siret"
THEME_COLUMN = "theme_principal"
NATURES_COLUMN = "nature"
CLEANED_THEME_COLUMN = "theme_principal_corr"
SECTORS_COLUMN = "secteur"
DOMAINS_COLUMN = "domaine"

KEY_THEME_COLUMN = "key_theme"

INB_DF = pd.read_excel(
    get_config()["letters"]["INBs"], engine="openpyxl", index_col=None, dtype=str
)

HOSPITALS_DF = pd.read_excel(
    get_config()["letters"]["hospitals"], engine="openpyxl", index_col=None, dtype=str
)

THEMES_DF = pd.read_excel(
    get_config()["letters"]["themes"], engine="openpyxl", dtype=str
).dropna(subset=[THEME_COLUMN])
THEMES_DF[KEY_THEME_COLUMN] = THEMES_DF.apply(
    lambda row: unidecode.unidecode(row[THEME_COLUMN].lower().replace(" ", "")),
    axis=1,
)

with open(get_config()["letters"]["fix_siret"], "r") as f:
    FIX_SIRET = json.load(f)

class SIv2EnrichedResponse(BaseModel):
    # to the referentials
    # to correct possible mistakes
    # ex: La Hague INB116
    #     - Éculleville
    #     - Cherbourg-Octeville
    # -> two different cities (but same siret)
    # -> (different «inb names»)
    theme: List[str] = []
    sectors: List[str] = []
    domains: List[str] = []
    natures: List[str] = []
    siret: List[str] = []
    cnpe_name: List[str] = []
    site: List[str] = []
    criticity: List[str] = []
    palier: List[str] = []
    inb_num: List[str] = []
    inb_name: List[str] = []
    inb_nature: List[str] = []


def classification_to_REP_LUDD(classification: str) -> List[str]:
    if classification == "ex-INB" or classification == "" or classification == "Autre":
        return ["REP", "LUDD"]
    elif classification == "REP" or classification == "LUDD":
        return [classification]
    else:
        raise ValueError(f"Invalid classification {classification}")


def sectors_to_classification(sectors: List[str]) -> List[str]:
    classifs = set()
    if "LUDD" in sectors:
        classifs.add("LUDD")
        classifs.add("ex-INB")
        classifs.add("Autre")

    if "REP" in sectors:
        classifs.add("REP")
        classifs.add("ex-INB")
        classifs.add("Autre")

    return list(classifs)


def dataframe_matching_INBs(sr: SIv2SmartResponse):
    """
    Selects all the rows of the INB dataframe
    that match the current SIv2SmartResponse
    """
    checkable_sirets = [
        siret
        for possible_siret in sr.siret
        for siret in (possible_siret, fix_common_errors_cnpe_siret(possible_siret))
    ]

    checkable_site_name = [
        possible_name.lower().replace(" ", "") for possible_name in sr.site
    ]

    checkable_inb_num = [nom.lower().replace(" ", "") for nom in sr.num_nom_inb]
    checkable_inb_name = [nom.lower().replace(" ", "") for nom in sr.nom_ura]
    if "réacteur1" in checkable_inb_name or "réacteur2" in checkable_inb_name:
        checkable_inb_name.append("réacteurs1&2")
    if "réacteur3" in checkable_inb_name or "réacteur4" in checkable_inb_name:
        checkable_inb_name.append("réacteurs3&4")
    if "réacteur5" in checkable_inb_name or "réacteur6" in checkable_inb_name:
        checkable_inb_name.append("réacteurs5&6")

    checkable_classification = []

    # TEST IF THE is_rep_ludd property enables to decide
    siv2_rep = any(ans == "REP" for ans in sr.inb_type_rep_ludd)
    siv2_ludd = any(ans == "LUDD" for ans in sr.inb_type_rep_ludd)

    if siv2_rep:
        checkable_classification.extend(sectors_to_classification(["REP"]))
    if siv2_ludd:
        checkable_classification.extend(sectors_to_classification(["LUDD"]))

    checkable_classification = [u.lower() for u in checkable_classification]

    possibles_inb_df = INB_DF
         
    for (colname, condition) in [
        (SIRET_COLUMN, checkable_sirets),
        (INB_SITE_COLUMN, checkable_site_name),
        (CLASSIFICATION_COLUMN, checkable_classification),
        (INB_NAME_COLUMN, checkable_inb_name),
        (INB_CODE_COLUMN, checkable_inb_num),
    ]:
        # given a list of candidate values, keep only the rows of refenretial consistent with these candidates
        if len(condition) > 0 and colname != INB_SITE_COLUMN and colname != CLASSIFICATION_COLUMN:
            possibles_inb_df = possibles_inb_df[
                possibles_inb_df[colname]
                .str.lower()
                .str.replace(" ", "")
                .isin(condition)
            ]
        if len(condition) > 0 and colname == CLASSIFICATION_COLUMN:
            possibles_inb_df = possibles_inb_df[
                (possibles_inb_df[CLASSIFICATION_COLUMN]
                .str.lower()
                .str.replace(" ", "")
                .isin(condition)) |
                (possibles_inb_df[OLD_CLASSIFICATION_COLUMN]
                .str.lower()
                .str.replace(" ", "")
                .isin(condition))
            ]

    return possibles_inb_df


def dataframe_matching_themes(sr: SIv2SmartResponse):
    """
    Selects all the rows of the themes dataframe
    that match the current SIv2SmartResponse
    """
    return THEMES_DF[
        THEMES_DF[KEY_THEME_COLUMN].isin(
            [unidecode.unidecode(theme.lower().replace(" ", "")) for theme in sr.themes]
        )
    ]


def dataframe_matching_hospitals(sr: SIv2SmartResponse):
    """
    Selects all the rows of the hospitals dataframe
    that match the current SIv2SmartResponse
    """
    return HOSPITALS_DF[HOSPITALS_DF[SIRET_COLUMN].isin(sr.siret)]


def consolidate_smart_response(sr: SIv2SmartResponse) -> SIv2EnrichedResponse:
    # complete the data from SIv2 with the expert referentials for theme, INB and hospitals
    # for each field, produce the list of candidates in a manner that a candidate value for one field
    # is consitent with the candidates values for all other fields!

    output = SIv2EnrichedResponse()

    inbs_df = dataframe_matching_INBs(sr)
    hosp_df = dataframe_matching_hospitals(sr)
    them_df = dataframe_matching_themes(sr)

    # STEP 1: find the theme
    #         if possible
    if len(them_df) == 0:
        logger.critical(f"Using unknown theme(s) {sr.themes}")
    elif len(them_df) >= 1:
        # At this point, we may have extracted several themes, coming from the various theme fields in SIv2
        # By construction, the first item of the list if the "theme_principal", or the most important known theme
        # So to pick only one theme we can keep the first element of the list
        output.theme = smart_eta(them_df[CLEANED_THEME_COLUMN].iloc[0])

        tmp_sectors = them_df[SECTORS_COLUMN].iloc[0]
        if isinstance(tmp_sectors, str):
            output.sectors = tmp_sectors.split(",")
            output.sectors = [sector.strip() for sector in output.sectors]

        tmp_domains = them_df[DOMAINS_COLUMN].iloc[0]
        if isinstance(tmp_domains, str):
            output.domains = tmp_domains.split(",")
            output.domains = [domain.strip() for domain in output.domains]

        try:
            tmp_natures = them_df[NATURES_COLUMN].iloc[0]
            if isinstance(tmp_natures, str):
                output.natures = tmp_natures.split(",")
                output.natures = [nature.strip() for nature in output.natures]
        except:
            pass

        # Filter possible inbs _even further_ using the sectors
        inbs_df = inbs_df[
            inbs_df[CLASSIFICATION_COLUMN].isin(
                sectors_to_classification(output.sectors)
            ) |
            inbs_df[OLD_CLASSIFICATION_COLUMN].isin(
                sectors_to_classification(output.sectors)
            )
        ]

    # STEP 2:
    #  find if it is a hospital (if possible)
    if len(hosp_df) == 0:
        logger.debug(f"Response {sr} is not a hosptial")
    elif len(hosp_df) == 1:
        output.siret = smart_eta(hosp_df[SIRET_COLUMN].iloc[0])
        output.site = smart_eta(hosp_df[HOSPITAL_SITE_COLUMN].iloc[0])
        return output
    else:
        logger.debug(f"Unable to {sr} could be serveral hospitals")
        return output

    # STEP 3:
    #  we possibly are a INB
    #  let’s check that
    if len(inbs_df) == 0:
        output.siret = smart_eta(sr.siret[0])
        output.site = smart_eta(sr.site[0])
        return output
    else:
        classifications = list(inbs_df[CLASSIFICATION_COLUMN].dropna().unique())
        sectors = list(
            set(
                possible_sector
                for classification in classifications
                for possible_sector in classification_to_REP_LUDD(classification)
            )
        )

        if "LUDD" in output.sectors and "LUDD" not in sectors:
            output.sectors.remove("LUDD")
        elif "REP" in output.sectors and "REP" not in sectors:
            output.sectors.remove("REP")
        output.sectors = list(set(output.sectors).union(set(sectors)))

        output.cnpe_name = list(inbs_df[USUAL_CNPE_NAME_COLUMN].dropna().unique())
        output.site = list(
            inbs_df[INB_SITE_COLUMN].dropna().unique()
        )
        output.criticity = list(inbs_df[LUDD_LEVEL_COLUMN].dropna().unique())
        output.inb_name = list(inbs_df[INB_NAME_COLUMN].dropna().unique())
        output.inb_num = list(inbs_df[INB_CODE_COLUMN].dropna().unique())
        output.siret = list(inbs_df[SIRET_COLUMN].dropna().unique())
        output.palier = list(inbs_df[CNPE_PALIER_COLUMN].dropna().unique())
        output.inb_nature = list(inbs_df[INB_NATURE_COLUMN].dropna().unique())

        return output
    

def fix_common_errors_cnpe_siret(siret: str):
    siret = str(siret)
    if siret in FIX_SIRET:
        siret = str(FIX_SIRET[siret])
    return siret
