import numpy as np
import pandas as pd
from typing import Optional, Dict, Iterable, List, Tuple
import datetime as dt
import json
import logging

logger = logging.getLogger("siance-api-log")
fh = logging.FileHandler("logs/siance-api-log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


def filter_logs(
    df: pd.DataFrame,
    equality_filters: Optional[Dict] = None,
    difference_filters: Optional[Dict] = None,
    inequality_filters: Optional[Dict] = None,
    group_count: Optional[Iterable] = None,
) -> pd.DataFrame:
    """
    Example: if the input is the following, the output will be, for each disciple, the number of times he was taught
     philosophy by Marc Aurele outside the city of Athens and after the 15th birthday of Marc Aurele
    group_count = "disciple",
    equality_filters = {"user": "Marc Aurele", "action": "teaching philosophy"}
    difference_filters = {"place": "Athens"}
    inequality_filters = {"age": [15,None]} bounds of inequality to filter persons >= 15 years old
    """
    if equality_filters is not None:
        for key, value in equality_filters.items():
            df = df[df[key] == value]
    if difference_filters is not None:
        for key, value in difference_filters.items():
            df = df[df[key] != value]
    if inequality_filters is not None:
        for key, value in inequality_filters.items():
            lower, upper = value
            if lower is not None:
                df = df[df[key] >= lower]
            if upper is not None:
                df = df[df[key] <= upper]
    if group_count is not None:
        if not isinstance(group_count, Iterable):
            group_count = [group_count]
        other_columns = np.setdiff1d(df.columns.values, group_count)
        df = df.groupby(group_count).count()
        df["count"] = df[other_columns[0]]
        df = df.drop(columns=other_columns)
    return df


def get_user_stats(df: pd.DataFrame) -> Dict[str, int]:
    """
    Args:
        df (pd.DataFrame): if the dataframe has a timestamp column called `date` it must be calculated in milliseconds
    """
    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"], errors="coerce", utc=True
        ).dt.tz_localize(None)
    now = dt.datetime.now()
    user_stats_30d = filter_logs(
        df,
        equality_filters={"action": "USER_CONNECTION"},
        inequality_filters={"date": [now - dt.timedelta(days=30), now]},
        group_count="id_user",
    )
    user_stats_7d = filter_logs(
        df,
        equality_filters={"action": "USER_CONNECTION"},
        inequality_filters={"date": [now - dt.timedelta(days=7), now]},
        group_count="id_user",
    )
    user_stats_always = filter_logs(
        df,
        equality_filters={"action": "USER_CONNECTION"},
        inequality_filters={"date": [None, now]},
        group_count="id_user",
    )
    return {
        "connections_7d": int(user_stats_7d["count"].sum()),
        "connections_30d": int(user_stats_30d["count"].sum()),
        "connections_always": int(user_stats_always["count"].sum()),
        "users_7d": len(user_stats_7d),
        "users_30d": len(user_stats_30d),
        "users_always": len(user_stats_always),
    }


def get_letter_consultation_stats(df: pd.DataFrame) -> List[Dict[str, object]]:
    def get_quartiles(dataframe: pd.DataFrame) -> Tuple[float, float, float]:
        desc = dataframe["count"].describe().to_dict()
        if np.isnan(desc["25%"]):
            # return {"25%": 0., "75%": 0., "50%":0.}
            return 0.0, 0.0, 0.0
        else:
            return desc["25%"], desc["50%"], desc["75%"]
            # return {"25%": desc["25%"], "75%": desc["75%"], "50%":desc["50%"]}

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"], errors="coerce", utc=True
        ).dt.tz_localize(None)

    now = dt.datetime.now()
    filter_series = []
    consultation_dict = {
        "PDF": "OPEN_PDF",
        "Excel": "OPEN_XLSX",
        "Observe": "OPEN_OBSERVE",
        "SIv2": "OPEN_SIV2",
    }
    # number of times than every user has clicked on consultation button (example:"OPEN PDF") for 30 days
    for name, button in consultation_dict.items():
        consultation_30d = filter_logs(
            df,
            inequality_filters={"date": [now - dt.timedelta(days=180), now]},
            equality_filters={"action": button},
            group_count="id_user",
        )
        v25, v50, v75 = get_quartiles(consultation_30d)
        filter_series.append(
            {
                "name": name,
                "users": len(consultation_30d),
                "25%": v25,
                "50%": v50,
                "75%": v75,
            }
        )

    return filter_series


def get_bean_stats(df: pd.DataFrame) -> List[Dict[str, object]]:
    def get_quartiles(dataframe: pd.DataFrame) -> Tuple[float, float, float]:
        desc = dataframe["count"].describe().to_dict()
        if np.isnan(desc["25%"]):
            # return {"25%": 0., "75%": 0., "50%":0.}
            return 0.0, 0.0, 0.0
        else:
            return desc["25%"], desc["50%"], desc["75%"]
            # return {"25%": desc["25%"], "75%": desc["75%"], "50%":desc["50%"]}

    def build_beans_counter(dataframe: pd.DataFrame) -> pd.DataFrame:
        beans = [
            "site_name",
            "interlocutor_name",
            "theme",
            "sectors",
            "pilot_entity",
            "resp_entity",
            "topics",
            "equipments_trigrams",
            "isotopes",
            "domains",
            "natures",
            "paliers",
            "region",
        ]

        data_array = []

        dataframe["date"] = pd.to_datetime(
            dataframe["date"], errors="coerce", utc=True
        ).dt.tz_localize(None)

        for ind, row in dataframe[dataframe.action == "SEARCH"].iterrows():
            try:
                filters = json.loads(row["details"])["filters"]
                filters["id_user"] = row["id_user"]
                filters["date"] = row["date"]
                data_array.append(filters)
            except Exception:
                pass
        beans_df = pd.DataFrame.from_records(
            data=data_array, columns=np.union1d(beans, ["id_user", "date"])
        )
        for col in beans:
            beans_df[col] = beans_df[col].apply(
                lambda row: len(row) if isinstance(row, Iterable) else 0
            )
        return beans_df

    details = build_beans_counter(df)
    now = dt.datetime.now()
    filter_series = []
    bean_dict = {
        "Catégories": "topics",
        "Nom de site": "site_name",
        "Interlocuteur": "interlocutor_name",
        "Trigramme": "equipments_trigrams",
        "Isotopes": "isotopes",
        "Domaines": "domains",
    }
    # number of times than every user has clicked on consultation button (example:"OPEN PDF") for 30 days
    for name, bean in bean_dict.items():
        beans_30d = filter_logs(
            details,
            inequality_filters={"date": [now - dt.timedelta(days=180), now]},
            difference_filters={bean: 0},
            group_count="id_user",
        )
        v25, v50, v75 = get_quartiles(beans_30d)
        filter_series.append(
            {
                "name": name,
                "users": len(beans_30d),
                "25%": v25,
                "50%": v50,
                "75%": v75,
            }
        )
    return filter_series
