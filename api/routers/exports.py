import logging
import itertools
from typing import Optional, List, Tuple
import json
from pydantic import parse_obj_as

import requests
import tempfile
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

import elasticsearch as es
import pandas as pd

from siancedb.elasticsearch.queries import build_paginated_query

from siancedb.elasticsearch.schemes import EFilter, EQuery

from siancedb.models import (
    SessionWrapper,
    SiancedbActionLog,
    SiancedbLabel,
    SiancedbSIv2LettersMetadata,
    log_action,
)

from siancedb.config import get_config

from .auth import get_current_user, check_download_token

from ..schemes import SianceCategory, SianceSubcategory

logger = logging.getLogger("siance-api-log")
ES = get_config()["elasticsearch"]


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


exports_router = APIRouter(prefix="/export", tags=["export"])


@exports_router.get("/search/{index}")  # response_model=StreamingResponse)
def export_letters(
    index: str,
    sentence: str,
    token: str,
    daterange: Tuple[str, str] = Depends(daterange_parameter),
    filters: EFilter = Depends(filter_parameters),
):
    assert index in ["letters", "demands"]

    if check_download_token(token) == False:
        return

    realq = build_paginated_query(
        EQuery(sentence=sentence, filters=filters, daterange=daterange),
        0,
        ["content"] if index == "letters" else [],
    )
    realq["size"] = 10000
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )
    res = conn.search(index=ES[index], body=realq)

    # FIXME: if no results fail!
    if index == "letters":
        columns = {
            "link": "Lettre",
            "date": "Date",
            "theme": "Thème",
            "pilot_entity": "Entité pilote",
            "site_name": "Site",
            "complementary_site_name": "URA",
            "interlocutor_name": "Exploitant",
            "sectors": "Secteur",
            #    "domains",
            #    "natures",
            "paliers": "Palier (INB)",
            "equipments_trigrams": "Systèmes (REP)",
            "isotopes": "Isotopes",
            #    "identifiers",
            "topics": "Sujets détectés",
            "demands_a": "Demandes A",
            "demands_b": "Demandes B",
        }
    else:
        columns = {
            "link": "Lettre",
            "date": "Date",
            "theme": "Thème",
            "site_name": "Site",
            "complementary_site_name": "URA",
            "interlocutor_name": "Exploitant",
            "sectors": "Secteur",
            # "domains",
            # "natures",
            "paliers": "Palier (INB)",
            "demand_type": "Type de demande",
            "content": "Demande",
            "summary": "Synthèse",
        }

    def build_hyperlink(doc):
        doc[
            "link"
        ] = '=HYPERLINK("http://si.asn.i2/webtop/drl/objectId/{objectId}","{name}")'.format(
            objectId=doc.get("siv2", ""), name=doc.get("name")
        )
        return doc

    df = pd.DataFrame(
        [build_hyperlink(doc["_source"]) for doc in res["hits"]["hits"]],
        columns=list(columns.keys()),
    ).rename(columns=columns)

    def rewrite_list(l):
        if isinstance(l, list):
            return ", ".join(str(x) for x in l)
        return l

    for col in columns.keys():
        df[columns[col]] = df[columns[col]].map(rewrite_list, na_action="ignore")

    # with tempfile.TemporaryFile() as fp:
    fp = tempfile.TemporaryFile()
    with pd.ExcelWriter(fp, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, engine="xlsxwriter", sheet_name=index)
        workbook = writer.book
        worksheet = writer.sheets[index]

        hypertext_format = workbook.add_format()
        hypertext_format.set_bold()
        hypertext_format.set_font_color("blue")
        worksheet.set_column("A:A", None, hypertext_format)
        worksheet.set_column("D:Z", 16)
        worksheet.set_column("A:C", 25)
        worksheet.set_column("D:Z", 16)

        if index != "letters":
            worksheet.set_column("J:K", 50)

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
        for col, value in enumerate(df.columns.values):
            worksheet.write(0, col, value, header)
    fp.seek(0)
    content = fp.read()

    response = StreamingResponse(
        (content for _ in [1]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response.headers["Content-Disposition"] = "attachment; filename=siance-export.xlsx"

    return response


@exports_router.get("/pdf/{pdf_id}")  # , response_model=StreamingResponse)
def redirect_pdf(pdf_id: str):
    try:
        r = requests.get(f"{ES['url']}:8001/pdf/{pdf_id}.pdf")
        response = StreamingResponse(
            (chunk for chunk in r.iter_content(chunk_size=1024) if chunk),
            media_type="application/pdf",
        )
        response.headers["Content-Disposition"] = f"attachment; filename={pdf_id}.pdf"
        return response
    except Exception as e:
        logger.error(f"Error while downloading pdf file {e}")
        raise HTTPException(
            status_code=404, detail=f"The file {pdf_id} was not available on the server"
        )


@exports_router.get("/referentials/{ref_id}")  # , response_model=StreamingResponse)
def redirect_referentials(ref_id: str):
    log_action(
        SiancedbActionLog(
            id_user=1,
            action="REFERENTIALS",
            details=json.dumps({"ref_id": ref_id}),
        )
    )
    try:
        r = requests.get(f"{ES['url']}:8001/referentials/{ref_id}.xlsx")
        response = StreamingResponse(
            (chunk for chunk in r.iter_content(chunk_size=1024) if chunk),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response.headers["Content-Disposition"] = f"attachment; filename={ref_id}.xlsx"
        return response
    except Exception as e:
        logger.error(f"Error while downloading pdf file {e}")
        raise HTTPException(
            status_code=404, detail=f"The file {ref_id} was not available on the server"
        )


@exports_router.get("/ontology", response_model=List[SianceCategory])
def fetch_ontology():
    with SessionWrapper() as db:
        return [
            {
                "category": key,
                "subcategories": [SianceSubcategory.from_orm(g) for g in group],
            }
            for key, group in itertools.groupby(
                sorted(
                    # pylint: disable=no-member
                    db.query(SiancedbLabel).all(),
                    key=lambda x: x.category,
                ),
                lambda x: x.category,
            )
        ]


@exports_router.get("/themes", response_model=List[str])
def fetch_themes():
    print("building themes")
    with SessionWrapper() as db:
        return [
            theme[0]
            for theme in db.query(SiancedbSIv2LettersMetadata.theme)
            .distinct(SiancedbSIv2LettersMetadata.theme)
            .all()
        ]
