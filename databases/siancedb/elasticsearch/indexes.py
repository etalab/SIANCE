FRENCH_SETTINGS = {
    "analysis": {
        "filter": {
            "french_elision": {
                "type": "elision",
                "articles_case": True,
                "articles": [
                    "l",
                    "m",
                    "t",
                    "qu",
                    "n",
                    "s",
                    "j",
                    "d",
                    "c",
                    "jusqu",
                    "quoiqu",
                    "lorsqu",
                    "puisqu",
                ],
            },
            "french_stop": {"type": "stop", "stopwords": "_french_"},
            "french_synonym": {
                "type": "synonym",
                "expand": True,
                "synonyms": [
                    "EDF,Électricité de France",
                    "PIR,pratiques interventionnelles radioguidées",
                    "CEA,Commissariat à l'énergie atomique et aux énergies alternatives",
                    "séisme,tremblement de terre",
                    "incendie,feu",
                ],
            },
            "french_stemmer": {"type": "stemmer", "language": "light_french"},
        },
        "analyzer": {
            "french_heavy": {
                "tokenizer": "standard",
                "filter": [
                    "french_elision",
                    "asciifolding",
                    "french_synonym",
                    "lowercase",
                    "french_stop",
                    "french_stemmer",
                ],
            },
            "french_light": {
                "tokenizer": "standard",
                "filter": ["french_elision", "lowercase"],
            },
        },
    }
}


meta_fields = [
    {"name": "theme", "spec": {"norms": False}},
    {"name": "site_name", "spec": {}},
    {"name": "complementary_site_name", "spec": {}},
    {"name": "interlocutor_city", "spec": {}},
    {"name": "interlocutor_name", "spec": {}},
    {"name": "sectors", "spec": {}},
    {"name": "domains", "spec": {}},
    {"name": "natures", "spec": {}},
    {"name": "paliers", "spec": {}},
    {"name": "pilot_entity", "spec": {}},
    {"name": "resp_entity", "spec": {}},
    {"name": "topics", "spec": {"norms": False}},
    {"name": "complementary_topics", "spec": {}},
    {"name": "equipments_trigrams", "spec": {}},
    {"name": "equipments_full_names", "spec": {"norms": False}},
    {"name": "isotopes", "spec": {}},
    {"name": "region", "spec": {}},
]


LETTERS = {
    "settings": FRENCH_SETTINGS,
    "mappings": {
        "properties": {
            "autocomplete": {"type": "search_as_you_type", "analyzer": "french_light"},
            "id_letter": {"type": "long"},
            "id_interlocutor": {"type": "long"},
            "name": {
                "type": "search_as_you_type",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "completion": {"type": "completion"},
                },
            },
            "content": {
                "type": "text",
                "analyzer": "french_light",
                "fields": {"stemmed": {"type": "text", "analyzer": "french_heavy"}},
                "copy_to": "autocomplete",
            },
            **{
                v["name"]: {
                    "type": "text",
                    "analyzer": "french_heavy",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "completion": {
                            "type": "completion",
                            "analyzer": "french_heavy",
                        },
                    },
                    "copy_to": "autocomplete",
                    **v["spec"],
                }
                for v in meta_fields
            },
            "date": {"type": "date", "format": "dd/MM/yyyy||yyyy-MM-dd"},
            "identifiers": {"type": "long"},
            "siv2": {
                "type": "keyword",
            },
            "demands_a": {"type": "integer"},
            "demands_b": {"type": "integer"},
            "point": {"type": "geo_point"},
            "region_code": {"type": "keyword"},
        }
    },
}

cres_fields = [
    {"name": "site_name", "spec": {}},
    {"name": "inb_information", "spec": {}},
    {"name": "interlocutor_name", "spec": {}},
    {"name": "natures", "spec": {}},
]


CRES = {
    "settings": FRENCH_SETTINGS,
    "mappings": {
        "properties": {
            "autocomplete": {"type": "search_as_you_type", "analyzer": "french_light"},
            "id_cres": {"type": "long"},
            "id_interlocutor": {"type": "long"},
            "name": {
                "type": "search_as_you_type",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "completion": {"type": "completion"},
                },
            },
            "summary": {
                "type": "text",
                "analyzer": "french_light",
                "fields": {"stemmed": {"type": "text", "analyzer": "french_heavy"}},
                "copy_to": "autocomplete",
            },
            **{
                v["name"]: {
                    "type": "text",
                    "analyzer": "french_heavy",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "completion": {
                            "type": "completion",
                            "analyzer": "french_heavy",
                        },
                    },
                    "copy_to": "autocomplete",
                    **v["spec"],
                }
                for v in cres_fields
            },
            "date": {"type": "date", "format": "dd/MM/yyyy||yyyy-MM-dd"},
            "siret": {"type": "long"},
            "siv2": {
                "type": "keyword",
            },
        }
    },
}


DEMANDS = {
    "settings": FRENCH_SETTINGS,
    "mappings": {
        "properties": {
            "id_letter": {"type": "long"},
            "id_demand": {"type": "long"},
            "id_interlocutor": {"type": "long"},
            "autocomplete": {"type": "search_as_you_type", "analyzer": "french_light"},
            "name": {"type": "keyword"},
            "content": {
                "type": "text",
                "analyzer": "french_light",
                "fields": {"stemmed": {"type": "text", "analyzer": "french_heavy"}},
                "copy_to": "autocomplete",
            },
            **{
                v["name"]: {
                    "type": "text",
                    "analyzer": "french_heavy",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "completion": {"type": "completion"},
                    },
                    "copy_to": "autocomplete",
                    **v["spec"],
                }
                for v in meta_fields
            },
            "date": {"type": "date", "format": "dd/MM/yyyy||yyyy-MM-dd"},
            "demand_type": {"type": "keyword"},
            "point": {"type": "geo_point"},
            "region_code": {"type": "keyword"},
        }
    },
}
