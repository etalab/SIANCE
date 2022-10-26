#!/usr/bin/env python3
import json
import re
import datetime
from siancedb.config import get_config
from typing import List, Optional, Tuple, Union
from siancedb.elasticsearch.schemes import EFilter, EValue, EQuery, FieldValuesPost

PAGE_SIZE = get_config()["elasticsearch"]["page_size"]


def did_you_mean(sentence: str):
    """Build the did_you_mean type of
    query as a suggestion
    called dym for `did_you_mean`
    """
    return {
        "suggest": {
            "dym": {
                "text": sentence,
                "phrase": {
                    "field": "autocomplete",
                    "size": 3,
                    "gram_size": 3,
                    "highlight": {"pre_tag": "###", "post_tag": "###"},
                },
            }
        }
    }


def search_as_you_type(completion: str, fields: List[str]):
    """Build the search_as_you_type query"""
    return {
        "suggest": {
            "text": completion,
            **{
                field_name: {
                    "completion": {
                        "field": f"{field_name}.completion",
                        "skip_duplicates": True,
                        "size": 2,
                    }
                }
                for field_name in fields
            },
        }
    }


def constraint_to_filter(k: str, v: EValue):
    field = f"{k}.keyword"
    if isinstance(v, str):
        return {"term": {field: v}}
    else:
        return {"terms": {field: v}}


def body_query_demands(filters: EFilter, max_id: int = -1):
    return {
        "size": 10000,
        "search_after": [int(max_id)],
        "query": {"bool": query_filters(filters)},
        "sort": [{"id_demand": "asc"}],
    }


def query_filters(
    filters: EFilter, dates: Optional[Union[Tuple[int, int], datetime.datetime]] = None
):
    musts = [
        constraint_to_filter(k, v)
        for k, v in dict(filters).items()
        if v != "" and v != []
    ]

    if dates:
        if isinstance(dates, tuple):
            musts.append(
                {
                    "range": {
                        "date": {
                            "gte": f"{dates[0]}/01/01",
                            "lte": f"{dates[1]}/12/31",
                            "format": "yyyy/MM/dd",
                        }
                    }
                }
            )
        else:
            musts.append(
                {
                    "range": {
                        "date": {
                            "gt": str(dates),
                            "format": "yyyy-MM-dd HH:mm:ss.SSSSSS",
                        }
                    }
                }
            )
    return {"filter": {"bool": {"must": musts}}}


def simple_query_string(sentence: str):
    return {
        "simple_query_string": {
            "query": sentence,
            "fields": [
                "content^3",
                "content.stemmed^2",
                "name^2",
                "site_name^2",
                "interlocutor_name^2",
                "interlocutor_city",
                "topics",
            ],
            "default_operator": "and",
        }
    }


def date_aggregation(filters: EFilter):
    return {
        "date_aggregation_filtered": {
            **query_filters(filters),
            "aggs": {
                "date_aggregation": {
                    "date_histogram": {
                        "field": "date",
                        "calendar_interval": "quarter",
                        "format": "dd-MM-yyyy",
                    }
                }
            },
        }
    }


def composite_id_value_aggregation(id_field, value_field):

    return {
        "terms": {"field": value_field, "size": 10},
        "aggs": {"inner_agg": {"terms": {"field": id_field}}},
    }


def basic_value_aggregation(value_field):
    return {
        "terms": {
            "field": value_field,
            "size": 350 if value_field == "topics.keyword" else 10,
        }
    }


def field_aggregation(field):
    # if field == "interlocutor_name":
    #     return composite_id_value_aggregation(
    #       "id_interlocutor", "interlocutor_name.keyword"
    #   )
    if field == "site_name":
        return composite_id_value_aggregation(
            "interlocutor_name.keyword", "site_name.keyword"
        )
    else:
        return basic_value_aggregation(f"{field}.keyword")


def suggestions_aggregations(
    fields: List[str], filters: EFilter, daterange: Optional[Tuple[int, int]]
):
    return {
        f"{field}_filtered": {
            **query_filters(
                {k: v for k, v in dict(filters).items() if k != field}, daterange
            ),
            "aggs": {field: field_aggregation(field)},
        }
        for field in fields
    }


def build_fields_values_query(query: FieldValuesPost):
    # doc June 2021:
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html
    return {
        "size": 0,
        "_source": query.requested_fields,
        "query": {
            "multi_match": {"query": query.value, "fields": query.requested_fields}
        },
        "aggs": {field: field_aggregation(field) for field in query.requested_fields},
    }


def build_field_values_query(field: str, value: str):
    return {
        "size": 0,
        "_source": field,
        "aggs": {field: field_aggregation(field)},
    }


def build_paginated_cres_query(q: EQuery, page: int, includes: List[str]):

    b = dict()
    if q.sentence.strip() != "":
        b["must"] = simple_query_string(q.sentence)

    return {
        "_source": {"includes": includes},
        "from": page * PAGE_SIZE,
        "sort": ["_score", {"date_deb_evenement": "desc"}, {"date_incident": "desc"}]
        if q.sorting is None
        else [{q.sorting.key: q.sorting.order}, "_score"],
        "size": PAGE_SIZE,
        "query": {
            "bool": {
                **b,
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "site_concerne": " ".join(
                                        [
                                            part
                                            for site in q.filters.site_name
                                            for part in re.compile(r"[ -]").split(site)
                                        ]
                                    )
                                }
                            },
                            {
                                "match": {
                                    "etablissement": " ".join(
                                        [
                                            part
                                            for site in q.filters.interlocutor_name
                                            for part in re.compile(r"[ -]").split(site)
                                        ]
                                    )
                                }
                            },
                            # to be used, the folder paths must be first more cleaned
                            # {
                            #     "match": {
                            #         "r_folder_path": " ".join(
                            #             [
                            #                 part
                            #                 for item in [
                            #                     "interlocutor_name",
                            #                     "site_name",
                            #                 ]
                            #                 for site in q.filters.get(item, [])
                            #                 for part in re.compile(r"[ -]").split(site)
                            #             ]
                            #         )
                            #     }
                            # },
                        ]
                    }
                },
            }
        },
    }


def build_paginated_query(q: EQuery, page: int, excludes: List[str]):

    b = dict()
    if q.sentence.strip() != "":
        b["must"] = simple_query_string(q.sentence)

    return {
        "_source": {"excludes": excludes},
        "from": page * PAGE_SIZE,
        "size": PAGE_SIZE,
        "sort": ["_score", {"date": "desc"}]
        if q.sorting is None
        else [{q.sorting.key: q.sorting.order}, "_score"],
        "query": {
            "bool": {
                **b,
                **query_filters(q.filters, q.daterange),
            }
        },
        "highlight": {
            "pre_tags": ["###"],
            "post_tags": ["###"],
            "fields": {"content.stemmed": {}, "content": {}},
        },
    }
    
def build_not_paginated_query(q: EQuery,excludes: List[str], max_answer:int=100):

    b = dict()
    if q.sentence.strip() != "":
        b["must"] = simple_query_string(q.sentence)

    return {
        "_source": {"excludes": excludes},
        "from": 0,
        "size": min(max_answer, 9999),
        "sort": ["_score", {"date": "desc"}]
        if q.sorting is None
        else [{q.sorting.key: q.sorting.order}, "_score"],
        "query": {
            "bool": {
                **b,
                **query_filters(q.filters, q.daterange),
            }
        },
        "highlight": {
            "pre_tags": ["###"],
            "post_tags": ["###"],
            "fields": {"content.stemmed": {}, "content": {}},
        },
    }



def build_explain_query(q: EQuery):
    return {
        "query": {
            "bool": {
                "must": simple_query_string(q.sentence),
                **query_filters(q.filters, q.daterange),
            }
        },
    }


with open(get_config()["geography"]["regions"], "r") as f:
    GEO = json.load(f)


def build_geo_query(q: EQuery, id_interlocutors: List[int] = []):
    b = dict()
    if q.sentence.strip() != "":
        b["must"] = simple_query_string(q.sentence)
    return {
        "size": 0,
        "_source": ["name"],
        "query": {
            "bool": {
                **b,
                **query_filters(q.filters, q.daterange),
            }
        },
        "aggs": {
            "ludd_and_rep": {
                "filter": {"terms": {"id_interlocutor": id_interlocutors}},
                "aggs": {"id_interlocutor": {"terms": {"field": "id_interlocutor"}}},
            },
            **{
                r["properties"]["code"]: {
                    "filter": {
                        "term": {"region_code": r["properties"]["code"]},
                    },
                    "aggs": {
                        "interlocutors": {"cardinality": {"field": "id_interlocutor"}}
                    },
                }
                for r in GEO["features"]
            },
        },
    }


def build_feedback_query(q: EQuery, fields: List[str]):
    b = dict()
    if q.sentence.strip() != "":
        b["must"] = simple_query_string(q.sentence)
    return {
        "size": 0,
        "_source": ["name"],
        "query": {
            "bool": {
                **b,
                # **query_filters(q.filters, q.daterange),
            }
        },
        "aggs": {
            **date_aggregation(q.filters),
            **suggestions_aggregations(fields, q.filters, q.daterange),
        },
        **did_you_mean(q.sentence),
    }


def build_instant_query(sentence: str, fields: List[str]):
    return {
        "size": 0,
        "_source": ["name"],
        **search_as_you_type(sentence, fields),
    }
