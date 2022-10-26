from typing import List, Dict
from fastapi import APIRouter, Depends
import pydantic

from ..schemes import WatchQueries, EQuery
from  sqlalchemy.sql.expression import func
from siancedb.config import get_config
from .auth import get_current_user, check_download_token
import json
from siancedb.elasticsearch.queries import (
    build_not_paginated_query,
)
import elasticsearch as es
from pydantic import parse_obj_as
import pandas as pd
import tempfile
from fastapi.responses import StreamingResponse

import logging
logger = logging.getLogger("siance-api-log")

ES = get_config()["elasticsearch"]

def get_watch_results(watch: WatchQueries):
    """

    Args:
        watch (WatchQueries): a bunch of searches to query 

    Returns:
        Dict: formated like pandas dataframe records
    """
    if len(watch.queries) == 0:
        return
    
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )
    results = {}
    summary = []
    for query in watch.queries:
        realq = build_not_paginated_query(query, excludes=["content"], max_answer=200)
        res = conn.search(index=ES["letters"], body=realq)
        letters_response =  {
            "hits": [
                {
                    "Mots-clefs": query.sentence,
                    "SCORE": doc["_score"],
                    "Lettre": doc["_source"]["name"],
                    "Date": doc["_source"]["date"],
                    "Thème": doc["_source"]["theme"],
                    "Site": doc["_source"]["site_name"],
                    "Exploitant": doc["_source"]["interlocutor_name"],
                    "Commune": doc["_source"]["interlocutor_city"],
                    "SIRET": doc["_source"]["identifiers"][0:1],
                }
                for doc in res["hits"]["hits"]
            ],
            "total": res["hits"]["total"]["value"],
        }
        results[query.sentence] = pd.DataFrame(letters_response["hits"])
        summary.append({
            "Mots-clefs": query.sentence,
            "Période recherchée": query.daterange,
            "Résultats": letters_response["total"],
            "Site recherché": query.filters.site_name,
            "Exploitant recherché": query.filters.interlocutor_name,
            "Thème recherché": query.filters.theme,
            "Secteur recherché": query.filters.sectors,
          #  "Autres critères de recherches": query.filters
                #{
         #       filt: value for filt, value in dict(query.filters).items()
         #       if filt not in ["site_name", "interlocutor_name", "theme", "sectors"]
            #}
        })
        
    return {
        "results": pd.concat(results.values()).to_dict("records"),
        "summary": summary
    }

watch_router = APIRouter(
    prefix="/watch",
    tags=["watch"],
)

@watch_router.post("/queries", response_model=Dict)
def upload_watch(watch: WatchQueries) :
    return get_watch_results(watch)


@watch_router.get("/download")
def download_watch(token: str, watch):
    """
    Args:
        watch_string (str): a string formated like WatchQueries, containing a bunch of searches to query 
        token (str): a token to allow download

    Returns:
        StreamingResponse: a temporary file response
    """
    if check_download_token(token) == False:
        return
    
    queries = [parse_obj_as(EQuery, query) for query in json.loads(watch)["queries"]]
    watch_query = parse_obj_as(WatchQueries, {"queries": queries})
    watch_results = get_watch_results(watch_query)
    if watch_results is None:
        return
    results = pd.DataFrame.from_records(watch_results["results"])
    summary = pd.DataFrame.from_records(watch_results["summary"])

    # with tempfile.TemporaryFile() as fp:
    fp = tempfile.TemporaryFile()
    with pd.ExcelWriter(fp, engine="xlsxwriter") as writer:
        results.to_excel(writer, index=False, engine="xlsxwriter", sheet_name="Résultats")
        summary.to_excel(writer, index=False, engine="xlsxwriter", sheet_name="Critères")
        
        workbook = writer.book
        worksheet = writer.sheets["Résultats"]

        keywords_format = workbook.add_format()
        keywords_format.set_bold()
        worksheet.set_column("A:A", None, keywords_format)
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:D", 16)
        worksheet.set_column("C:C", 25)
        worksheet.set_column("E:Z", 25)

        header = workbook.add_format(
            {
                "bold": True,
                "text_wrap": True,
                "valign": "bottom",
                "fg_color": "#008080",
                "font_color": "#FFFFFF",
                "border": 1,
            }
        )
        for col, value in enumerate(results.columns.values):
            worksheet.write(0, col, value, header)
            
        worksheet = writer.sheets["Critères"]
        worksheet.set_column("A:Z", 25)
        for col, value in enumerate(summary.columns.values):
            worksheet.write(0, col, value, header)

    fp.seek(0)
    content = fp.read()

    response = StreamingResponse(
        (content for _ in [1]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response.headers["Content-Disposition"] = "attachment; filename=siance-recherches.xlsx"
    return response