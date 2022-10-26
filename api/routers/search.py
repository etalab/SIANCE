from typing import List

from datetime import date

from fastapi import APIRouter, Depends

import elasticsearch as es

from siancedb.elasticsearch.queries import (
    build_paginated_query,
    build_paginated_cres_query,
)

from siancedb.elasticsearch.schemes import EQuery, ECres

from siancedb.models import (
    SiancedbActionLog,
    log_action,
    SessionWrapper,
    SiancedbCres,
    SiancedbInterlocutor,
)

from siancedb.config import get_config

from .auth import get_current_user

from ..schemes import (
    User,
    CRES,
    DemandsSearchResponse,
    LettersSearchResponse,
    CresSearch,
)

ES = get_config()["elasticsearch"]


search_router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_current_user)],
)


def safe_highlight(d):
    if "highlight" in d:
        return list(set(x for k, v in d["highlight"].items() for x in v))
    else:
        return []


@search_router.post("/cres")  # , response_model=List[CRES])
def answer_cres(query: EQuery, page: int, user: User = Depends(get_current_user)):
    realq = build_paginated_cres_query(
        query,
        page,
        """
        [
            "r_object_id",
            "date_deb_evenement",
            "date_incident",
            "site_concerne",
            "etablissement",
            "observations",
            "description",
            "object_name",
        ],
        """,
    )
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )

    res = conn.search(index=ES["cres"], body=realq)
    log_action(
        SiancedbActionLog(
            id_user=user.id_user,
            action="SEARCH_CRES",
            details=query.json(),
        )
    )

    try:
        return [
            {
                "id_cres": doc["_source"]["object_name"],
                "content": doc["_source"]["description"],
                "date": doc["_source"].get(
                    "date_deb_evenement",
                    doc["_source"].get("date_incident", date.today()),
                ),
                "site_name": doc["_source"]["site_concerne"],
                "siv2": doc["_source"]["r_object_id"],
            }
            for doc in res["hits"]["hits"]
        ]
    except KeyError as e:
        print("exception occured")
        print(res)
        print(realq)
        print(e)
        return []


@search_router.post("/letters", response_model=LettersSearchResponse)
def answer_letters(query: EQuery, page: int, user: User = Depends(get_current_user)):
    realq = build_paginated_query(query, page, ["content"])
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )

    res = conn.search(index=ES["letters"], body=realq)
    log_action(
        SiancedbActionLog(
            id_user=user.id_user,
            action="SEARCH",
            details=query.json(),
        )
    )

    try:
        return {
            "hits": [
                {
                    "doc_id": doc["_id"],
                    "highlight": safe_highlight(doc),
                    "_source": doc["_source"],
                    "_score": doc["_score"],
                }
                for doc in res["hits"]["hits"]
            ],
            "total": res["hits"]["total"]["value"],
        }
    except Exception as e:
        print("exception occured")
        print(res)
        print(realq)
        print(e)
        return res


@search_router.post("/demands", response_model=DemandsSearchResponse)
def answer_demands(
    query: EQuery,
    page: int,
    user: User = Depends(get_current_user),
):
    realq = build_paginated_query(query, page, [])
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )

    log_action(
        SiancedbActionLog(
            id_user=user.id_user,
            action="SEARCH",
            details=query.json(),
        )
    )

    res = conn.search(index=ES["demands"], body=realq)
    try:
        return {
            "hits": [
                {
                    "doc_id": doc["_id"],
                    "highlight": safe_highlight(doc),
                    "_source": doc["_source"],
                    "_score": doc["_score"],
                }
                for doc in res["hits"]["hits"]
            ],
            "total": res["hits"]["total"]["value"],
        }
    except Exception as e:
        print(res)
        print(realq)
        print(e)
        return res


@search_router.post("/interlocutor/cres", response_model=List[ECres])
def search_cres_by_interlocutor(
    cres_search: CresSearch, user: User = Depends(get_current_user)
):
    print(cres_search)
    with SessionWrapper() as db:

        query = db.query(SiancedbCres, SiancedbInterlocutor).filter(
            SiancedbCres.id_interlocutor == SiancedbInterlocutor.id_interlocutor
        )

        if cres_search.id_interlocutor:
            query = query.filter(
                SiancedbCres.id_interlocutor.in_(cres_search.id_interlocutor),
            )

        if cres_search.interlocutor_name:
            query = query.filter(
                SiancedbInterlocutor.name.in_(cres_search.interlocutor_name),
            )

        if cres_search.site_name:
            query = query.filter(
                (SiancedbInterlocutor.main_site.in_(cres_search.site_name)) |
                (SiancedbCres.site.in_(cres_search.site_name))
            )

        query = query.order_by(SiancedbCres.date.desc()).limit(10)

        return [
            ECres(
                id_cres=cres.id_cres,
                id_interlocutor=interlocutor.id_interlocutor,
                name=cres.name,
                siv2=cres.siv2,
                summary=cres.summary,
                natures=cres.natures,
                inb_information=cres.inb_information,
                date=cres.date,
                siret=interlocutor.siret,
                interlocutor_name=interlocutor.name,
                site_name=interlocutor.main_site,
            )
            for cres, interlocutor in query.all()
        ]
