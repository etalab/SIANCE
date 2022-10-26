# validation 

https://stackoverflow.com/questions/30428639/check-database-schema-matches-sqlalchemy-models-on-application-startup

# AJOUT LETTRES

--------------------
NOM. Date. Demandes.
[TSR, ESP, REP]
--------------------

Exemple REP:
{
    ---inspection---
    name: "INSSN-BDX-2020-0007",
    text: "....",
    theme: "...",
    date: date,

    ---exploitant---
    site_name: "Ionisos Marseille",
    interlocutor_name: "Ionisos",
    --> suggestions vieux noms
    interlocutor_city: "Marseille",
    // nature: ["CNPE", "CP0"] / "Usine",
    identifiers: [numéro d'INB, SIRET]
    sectors: [INB, NPX, REP, LUDD, TSR, ESP, Industrie, Médical]
    --> INB/NPX filtrés des champs possibles
    --> suggestions: tsr / transport, ESP equip.sous.press., industrie/industriel etc ...
    domains: [OA, LA, Vétérinaire, Médical, Recherche, Environnement]
    // natures: [Gamma graphie, radiopro, ...]

    ---entite---
    pilot_entity_name: Marseille / DRC / ...
    resp_entity_name: Marseille / DRC (la plus intéressante!)

    ---demandes---
    ----> fuzzy & exact a priori.
    category_a_demands_nb: 6,
    category_a_demands_topics: ["incendie", "..."]
    category_a_demands_subtopics: ["incendie", "..."]
        --> répliquer dans la liste augmente le score :)

    category_b_demands_nb: 6,
    category_b_demands_topics: ["incendie", "..."]
    category_b_demands_subtopics: ["incendie", "..."]
        --> répliquer dans la liste augmente le score :)

    observations_topics: ["incendie",...] (par phrase)
        --> à requêter « sans répétition »
    synthese_topics: ["incendie", ...] (par phrase)
        --> à requêter « sans répétition »

    topics: ["", ""] (avec répétition par phrase)

    ---matériel---
    equipments: []
}

# INDEX Demandes / Synthèse / Observations

{
    text: "...",
    inspection: "...",
    letter_id:,

    topics: []
    subtopics: []
    resp_entity_name: Marseille / DRC (la plus intéressante!)

    date: date,
    site_name: "Ionisos Marseille",
    interlocutor_city: "Marseille",
}

# Liens

https://www.elastic.co/guide/en/elasticsearch/reference/6.8/suggester-context.html
https://www.elastic.co/guide/en/elasticsearch/reference/6.8/search-suggesters-completion.html
https://www.elastic.co/guide/en/elasticsearch/reference/6.8/search-suggesters-phrase.html
https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html
https://jolicode.com/blog/construire-un-bon-analyzer-francais-pour-elasticsearch
https://www.elastic.co/fr/blog/elastic-app-search-query-suggestion-api-now-available
https://swiftype.com/documentation/app-search/guides/query-suggestions

https://fr.slideshare.net/linagora/prsentation-elasticsearch-linagora-open-source

+basic query string


### FIRST MAPPING TEST

```

PUT /letters
{
  "settings": {
    "analysis": {
      "filter": {
        "french_elision": {
          "type": "elision",
          "articles_case": true,
          "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
        },
        "french_stop": {
          "type":       "stop",
          "stopwords":  "_french_" 
        },
        "french_synonym": {
          "type": "synonym",
          "expand": true,
          "synonyms": [
            "salade, laitue",
            "mayo, mayonnaise",
            "grille, toaste",
	    "Orano, Areva"
          ]
        },
        "french_stemmer": {
          "type": "stemmer",
          "language": "light_french"
        }
      },
      "analyzer": {
        "french_heavy": {
          "tokenizer": "standard",
          "filter": [
            "french_elision",
            "lowercase",
            "french_stop",
            "french_synonym",
            "french_stemmer"
          ]
        },
        "french_light": {
          "tokenizer": "standard",
          "filter": [
            "french_elision",
            "lowercase"
          ]
        }
      }
    }
  },
  "mappings":{
      "properties": {
        "autocomplete": {
          "type": "search_as_you_type",
          "analyzer": "french_light"
        },
        "name": {
          "type": "search_as_you_type",
          "fields": {
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "content": {
          "type": "text",
          "analyzer": "french_light", 
          "fields": {
            "stemmed": {
              "type": "text",
              "analyzer": "french_heavy"
            }
          },
          "copy_to": "autocomplete"
        },
        "theme": {
          "type": "text",
          "norms": false,
          "analyzer": "french_light",
          "fields": {
            "keyword": {
              "type": "keyword"
            },
            "completion": {
              "type": "completion"
            }
          },
          "copy_to": "autocomplete"
        },
        "date": {
          "type": "date",
          "format": "dd/MM/yyyy||yyyy-MM-dd"
        },
        "site_name": {
          "type": "text",
          "analyzer": "french_light",
          "fields": {
            "suggest": {
              "type": "completion"
            },
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "interlocutor_name": {
          "type": "text",
          "analyzer": "french_light",
          "fields": {
            "suggest": {
              "type": "completion"
            },
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "interlocutor_city": {
          "type": "text",
          "analyzer": "french_light",
          "fields": {
            "suggest": {
              "type": "completion"
            },
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "identifiers": {
          "type": "long"
        },
        "sectors": {
          "type": "keyword",
          "copy_to": "autocomplete"
        },
        "domains": {
          "type": "keyword",
          "copy_to": "autocomplete"
        },
        "pilot_entity": {
          "type": "keyword"
        },
        "resp_entity": {
          "type": "keyword"
        },
        "demands_a": {
          "type": "integer"
        },
        "demands_b": {
          "type": "integer"
        },
        "observations_topics": {
          "type": "keyword"
        },
        "synthesis_topics": {
          "type": "keyword"
        },
        "demands_a_topics": {
          "type": "keyword"
        },
        "demands_b_topics": {
          "type": "keyword"
        },
        "topics": {
          "type": "keyword",
          "copy_to": "autocomplete"
        },
        "equipments": {
          "type": "keyword",
          "copy_to": "autocomplete", 
          "fields": {
            "completion": {
              "type": "completion"
            }
          }
        }
      }
    }
}
```

### Queries
#### Autocomplete « did you mean »

```
POST /letters/_search
{
  "suggest": {
    "dym": {
      "text": "arrêt de racteur", 
      "phrase": {
        "field": "autocomplete",
        "size": 3,
        "gram_size": 3,
        "highlight": {
          "pre_tag": "<em>",
          "post_tag": "</em>"
        }
      }
    }
  }
}
```

#### Autocomplete « as you type »
1. Prendre le dernier mot de la requête
2. Faire une recherche de complétion sur les champs 
```curl
POST /letters/_search 
{
  "_source": "",
  "suggest": {
    "text": "lil",
    "city": {
      "completion": {
        "field": "interlocutor_city.suggest",
        "skip_duplicates": true,
        "size": 2
      }
    },
    "equipment": {
      "completion": {
        "field": "equipments.completion",
        "skip_duplicates": true,
        "size": 2
      }
    }
  }
}
```

#### Real Query: fulltext part

```
POST /letters/_search
{
  "_source": ["name", "theme", "content"],
  "query": {
    "multi_match": {
      "query": "arrêt de réacteur",
      "type": "bool_prefix",
      "fields": ["content", "content.stemmed"]
    }
  },
  "highlight": {
    "pre_tags": ["<em>"],
    "post_tags": ["</em>"],
    "fields": {
      "content": {}
    }
  },
  "aggs": {
    "equipments": {
      "significant_terms": {
        "field": "equipments.keyword" / equipments.completion??
      }
    }, ...
  }
}
```
Remarque: il faut ajouter les filtres qui vont par dessus!

#### Idées ajouter « simple_query_string »

Cela permet d'utiliser  « + » / « | » / « " " » ce qui est VRAIMENT utile !
On met cela à la place de multi_match et hop c'est parti ;).

####  Ajouter BERT

https://xplordat.com/2019/10/28/semantics-at-scale-bert-elasticsearch/

#### Construire des variantes

- Où la query cherche aussi dans les champs de méta-données (via autocomplete en fait)

#### Tester le modèle version [JE SAIS CE QUE JE VEUX]

Pour N,K fixés
1. Sélectionner un document aléatoirement
2. Extraire les informations suivantes
	- date
	- interlocuteur
	- ville
	- thème
	- équipements
	- entité responsable / entité pilote
	- secteurs / domaines
3. Sélectionner N valeurs à chercher, et faire au plus K erreurs.
4. Produire l'histogramme des scores et placer notre document 
    dans cet histogramme.

#### Tester le modèle version [Je cherche un thème]

1. Sélectionner un document aléatoirement
2. Extraire les informations suivantes
	- date
	- interlocuteur
	- ville
	- thème
	- équipements
	- entité responsable / entité pilote
	- secteurs / domaines
3. Sélectionner N valeurs à chercher, et faire au plus K erreurs.
4. Produire l'histogramme des scores et placer notre document 
    dans cet histogramme.
5. Effectuer cette même recherche en plein texte 
6. Effectuer cette même recherche dans le champ "autocomplete"

## Exemples de lettres

```
{
	"name": "INSSN-BDX-2020-0004",
	"content": "Le réacteur 2 du CNPE du Blayais a été arrêté le 9 mai 2020 pour maintenance et renouvellement du combustible. L’inspection concernait le contrôle de la bonne application des dispositions de sûreté en ce qui concerne la gestion des écarts de conformité traités sur cet arrêt. En outre, les inspecteurs se sont rendus  en  zone  contrôlée  dans  le  bâtiment  réacteur ainsi  que  dans  le  bâtiment  des  auxiliaires nucléaires (BAN), afin de contrôler par sondage la réalisation des travaux prévus pour le traitement de certains écarts de conformité. A l’issue de cette inspection, les inspecteurs considèrent que le traitement des écarts de conformité par vos services est satisfaisant. Depuis l’inspection des réponses satisfaisantes ont été apportées à certaines demandes formulées en réunion de synthèse, en particulier en ce qui concerne la pose de renforts d’armoires électriques pourgarantir leur tenue aux séismes, le contrôle de fixations du système de ventilation de secours des locaux pompes de charge et le finalisation des travaux sur la soupape du système d’injection de sécurité 2 RIS 2015 VP. Toutefois,  des actions correctives doivent être apportées dans la détermination des causes ayant conduit à une dégradation de l’huile d’un groupe motopompe primaire en dehors des spécifications autorisées. De plus, dans le domaine de la surveillance de la conservation humide des générateurs de vapeur en cours d’arrêt, des dispositions harmonisées entre vos services concernés devront être adoptées, pour mettre en place des actions correctives en cas de dérive des critères à respecter.",
	"theme":  "Arrêt de réacteur",
	"date": "2020-07-23",
	"interlocutor": ["EDF", "CNPE du Blayas"],
	"identifiers": [789988765447766, 102, 104],
	"sectors": ["Environnement", "ESP", "INB", "REP"],
	"demands": 4,
 	"topics": ["générateur vapeur", "FOH", "environnement"],
        "equipments": ["2 RCP 003 MO", "PA 100343", "RPVOT", "MSR", "ECE", "GV", "hydrazine", "N2H4", "ASR36", "2R36", "BAN", "2 RIS", "2015 VP"] 
}
```

```
PUT /letters/_doc/2
{
	"name": "INSNP-LIL-2020-0464",
	"content": "L’ASN a conduit, le 25 novembre 2020,Source du renvoi introuvable. une inspection du Centre Hospitalier Saint-Philibert, situé à LOMME (59), structure du Groupement des Hôpitaux de l’Institut Catholique de Lille. L’inspection a porté sur l’organisation et les dispositions mises en œuvre pour assurer le espect des dispositions réglementaires relatives à la radioprotection des patients, des travailleurs et du public dans le cadre des pratiques interventionnelles radioguidées. En raison de la pandémie de Covid-19, l’ASN a réalisé cette inspection à distance. L’inspecteur a préalablement instruit les documents transmis par le centre hospitalier et s’est entretenu en visioconférence avec le Directeur Adjoint des Ressources Humaines, la responsable de la gestion des risques, la responsable des soins en coordination avec le bloc opératoire et le plateau technique interventionnel, les conseillers en radioprotection dont le coordinateur en radioprotection et la radiophysicienne de l’entreprise prestataire en physique médicale. En matière de radioprotection des travailleurs, l’inspecteur a constaté que l’organisation qui s’appuie sur deux personnes compétentes en radioprotection (PCR) est robuste, leurs missions sont assez précisément définies. Il conviendra toutefois de mettre à jour certaines de leurs missions afin de prendre en compte, d’une part, de récentes évolutions réglementaires et, d’autre part, y intégrer les actions en lien avec le transfert du bloc opératoire dans de nouveaux locaux. Sur ce dernier point, il conviendra de s’assurer que les exigences prescrites dans le cahier des charges de ces nouveaux locaux sont bien conformes à la réglementation en vigueur. Les vérifications de radioprotection sont réalisées conformément aux exigences réglementaires et aucune non-conformité n’a été relevée. L’évaluation de l’exposition des travailleurs aux rayonnements ionisants est bien avancée et nécessite seulement, à ce stade, une formalisation des données d’ores et déjà collectées. Par contre, de nombreux travailleurs ne sont plus à jour en matière de formation à la radioprotection, tant en matière de renouvellement qu’en matière de formation initiale. Si cette situation s’explique par le contexte sanitaire dû à la COVID-19, elle exige une action engageante pour remédier au retard pris. En matière de radioprotection des patients, les contrôles de qualité des dispositifs médicaux sont réalisés pour tous les équipements. De manière générale, si des attendus de la décision n° 2019-DC-0660 de l’Autorité de sûreté nucléaire du 15 janvier 2019, fixant les obligations d’assurance de la qualité en imagerie médicale mettant en œuvre des rayonnements ionisants sont aboutis ou en cours, il n’existe pas encore un système de gestion de la qualité formalisé au regard de l’importance du risque radiologique pour les personnes exposées, en tenant compte de la cartographie des risques réalisée en application de l’article R.1333-70 du code de la santé publique. De plus, l’inspecteur a constaté que le plan d’optimisation de la physique médicale tel que rédigé présentait beaucoup trop de références obsolètes et qu’il nécessitait une mise à jour en profondeur. Enfin, de nombreux travailleurs ne sont pas à jour en matière de formation à la radioprotection des patients.",
	"theme":  "Radioprotection",
	"date": "2020-11-25",
	"interlocutor": ["Hôpital Saint Philibert", "Hôpitaux de l'Institut Catholique de Lille"],
	"identifiers": [457876543456789],
	"sectors": ["Médical", "NPX"],
	"demands": 5,
 	"topics": ["radioprotection", "intervetions radioguidées", "zonage", "FOH", "générateurs X"],
  "equipments": ["générateur X", "ASL", "rayonnement X", "SIEMENS", "ARCADIS", "AVANTIC", "VASCULAIRE", "urologues", "PCR", "COVID"] 
}
```


### Index des demandes

```
PUT /demands
{ "settings": {
    "analysis": {
      "filter": {
        "french_elision": {
          "type": "elision",
          "articles_case": true,
          "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
        },
        "french_stop": {
          "type":       "stop",
          "stopwords":  "_french_" 
        },
        "french_synonym": {
          "type": "synonym",
          "expand": true,
          "synonyms": [
            "salade, laitue",
            "mayo, mayonnaise",
            "grille, toaste"
          ]
        },
        "french_stemmer": {
          "type": "stemmer",
          "language": "light_french"
        }
      },
      "analyzer": {
        "french_heavy": {
          "tokenizer": "standard",
          "filter": [
            "french_elision",
            "lowercase",
            "french_stop",
            "french_synonym",
            "french_stemmer"
          ]
        },
        "french_light": {
          "tokenizer": "standard",
          "filter": [
            "french_elision",
            "lowercase"
          ]
        }
      }
    }
  },
  "mappings":{
      "properties": {
        "autocomplete": {
          "type": "search_as_you_type",
          "analyzer": "french_light"
        },
        "name": {
          "type": "keyword"
        },
        "content": {
          "type": "text",
          "analyzer": "french_light", 
          "fields": {
            "stemmed": {
              "type": "text",
              "analyzer": "french_heavy"
            }
          },
          "copy_to": "autocomplete"
        },
        "theme": {
          "type": "text",
          "norms": false,
          "analyzer": "french_light",
          "fields": {
            "keyword": {
              "type": "keyword"
            }
          },
          "copy_to": "autocomplete"
        },
        "date": {
          "type": "date",
          "format": "dd/MM/yyyy||yyyy-MM-dd"
        },
        "site_name": {
          "type": "text",
          "analyzer": "french_light",
          "fields": {
            "suggest": {
              "type": "completion"
            },
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "interlocutor_name": {
          "type": "text",
          "analyzer": "french_light",
          "fields": {
            "suggest": {
              "type": "completion"
            },
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "interlocutor_city": {
          "type": "text",
          "analyzer": "french_light",
          "fields": {
            "suggest": {
              "type": "completion"
            },
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "sectors": {
          "type": "keyword",
          "copy_to": "autocomplete"
        },
        "domains": {
          "type": "keyword",
          "copy_to": "autocomplete"
        },
        "pilot_entity": {
          "type": "keyword"
        },
        "resp_entity": {
          "type": "keyword"
        },
        "demand_type": {
          "type": "keyword"
        },
        "topics": {
          "type": "keyword",
          "copy_to": "autocomplete"
        }
      }
    }
  }
}
```
