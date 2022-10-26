from typing import List, Dict, Tuple
import pandas as pd
import json
import altair as alt
import elasticsearch as es

from siancedb.elasticsearch.schemes import EQuery, EFilter
from siancedb.elasticsearch.queries import build_paginated_query
import pandas as pd
import numpy as np

alt.data_transformers.disable_max_rows()

def parse_elastic_response(
    config: Dict,
    query: EFilter
):
    realq = build_paginated_query(
        query,
        0,
        ["content"]
    )
    realq["size"] = 10000
    conn = es.Elasticsearch(
        hosts=[{"host": config["host"], "port": config["port"]}], timeout=30
    )
    res = conn.search(index=config["letters"], body=realq)

    columns = {
        "link": "Lettre",
        "date": "Date",
        "theme": "Thème",
        "pilot_entity": "Entité pilote",
        "site_name": "Site",
        "complementary_site_name": "URA",
        "interlocutor_name": "Exploitant",
        "sectors": "Secteurs",
        "paliers": "Palier (INB)",
        "equipments_trigrams": "Systèmes (REP)",
        "isotopes": "Isotopes",
        "topics": "Sujets détectés",
        "demands_a": "Demandes A",
        "demands_b": "Demandes B",
        "merged_interlocutors": "Établissements"
    }
    
    def merge_interlocutor_site(doc):
        if doc["site_name"] is None or pd.isna(doc["site_name"]) or not doc["site_name"]:
            merged_interlocutors = doc["interlocutor_name"]
        else:
            merged_interlocutors = doc["site_name"][0]
        if not merged_interlocutors:
            merged_interlocutors = np.nan
        return merged_interlocutors
    
    def clean_sector(doc):
        if "NPX" in doc["sectors"] and "Médical" not in doc["sectors"] and "Industrie" not in doc["sectors"]:
            return "Autres NPX"
        elif "NPX" in doc["sectors"]:
            return [sector for sector in doc["sectors"] if sector != "NPX"]
        return doc["sectors"]

    def clean_data(doc):
        doc["merged_interlocutors"] = merge_interlocutor_site(doc)
        doc["sectors"] = clean_sector(doc)
        return doc

    df = pd.DataFrame(
        [clean_data(doc["_source"]) for doc in res["hits"]["hits"]],
        columns=list(columns.keys()),
    ).rename(columns=columns)
    return df

def get_hist(data: pd.DataFrame, col: str) -> Dict:
    """
    Prepare a top-10 histogram for the required column

    Args:
        data (pd.DataFrame): a dataframe or series including the column of interest (after explosion = without nested values)
        col (str): the name of the column to plot top-10 histogram on

    Returns:
        Dict: json with altair ready-to-serve altair content
    """
    
    chart = alt.Chart().transform_aggregate(
        Lettres="count(*):Q",
        groupby=[col]
    ).transform_window(
        rank='rank(Lettres)',
        sort=[alt.SortField('Lettres', order='descending')],
    ).transform_filter(
        alt.datum.rank <= 10
    ).mark_bar().encode(
        y=alt.Y(col+":O", sort="-x"),
        x=alt.X("Lettres:Q"),
        tooltip=[col, alt.Tooltip("Lettres", type="quantitative")],
    )
    
    json_content = (
        alt.layer(
            chart,
            data=data,
        )
        .interactive()
        .to_json()
    )
    return json.loads(json_content)

def get_dashboards_hist(data: pd.DataFrame) -> Dict[str, Dict]:
    columns = ["Établissements", "Sujets détectés", "Secteurs"]
    return {
        col : get_hist(data.explode(col).dropna(subset=[col]), col=col)
        for col in columns
    }
