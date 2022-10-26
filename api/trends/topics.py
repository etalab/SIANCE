from datetime import date
from siancedb.models import SessionWrapper, get_active_model_id, SiancedbLabel
import pandas as pd
import elasticsearch as es
import itertools
import altair as alt
from typing import List, Dict, Iterable, Union
import json
import numpy as np
from siancedb.config import get_config
from urllib.parse import unquote

ES = get_config()["elasticsearch"]


class MultiLabelCounter:
    def __init__(self, classes=None):
        self.classes_ = classes

    def fit(self, y):
        self.classes_ = sorted(set(itertools.chain.from_iterable(y)))
        self.mapping = dict(zip(self.classes_, range(len(self.classes_))))
        return self

    def transform(self, y):
        yt = []
        for labels in y:
            data = [0] * len(self.classes_)
            for label in labels:
                data[self.mapping[label]] += 1
            yt.append(data)
        return yt

    def fit_transform(self, y):
        return self.fit(y).transform(y)


def add_nested_allowed_values_clause(
    field, allowed_values: List = [], first_clause=False
):
    """
    Prepare a substring of sql query to select rows where 'field' matches at least one of 'allowed_values'
    ONLY for SQL fields that ARE saved as arrays

    Args:
        field (str): name of sql field to make the restriction on
        allowed_values (List, optional): a list of values of accept for this field. Defaults to [].
        first_clause (bool, optional): if True, the clause begins with "WHERE", otherwise it begins with "AND". Defaults to False.

    Returns:
        str: substring of sql query with the desired 'where' condition
    """

    if not isinstance(allowed_values, Iterable) or isinstance(
        allowed_values, str
    ):  # if the input is not a list/tuple/set/iterable_other_than_str
        if (
            not allowed_values
        ):  # to filter out indesirable values like NaN, None, or empty string
            allowed_values = []
        else:
            allowed_values = [allowed_values]
    allowed_values = list(
        allowed_values
    )  # at this point, the variable is a non-string iterable
    if len(allowed_values) == 0:
        return ""
    else:
        clause = (
            "WHERE " if first_clause else "AND "
        ) + f"('{allowed_values[0]}' = ANY ({field}) "
        for value in allowed_values[1:]:
            clause += f"""OR '{value}' = ANY ({field})"""
        clause += ") "
        return clause


def add_allowed_values_clause(
    field, allowed_values: List = [], first_clause=False
) -> str:
    """
    Prepare a substring of sql query to select rows where 'field ' matches at least one of 'allowed_values'
    ONLY for SQL fields that ARE NOT saved as arrays

    Args:
        field (str): name of sql field to make the restriction on
        allowed_values (List, optional): a list of values of accept for this field. Defaults to [].
        first_clause (bool, optional): if True, the clause begins with "WHERE", otherwise it begins with "AND". Defaults to False.

    Returns:
        str: substring of sql query with the desired 'where' condition
    """
    if not isinstance(allowed_values, Iterable) or isinstance(
        allowed_values, str
    ):  # if the input is not a list/tuple/set/iterable_other_than_str
        if (
            not allowed_values
        ):  # to filter out indesirable values like NaN, None, or empty string
            allowed_values = []
        else:
            allowed_values = [allowed_values]
    allowed_values = list(
        allowed_values
    )  # at this point, the variable is a non-string iterable
    if len(allowed_values) == 0:
        return ""
    elif len(allowed_values) == 1:
        return (
            "WHERE " if first_clause else "AND "
        ) + f"{field} = '{str(allowed_values[0])}' "
    else:
        return (
            "WHERE " if first_clause else "AND "
        ) + f"{field} IN {tuple(allowed_values)}"


def get_topics_count_sql(
    subcategories: List[str], sectors: List[str] = []
) -> pd.DataFrame:
    """
    Take as input a list of subcategories names, and optionally of sectors to apply restrictions, do the corresponding SQL query and return a dataframe

    Args:
        subcategories (List[str]): the list of subcategories for which we want to compute count time series
        sectors (List[str], optional):  A restriction to some sectors ("NPX", "LUDD", etc.). Defaults to [], and apply no restrictions in that case

    Returns:
        pd.DataFrame: a dataframe with the time series of topcis
    """
    if not subcategories:
        return
    id_model = get_active_model_id()
    query = f"""
        SELECT extract( year FROM ape_letters.sent_date )::int as year, COUNT(distinct(ape_predictions.id_letter)), ape_labels.subcategory
        FROM ape_predictions
        JOIN ape_sections ON ape_sections.id_letter = ape_predictions.id_letter
        JOIN ape_letters ON ape_predictions.id_letter = ape_letters.id_letter 
        JOIN ape_labels on ape_predictions.id_label = ape_labels.id_label
        JOIN ape_siv2_letters_metadata ON ape_siv2_letters_metadata.id_metadata = ape_letters.id_letter
        WHERE ape_sections.priority IN (1,2)
            AND ape_predictions.id_model = {id_model}
            AND ape_letters.sent_date > '10/10/2001'
            AND ape_sections.start <= ape_predictions.start 
            AND ape_predictions.end <= ape_sections.end
        """
    query += add_nested_allowed_values_clause(
        field="ape_siv2_letters_metadata.sectors", allowed_values=sectors
    )
    query += add_allowed_values_clause(
        field="ape_labels.subcategory", allowed_values=subcategories
    )
    query += """
        GROUP BY 1, ape_labels.subcategory
    """
    query = query.replace('"', "'")
    with SessionWrapper() as db:
        df = pd.read_sql_query(query, con=db.bind)

    return df.rename(
        columns={"subcategory": "Thématique", "year": "Année", "count": "Occurrences"}
    ).astype({"Année": 'int32'})


def get_themes_count_sql(themes: List[str] = []):
    """
    Take as input a list of theme names, do the corresponding SQL query and return a dataframe

    Args:
        themes (List[str]): the list of themes for which we want to compute count time series

    Returns:
        pd.DataFrame: a dataframe with the time series of the required themes
    """
    query = f"""
        SELECT extract( year FROM date_mail )::int as year, COUNT(*), theme
        FROM ape_siv2_letters_metadata
        WHERE date_mail > '10/10/2001'
    """
    query += add_allowed_values_clause(
        field="theme", allowed_values=themes, first_clause=False
    )
    query += """
        GROUP BY 1, theme
    """

    with SessionWrapper() as db:
        df = pd.read_sql_query(query, con=db.bind)
    query = query.replace('"', "'")

    return df.rename(
        columns={"theme": "Thématique", "year": "Année", "count": "Occurrences"}
    ).astype({"Année": 'int32'})


def get_countchart_json(data: pd.DataFrame, display_sum=False) -> Dict:
    """
    Take as input a formated dataframe with columns "Année", "Thématique", "Occurrences"
    and return all the altair data to display in front

    Args:
        data (pd.DataFrame): a dataframe with the time series of topcis
        display_sum (bool, optional): indicates if a times series summing the counts of all 'Thémartique'
            should be displayed in altair chart. Defaults to False.

    Returns:
        Dict: a json with all the altair data, tooltips, and axes to display with vega in front-end
    """
    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["Année:O"], empty="none"
    )
    selectors = (
        alt.Chart()
        .mark_point()
        .encode(
            x="Année:O",
            opacity=alt.value(0),
        )
        .add_selection(nearest)
    )

    line = (
        alt.Chart()
        .mark_line()
        .encode(
            x="Année:O",
            y="Occurrences:Q",
            color=alt.Color("Thématique:O", scale=alt.Scale(scheme="dark2")),
            # strokeDash="Thématique:O",
            tooltip=["Année:O", "Occurrences", "Thématique"],
        )
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(nearest, "Thématique:O", alt.value(" "))
    )

    # Draw a rule at the location of the selection
    rules = (
        line.mark_rule(color="gray")
        .encode(
            x="Année:O",
        )
        .transform_filter(nearest)
    )
    try:
        if display_sum:
            data_sum = data[["Année", "Occurrences"]].groupby("Année").sum().reset_index()

            line_sum = (
                alt.Chart(data_sum)
                .mark_bar()
                .encode(
                    x="Année:O",
                    y="Occurrences:Q",
                    #     strokeDash=[1,1],
                    opacity=alt.value(0.15),
                    tooltip=["Année:O", "Occurrences"],
                )
            )
            json_content = (
                alt.layer(
                    line_sum,
                    alt.layer(line, line_sum, selectors, points, rules, text, data=data),
                )
              #  .interactive()
                .to_json()
            )
        else:
            json_content = (
                alt.layer(
                    line,
                    selectors,
                    points,
                    rules,
                    text,
                    data=data,
                )
            #    .interactive()
                .to_json()
            )
        json_content = json.loads(json_content)
        return json_content
    except Exception:
        return {}


def get_decreasing_subcategories(data: pd.DataFrame) -> List[str]:
    """
    Take as input a formated dataframe with columns "Année", "Thématique", "Occurrences"

    Args:
        data (pd.DataFrame): the timeseries of the counts of topics

    Returns:
        List: the names of subcategories where counts have recently decreased
    """
    def time_slicing_counts(df: pd.DataFrame, start: int, end: int):
        time_slice = df[(start <= df["Année"]) & (df["Année"] <= end)]
        cumu_counts = time_slice.groupby(["Thématique"]).sum().reset_index()[["Occurrences", "Thématique"]].set_index("Thématique")
        return cumu_counts
    
    def decreasing_topics(old_counts: pd.DataFrame, new_counts: pd.DataFrame) -> List[str]:
        perc_decrease_thresh = -0.30  # example: cumulative counts have decreases of -30%
        # check if (new - old) < threshold * old with threshold being negative
        strong_decrease = (
            new_counts.add(-old_counts, fill_value=0).add(-perc_decrease_thresh*old_counts, fill_value=0)
        ) < 0 
        # also require at least 15 detections on the previous 3-year period
        significant = old_counts.add(-new_counts,fill_value=0).add(new_counts, fill_value=0) >= 15
        return list(strong_decrease[strong_decrease.Occurrences & significant.Occurrences].index.values)
        
    try:
        last_complete_year = date.today().year - 1
        return decreasing_topics(
            old_counts=time_slicing_counts(data, last_complete_year-5, last_complete_year-3),
            new_counts = time_slicing_counts(data, last_complete_year-2, last_complete_year)
        )
    except:
        return []
        

def highlight_topics() -> List[str]:
    with SessionWrapper() as db:
        subcategories = [label.subcategory for label in db.query(SiancedbLabel).all()]
    
    subcategories = [
        unquote(subcategory).replace("'", "''") for subcategory in subcategories
    ]
    return get_decreasing_subcategories(
        get_topics_count_sql(subcategories, sectors=[])
    )
    

def prepare_topics_chart(
    subcategories: List[str] = [], sectors: List[str] = []
) -> Dict:
    """

    Take as input a list of subcategories names, and optionally of sectors to apply restrictions, and return altair time series (in json format) to display in front-end


    Args:
        subcategories (List[str]): the list of subcategories for which we want to compute count time series
        sectors (List[str], optional):  A restriction to some sectors ("NPX", "LUDD", etc.). Defaults to [], and apply no restrictions in that case


    Returns:
        Dict: a json with all the altair data, tooltips, and axes to display with vega in front-end
    """
    subcategories = [
        unquote(subcategory).replace("'", "''") for subcategory in subcategories
    ]  # add escaping rule
    counts = get_topics_count_sql(subcategories, sectors)
    return get_countchart_json(counts, display_sum=False)


def prepare_themes_chart(themes: List = []):
    themes = [unquote(theme).replace("'", "''") for theme in themes]
    counts = get_themes_count_sql(themes)
    return get_countchart_json(counts, display_sum=True)
