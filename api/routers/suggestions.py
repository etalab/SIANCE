from typing import List, Dict
import numpy as np
from fastapi import APIRouter, Depends

import itertools
import elasticsearch as es

from siancedb.elasticsearch.queries import (
    build_feedback_query,
    build_field_values_query,
    build_fields_values_query,
    build_instant_query,
)

from siancedb.elasticsearch.schemes import EQuery, FieldValuesPost

from siancedb.config import get_config

from .auth import get_current_user

from ..schemes import (
    Suggestion,
    SuggestResponse,
    SuggestFiltersResponse,
)

ES = get_config()["elasticsearch"]


suggestion_router = APIRouter(
    prefix="/suggestion",
    tags=["suggestion"],
    dependencies=[Depends(get_current_user)],
)


def parse_composite_suggestion(bucket):
    value = bucket["key"]
    return [
        Suggestion(id=subbucket["key"], value=value, count=subbucket["doc_count"])
        for subbucket in bucket["inner_agg"]["buckets"]
    ]


def parse_simple_suggestion(bucket):
    if isinstance(bucket["key"], str):
        return Suggestion(value=bucket["key"], count=bucket["doc_count"])
    elif isinstance(bucket["key"], int):
        return Suggestion(id=bucket["key"], count=bucket["doc_count"])
    else:
        return Suggestion(
            value=bucket["key"]["value"],
            count=bucket["doc_count"],
            id=bucket["key"]["id"],
        )


@suggestion_router.post("/letters", response_model=SuggestResponse)
def suggest_letters(query: EQuery):
    return suggest_generic(query, "letters")


@suggestion_router.post("/demands", response_model=SuggestResponse)
def suggest_demands(query: EQuery):
    return suggest_generic(query, "demands")


def suggest_generic(query: EQuery, index: str):
    fields = SuggestFiltersResponse.__fields__.keys()
    realq = build_feedback_query(query, fields)
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )
    res = conn.search(index=ES[index], body=realq)

    try:
        return {
            "dym": [
                Suggestion(value=sentence)
                for what_is_this in res["suggest"]["dym"]
                for sentence in what_is_this["options"]
            ],
            "date": [
                [bucket["key"], bucket["doc_count"]]
                for bucket in res["aggregations"]["date_aggregation_filtered"][
                    "date_aggregation"
                ]["buckets"]
            ],
            **{
                suggestion_name: [
                    Suggestion(value=suggestion["key"], count=suggestion["doc_count"])
                    for suggestion in res["aggregations"][
                        f"{suggestion_name}_filtered"
                    ][suggestion_name]["buckets"]
                    if suggestion["key"] != ""
                ]
                for suggestion_name in fields
            },
        }
    except KeyError:
        return res


@suggestion_router.get("/field_values", response_model=List[str])
def field_values(field: str, value: str):

    realq = build_field_values_query(field, value)
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )

    res = conn.search(index=ES["letters"], body=realq)

    try:
        return [
            Suggestion(value=bucket["text"])
            for bucket in res["aggregations"][field]["buckets"]
        ]
    except:
        return res


@suggestion_router.post("/field_values", response_model=Dict[str, List[Suggestion]])
def field_values(request: FieldValuesPost):

    realq = build_fields_values_query(request)
    # doc June 2021
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )

    res = conn.search(index=ES["letters"], body=realq)

    try:
        composite_suggestions = {
            field: [
                suggestion
                for bucket in res["aggregations"][field]["buckets"]
                for suggestion in parse_composite_suggestion(bucket)
            ]
            for field in request.requested_fields
            if field in ["site_name"]
        }

        simple_suggestions = {
            field: [
                parse_simple_suggestion(bucket)
                for bucket in res["aggregations"][field]["buckets"]
            ]
            for field in request.requested_fields
            if field not in ["site_name"]
        }
        return {**composite_suggestions, **simple_suggestions}
    except KeyError:
        return res


@suggestion_router.post("/complete/letters", response_model=List[str])
def complete_letters(query: EQuery):
    fields = SuggestFiltersResponse.__fields__.keys()

    try:
        sent = query.sentence.split(" ")
        completion = sent[-1]
    except KeyError:
        return []

    realq = build_instant_query(completion, fields)
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )
    res = conn.search(index=ES["letters"], body=realq)
    try:
        return [
            " ".join(itertools.chain(sent[:-1], [x]))
            for x in sorted(
                list(
                    set(
                        suggestion["text"].lower()
                        for suggestion_name in fields
                        for what_is_this in res["suggest"][suggestion_name]
                        for suggestion in what_is_this["options"]
                        if suggestion["text"] != ""
                    )
                )
            )
        ]
    except KeyError:
        return []
