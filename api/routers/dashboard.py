from fastapi import APIRouter, Depends, Query

import elasticsearch as es
import json

from siancedb.elasticsearch.queries import (
    build_geo_query,
    GEO,
)

from siancedb.elasticsearch.schemes import EQuery
from typing import Tuple, Optional, Dict
from pydantic import parse_obj_as
from siancedb.elasticsearch.schemes import EFilter, EQuery

from ..visualize.visualize import (
    parse_elastic_response,
    get_dashboards_hist
)

from siancedb.models import SessionWrapper, SiancedbInb, SiancedbInterlocutor

from siancedb.config import get_config

from .auth import get_current_user

from .suggestions import suggest_generic


from ..schemes import DashboardResponse

ES = get_config()["elasticsearch"]

def daterange_parameter(
    daterange: Optional[str] = Query(
        None,
        description="A date range in years to limit search",
        example="[2010, 2020]",
    )
):
    try:
        if daterange:
            return parse_obj_as(Tuple[int, int], json.loads(daterange))
        else:
            return None
    except:
        return None

def filter_parameters(
    filters: Optional[str] = Query(
        None,
        description="JSON encoded object containing filters",
        example="""{ "topics": ["incendie", "agressions"] }""",
    )
):
    if filters is None:
        return dict()

    try:
        return parse_obj_as(EFilter, json.loads(filters))
    except:
        ## FIXME: need to use the "fastapi validation" errors!
        raise ValueError("mmm")


dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)



@dashboard_router.post("/histograms")
def dashboard_letters(
    query: EQuery,
) -> Dict[str, Dict]:
    
    df = parse_elastic_response(
        ES,
        query
    )
    return get_dashboards_hist(df)


@dashboard_router.post("/letters_carto", response_model=DashboardResponse)
def dashboard_letters(query: EQuery):

    # TODO: count the number for each INB... this is
    # done in the elasticsearch query !
    # we should add a parameter
    # siret_to_watch ^^

    with SessionWrapper() as db:
        inb_list = (
            db.query(SiancedbInb, SiancedbInterlocutor)
            .filter(SiancedbInterlocutor.siret == SiancedbInb.siret)
            .all()
        )
        ludd_and_rep = [
            {
                "id_interlocutor": interlocutor.id_interlocutor,
                "id_inb": inb.id_inb,
                "point": [
                    interlocutor.lat or 0,
                    interlocutor.lon or 0,
                ],
                "name": interlocutor.name,
                "code_inb": inb.code_inb,
                "palier": inb.palier,
                "ludd_level": inb.ludd_level,
                "site_name": inb.site_name,
                "cnpe_name": inb.cnpe_name,
                "inb_name": inb.inb_name,
                "inb_nature": inb.inb_nature,
                "is_seashore": inb.is_seashore,
            }
            for inb, interlocutor in inb_list
        ]

    realq = build_geo_query(
        query, id_interlocutors=[inb["id_interlocutor"] for inb in ludd_and_rep]
    )
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )
    res = conn.search(index=ES["letters"], body=realq)

    r = res["aggregations"]

    return {
        "suggest_letters": suggest_generic(query, "letters"),
        "suggest_demands": suggest_generic(query, "demands"),
        "dashboard": {
            "regions": {
                d["properties"]["code"]: {
                    "name": d["properties"]["nom"],
                    "code": d["properties"]["code"],
                    "count": r[d["properties"]["code"]]["doc_count"],
                    "nb_interlocutors": r[d["properties"]["code"]]["interlocutors"][
                        "value"
                    ],
                }
                for d in GEO["features"]
            },
            "ludd_and_rep": [],
        },
    }
