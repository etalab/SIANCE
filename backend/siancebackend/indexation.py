#!/usr/bin/env python3

from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import logging

import json

from siancebackend.pipe_logger import update_log_state

from siancedb.elasticsearch.schemes import ELetter, EDemand

from siancedb.config import get_config

from siancedb.models import (
    Session,
    SessionWrapper,
    SiancedbIsotope,
    SiancedbLabel,
    SiancedbSection,
    SiancedbLetter,
    SiancedbDemand,
    SiancedbSIv2LettersMetadata,
    SiancedbPrediction,
    SiancedbInterlocutor,
    SiancedbTrigram,
)

logger = logging.getLogger("elastic-index")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/elastic_index.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# threshold so index only classes with sufficient level of decision function
DECISION_THRESH = 0.3

LabelDict = Dict[int, Tuple[str, str]]
InbDict = Dict[int, any]

with open(get_config()["geography"]["regions"], "r") as f:
    GEO = json.load(f)


def get_region_name(region_code: str):
    if region_code == "":
        region_code = "0"
    try:
        l = [
            f["properties"]["nom"]
            for f in GEO["features"]
            if f["properties"]["code"] == str(region_code)
        ]

        return l[0]
    except:
        return "INCONNU·E·S"


def labels_dict() -> LabelDict:
    logger.debug("Fetching label names from the database")
    with SessionWrapper() as db:
        labels = db.query(SiancedbLabel).all()
        #        return {label.id_label: [label.category, label.subcategory] for label in labels}
        return {
            label.id_label: {
                "name": label.subcategory,
                # some labels (typically many transverse labels) are not proposed for research but can be displayed in Observer. They are called "complementary"
                "complementary": not label.research,
                "is_rep": label.is_rep,
                "is_ludd": label.is_ludd,
                "is_npx": label.is_npx,
                "is_transverse": label.is_transverse,
            }
            for label in labels
        }


def filter_labels_predictions(
    labels: LabelDict,
    sectors: (List[str] or None),
    predictions: List[SiancedbPrediction],
) -> Tuple[LabelDict, List[SiancedbPrediction]]:
    """
    filter labels and predictions in index according to the sectors of the letter
    """
    if not sectors:  # sectors is None, or empty string, or empty list
        return labels, predictions
    if isinstance(sectors, str):
        sectors = [sectors]
    sectors = [sector.lower() for sector in sectors]
    filter_on = ["is_transverse"]
    if "rep" in sectors:
        filter_on.append("is_rep")
    if "ludd" in sectors:
        filter_on.append("is_ludd")
    if "npx" in sectors:
        filter_on.append("is_npx")
    filtered_labels = {}
    for key, value in labels.items():
        if any([value[filt] for filt in filter_on]):  # if any filter is True
            filtered_labels[key] = value

    return filtered_labels, [p for p in predictions if p.id_label in filtered_labels]


def prepare_topics(labels, predictions):
    return list(
        set(
            labels[p.id_label]["name"]
            for p in predictions
            if (p.decision_score is not None)
            and labels[p.id_label]["complementary"] == False
        )
    )


"""
def inb_descriptions() -> InbDict:
    logger.debug("Fetching INBs from the excel file")
    df = pd.read_excel(get_config()["letters"]["INBs"], engine="openpyxl")
    return {
        str(int(line["Siret"])): line
        for ind, line in df.iterrows()
        if ind < 1000 and "Siret" in line and line["Siret"] and not np.isnan(line["Siret"])
    }
"""


def build_documents(db: Session, id_model: int, pipe_logger=None):
    letters = db.query(SiancedbLetter).all()
    n_documents = db.query(SiancedbLetter).count()
    letters_count = 0
    labels = labels_dict()
    for letter in letters:
        letters_count += 1
        logger.debug(f"Indexing letter {letter.id_letter} (number {letters_count})")
        # refresh advancement every 100 steps. if there is less than 100 docs  to index, refresh it only at the last
        if letters_count == n_documents or letters_count % 100 == 0:
            update_log_state(
                pipe=pipe_logger, progress=letters_count / n_documents, step="indexing"
            )
        for doc in letter_generator(letter, labels, id_model):
            yield doc


def group_predictions_by_demands(
    demands: List[SiancedbDemand], predictions: List[SiancedbPrediction]
) -> List[Tuple[SiancedbDemand, List[SiancedbPrediction]]]:
    """
    Groups the predictions by demands.

    O(n * log(n)) but lists should be roughly sorted
    so we are much closer to linear time.
    """
    logger.debug("Grouping predictions")
    demands.sort(key=lambda x: x.start)
    predictions.sort(key=lambda x: x.start)

    L = []
    i = 0
    for d in demands:
        e = d.end
        Ld = []
        while i < len(predictions) and predictions[i].end <= e:
            if d.start <= predictions[i].start:
                Ld.append(predictions[i])
            i += 1
        L.append((d, Ld))
    return L


def group_predictions_demands_a_b(
    demands: List[SiancedbDemand], predictions: List[SiancedbPrediction]
):
    g_demands = group_predictions_by_demands(demands, predictions)
    demands_a = [x for x in g_demands if x[0].priority == 1]
    demands_b = [x for x in g_demands if x[0].priority == 2]
    return demands_a, demands_b


def get_palier_or_criticity(palier: str, criticity: str) -> List:
    if palier is None and criticity is None:
        return []
    elif palier is not None and criticity is None:
        return [palier]
    else:
        return [criticity]


def extract_summary(text: str, sections: List[SiancedbSection]) -> str:
    for s in sections:
        if s.priority == 0:
            return text[s.start : s.end]
    return ""


def prepare_interlocutor_fields(interlocutor):
    if interlocutor is not None:
        identifiers = [interlocutor.siret]
        region_code = interlocutor.region
        point_gps = {"lat": interlocutor.lat or 0, "lon": interlocutor.lon or 0}
        interlocutor_name = interlocutor.name
        city = interlocutor.city
        id_interlocutor = interlocutor.id_interlocutor
        main_site = interlocutor.main_site
    else:
        identifiers = []
        region_code = ""
        interlocutor_name = ""
        city = ""
        id_interlocutor = ""
        point_gps = {"lat": 0, "lon": 0}
        main_site = ""
    region_name = get_region_name(region_code)
    return (
        identifiers,
        interlocutor_name,
        id_interlocutor,
        main_site,
        city,
        region_name,
        region_code,
        point_gps,
    )


def prepare_metadata_fields(metadata_si, letter):
    if metadata_si is not None:
        sectors = metadata_si.sectors
        siv2_link = (
            metadata_si.doc_id
        )  # needed to deliver the link SIv2 to the frontend
        date = (
            metadata_si.date_ins_end if metadata_si.date_ins_end else letter.sent_date
        )
        inb_name = metadata_si.inb_name
        theme = metadata_si.theme
        domains = metadata_si.domains
        inb_natures = [metadata_si.inb_nature] if metadata_si.inb_nature else []
        paliers = get_palier_or_criticity(
            metadata_si.cnpe_palier, metadata_si.ludd_criticity
        )
        pilot_entity = metadata_si.pilot_entity
        responsible_entity = metadata_si.responsible_entity
        site_name = metadata_si.site
    else:
        sectors = ""
        siv2_link = ""
        date = letter.sent_date
        inb_name = ""
        theme = ""
        domains = ""
        inb_natures = ""
        paliers = ""
        pilot_entity = ""
        responsible_entity = ""
        site_name = ""
    return (
        theme,
        site_name,
        inb_name,
        date,
        siv2_link,
        sectors,
        domains,
        inb_natures,
        paliers,
        pilot_entity,
        responsible_entity,
    )


def letter_generator(letter: SiancedbLetter, labels: LabelDict, id_model: int):
    logger.debug(f"Building letter {letter.name}")

    logger.debug(f"Letter date {letter.sent_date} {type(letter.sent_date)}")
    logger.debug(f"Letter interlocutor {letter.interlocutor}")
    logger.debug(f"Letter predictions {letter.predictions}")
    logger.debug(f"Letter metadata {letter.metadata_si}")
    logger.debug(f"Letter demands {letter.demands}")

    predictions: List[SiancedbPrediction] = (
        letter.predictions_dyn.filter(SiancedbPrediction.id_model == id_model)
        .filter(SiancedbPrediction.decision_score > DECISION_THRESH)
        .all()
    )
    interlocutor: SiancedbInterlocutor = letter.interlocutor
    metadata_si: SiancedbSIv2LettersMetadata = letter.metadata_si
    demands: List[SiancedbDemand] = letter.demands
    trigrams: List[SiancedbTrigram] = letter.trigrams
    isotopes: List[SiancedbIsotope] = letter.isotopes
    sections: List[SiancedbSection] = letter.sections
    summary = extract_summary(letter.text, sections)

    (
        identifiers,
        interlocutor_name,
        id_interlocutor,
        main_site,
        city,
        region_name,
        region_code,
        point_gps,
    ) = prepare_interlocutor_fields(interlocutor)
    (
        theme,
        inb_site,
        inb_name,
        date,
        siv2,
        sectors,
        domains,
        inb_natures,
        paliers,
        pilot_entity,
        responsible_entity,
    ) = prepare_metadata_fields(metadata_si, letter)

    if inb_site:
        site_name = [inb_site]
    elif main_site:
        site_name = [main_site]
    else:
        site_name = []

    labels, predictions = filter_labels_predictions(labels, sectors, predictions)
    demands_a, demands_b = group_predictions_demands_a_b(demands, predictions)
    topics = prepare_topics(labels, predictions)

    eletter = ELetter(
        id_letter=letter.id_letter,
        id_interlocutor=id_interlocutor or None,
        name=letter.name,
        content=letter.text,
        date=date,
        siv2=siv2,
        site_name=site_name,
        complementary_site_name=inb_name
        or None,  # field not used for filters/research but displayed in cards
        interlocutor_name=interlocutor_name or None,
        interlocutor_city=city or None,
        identifiers=identifiers,
        theme=theme,
        sectors=sectors or [],
        domains=domains or [],
        natures=inb_natures or [],
        paliers=paliers or [],
        pilot_entity=pilot_entity,
        resp_entity=responsible_entity,
        demands_a=len(demands_a),
        demands_b=len(demands_b),
        demands_a_topics=[],
        demands_b_topics=[],
        observations_topics=[],
        topics=topics,
        complementary_topics=[],
        low_confidence_topics=[],
        equipments_trigrams=list(trig.trigram for trig in trigrams),
        equipments_full_names=list(trig.trigram_full_name for trig in trigrams),
        isotopes=list(
            str(isotope.mass_number) + isotope.symbol for isotope in isotopes
        ),
        point=point_gps,
        region_code=region_code or "",
        region=region_name,
    )

    for (d, preds) in demands_a:
        yield build_demand(d, preds, eletter, labels, summary)
    for (d, preds) in demands_b:
        yield build_demand(d, preds, eletter, labels, summary)

    yield eletter


def priority_to_text(p: int) -> str:
    if p == 1:
        return "Demande d'action corrective"
    elif p == 2:
        return "Demande d'information complémentaire"
    elif p == 3:
        return "Observation"
    else:
        return "Générique"


def build_demand(
    demand: SiancedbDemand,
    predictions: List[SiancedbPrediction],
    letter: ELetter,
    labels: LabelDict,
    summary: str,
) -> EDemand:
    assert demand.id_letter == letter.id_letter
    logger.debug(f"Building demand {demand.id_demand} from {letter.name}")

    start = demand.start

    end = demand.end
    return EDemand(
        id_letter=demand.id_letter,
        id_demand=demand.id_demand,
        id_interlocutor=letter.id_interlocutor,
        name=letter.name,
        content=f"{letter.content[start: end + 1]}",
        summary=summary,
        date=letter.date,
        site_name=letter.site_name,
        complementary_site_name=letter.complementary_site_name,
        interlocutor_name=letter.interlocutor_name,
        interlocutor_city=letter.interlocutor_city,
        identifiers=letter.identifiers,
        theme=letter.theme,
        sectors=letter.sectors,
        domains=letter.domains,
        natures=letter.natures,
        paliers=letter.paliers,
        pilot_entity=letter.pilot_entity,
        resp_entity=letter.resp_entity,
        demand_type=priority_to_text(demand.priority),
        topics=list(
            set(
                labels[p.id_label]["name"]
                for p in predictions
                if (p.decision_score is not None and p.decision_score > DECISION_THRESH)
                and labels[p.id_label]["complementary"] == False
            )
        ),
        complementary_topics=list(
            set(
                labels[p.id_label]["name"]
                for p in predictions
                if (p.decision_score is not None and p.decision_score > DECISION_THRESH)
                and labels[p.id_label]["complementary"] == True
            )
        ),
        low_confidence_topics=list(
            set(
                labels[p.id_label]["name"]
                for p in predictions
                if (
                    p.decision_score is not None and p.decision_score <= DECISION_THRESH
                )
            )
        ),
        equipments_trigrams=[],
        equipments_full_names=[],
        isotopes=[],
        point=letter.point,
        region=letter.region,
        region_code=letter.region_code,
    )
