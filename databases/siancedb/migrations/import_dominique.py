"""

"""

import pandas as pd
import numpy as np

from siancedb.models import (
    SessionWrapper,
    SiancedbThemeValorisation,
)


def import_dominique_csv(path: str = "../Prototypage/dominique_utf8.csv"):
    """
    /!/ Do not run this script several times /!/
    Imports the csv file from Dominique into the table
    ape_theme_valorisation
    """
    df = pd.read_csv(path, sep=";")

    # What null values are expected
    nullValues = [np.nan, None, "Non précisé", "Non exploitable", "", " "]

    def parse_possible_list(text: str):
        """Values in the csv file
        are not well formated.
        Sometimes it is None,
        sometimes it is REP
        sometimes it is REP,LUDD
        Where in all cases it should have type
        list
        """
        if text in nullValues:
            return []
        elif "," not in text:
            return [text.strip()]
        else:
            return [x.strip() for x in text.split(",")]

    def parse_text(text: str):
        """Replace null values
        with the default null/non-observable
        value of our database
        which is Inconnu·e·s
        """
        if text in nullValues:
            return "Inconnu·e·s"
        else:
            return text

    with SessionWrapper() as db:
        # pylint: disable=maybe-no-member
        db.add_all(
            (
                SiancedbThemeValorisation(
                    raw_theme=parse_text(d["raw_theme"]),
                    domain=parse_possible_list(d["domain"]),
                    cleaned_theme=parse_text(d["cleaned_theme"]),
                    group=parse_text(d["group"]),
                    subgroup=parse_text(d["subgroup"]),
                    concept=parse_text(d["concept"]),
                    subconcept=parse_text(d["subconcept"]),
                )
                for d in df.to_dict(orient="records")
            )
        )
        # pylint: disable=maybe-no-member
        db.commit()
