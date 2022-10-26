from typing import Union
from elasticsearch.helpers import streaming_bulk
from elasticsearch import Elasticsearch
from itertools import starmap

import logging


from .schemes import EDemand, ELetter, ECres

from siancedb.config import get_config

import siancedb.elasticsearch.indexes as indexes

ES = get_config()["elasticsearch"]
DEMANDS = ES["demands"]
LETTERS = ES["letters"]
CRES = ES["cres"]

logger = logging.getLogger("elasticsearch-management")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("logs/elasticsearch_management.log")
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def create_index(name, shape):
    es = Elasticsearch([{"host": ES["host"]}], timeout=300)
    es.indices.create(index=name, body=shape)


def delete_index(name):
    es = Elasticsearch([{"host": ES["host"]}], timeout=300)
    es.indices.delete(name)


def reinitialize():
    try:
        delete_index(LETTERS)
        delete_index(DEMANDS)
        delete_index(CRES)
    except:
        pass
    create_index(LETTERS, indexes.LETTERS)
    create_index(DEMANDS, indexes.DEMANDS)
    create_index(CRES, indexes.CRES)


def bulk_insert(documents):
    """
    Performs the bulk insertion of documents (that are either
    letters or demands) in the elasticsearch index.
    """
    es = Elasticsearch([{"host": ES["host"]}], timeout=300)

    def op_dict_demand(demand: EDemand):
        return {
            "_index": DEMANDS,
            "_type": "_doc",
            "_id": demand.id_demand,
            "_source": demand.dict(),
        }

    def op_dict_letter(letter: ELetter):
        return {
            "_index": LETTERS,
            "_type": "_doc",
            "_id": letter.id_letter,
            "_source": letter.dict(),
        }

    def op_dict_cres(cres: ECres):
        return {
            "_index": CRES,
            "_type": "_doc",
            "_id": cres.id_cres,
            "_source": cres.dict(),
        }

    def op_dict(x: Union[EDemand, ELetter, ECres]):
        logger.debug(f"Inserting document {x.name}")
        if isinstance(x, EDemand):
            return op_dict_demand(x)
        elif isinstance(x, ECres):
            return op_dict_cres(x)
        else:
            return op_dict_letter(x)

    # streaming_bulk returns an ITERATOR of errors/success
    # values !
    return list(streaming_bulk(es, (op_dict(x) for x in documents)))
