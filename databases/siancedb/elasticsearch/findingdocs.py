#!/usr/bin/env python3

from typing import Optional, List, Union, Tuple
from pydantic import BaseModel, Field

import json
import sys
import os
from elasticsearch import Elasticsearch
import datetime
from random import random, randint

from schemes import ESLetter, ESDemand


def fulltextQuery(query: str):
    return {
        "multi_match": {
            "query": query,
            "type": "bool_prefix",
            "fields": ["content", "content.stemmed"],
            "minimum_should_match": "75%",
        }
    }


def aggquery(query):
    return {
        "query": query,
        "aggs": {
            "score_stats": {"stats": {"script": "_score"}},
            "score_histo": {"histogram": {"script": "_score", "interval": 0.3}},
        },
    }


def random_value_selector(v: Union[str, List[str]], prob: int):
    if isinstance(v, str):
        return v
    else:
        return [str(x) for x in v if random() < prob]


def randomize_filter_dict(constraints: dict, prob: float):
    """Extracts from the dict some fields and some values
    prob is the probability that a given field
    is selected. Which is also the probability that a value
    is selected.
    """
    return {
        k: random_value_selector(v, prob)
        for (k, v) in constraints.items()
        if random() < prob
    }


def valueToFulltext(value: Union[str, List[str]]):
    if isinstance(value, str):
        return value
    else:
        return " ".join(value)


def constraintsToFulltext(constraints: dict):
    return " ".join((valueToFulltext(v) for v in constraints.values()))


def constraintToFilters(k: str, v: Union[List[str], str]):
    if isinstance(v, str):
        return [{"term": {k: v}}]
    else:
        return [{"term": {k: y}} for y in v]


def constraintsToFilter(constraints: dict):
    myFilters = [c for k, v in constraints.items() for c in constraintToFilters(k, v)]
    return {"bool": {"filter": {"bool": {"must": myFilters}}}}


def documentToRandomQueries(letter: ESLetter, prob: float):
    constraints = letter.dict()
    del constraints["content"]
    # del constraints["id_letter"]
    del constraints["name"]

    constraints = randomize_filter_dict(constraints, 0.2)

    text = constraintsToFulltext(constraints)
    filt = constraintsToFilter(constraints)

    return {"fulltext": aggquery(fulltextQuery(text)), "filters": aggquery(filt)}


# Par défaut regarde le elasticsearch local ;)
es = Elasticsearch()


def getRandomDocument(maxid: int):
    return (maxid, ESLetter(**es.get(index="letters", id=randint(1, maxid))["_source"]))


def documentIsInResult(iddoc, results):
    try:
        return any(int(doc._id) == int(iddoc) for doc in results["hits"]["hits"])
    except:
        return False


iddoc, doc = getRandomDocument(2)
queries = documentToRandomQueries(doc, 0.7)
# pylint: disable=unexpected-keyword-arg
withFilter = es.search(index="letters", body=queries["filters"], size=10)
# pylint: disable=unexpected-keyword-arg
withFulltext = es.search(index="letters", body=queries["fulltext"], size=10)
isInFilter = documentIsInResult(iddoc, withFilter)
isInFulltext = documentIsInResult(iddoc, withFulltext)
del queries["fulltext"]["aggs"]
scoreFulltext = es.explain("letters", iddoc, body=queries["fulltext"])["explanation"][
    "value"
]

print(f"Document {iddoc}: text({isInFulltext}) filt({isInFilter})")
print(f"Document {iddoc}: {withFulltext} \n\t {scoreFulltext}")
