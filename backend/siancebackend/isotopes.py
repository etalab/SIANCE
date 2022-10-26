import pandas as pd
import re
from typing import List, Dict

from siancedb.models import Session, SiancedbLetter, SiancedbIsotope
from siancebackend.letter_management import normalize_text

from siancedb.pandas_writer import chunker
from siancedb.config import get_config

import logging


logger = logging.getLogger("isotopes")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/isotopes.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

CONFIG = get_config()


def get_isotopes_ref():
    return pd.read_excel(CONFIG["letters"]["isotopes"], engine="openpyxl")


def extract_isotopes(text: str, isotopes_ref: pd.DataFrame) -> List[Dict]:
    """
    Extract (without duplicates) all the isotopes in a text, and return the list
    of dictionaries with keys "mass number" and "symbol"

    Args:
        text (str): a text (in its original casing) that may contain isotopes
        isotopes_ref (pd.DataFrame): the table of isotopes (mass number, symbol, element name)

    Returns:
        list[dict]: a list of the isotopes found with no ambiguity in the letter
        (dictionaries with keys "mass number" and "symbol")
    """

    def get_variants(
        symbol: str, mass_number: int, element_name: str, other_name: str = None
    ):

        """
        Return a list of acceptable designations for a given radioisotope
        """
        element_name = element_name.lower()
        symbol = symbol.lower()
        if other_name and not pd.isna(other_name):
            other_name = other_name.lower()
        names = [
            r"[^A-Za-z0-9]"
            + element_name
            + str(mass_number),  # cobalt60, after a non-alphanumeric character
            r"[^A-Za-z0-9]"
            + element_name
            + " "
            + str(mass_number),  # cobalt 60, after a non-alphanumeric
            r"[^A-Za-z0-9]"
            + element_name
            + "-"
            + str(mass_number),  # cobalt-60, after a non-alphanumeric
            str(mass_number) + element_name,  # 60cobalt
            str(mass_number) + " " + element_name,  # 60 cobalt
            str(mass_number) + "-" + element_name,  # 60-cobalt
        ]
        number_strings = [
            r"[^A-Za-z0-9]"
            + symbol
            + str(mass_number),  # co60, after a non-alphanumeric character
            r"[^A-Za-z0-9]"
            + symbol
            + " "
            + str(mass_number),  # co 60, after a non-alphanumeric
            r"[^A-Za-z0-9]"
            + symbol
            + "-"
            + str(mass_number),  # co-60, after a non-alphanumeric
            str(mass_number) + symbol + r"[^A-Za-z0-9]",  # 60co
            str(mass_number) + " " + symbol + r"[^A-Za-z0-9]",  # 60 co
            str(mass_number) + "-" + symbol + r"[^A-Za-z0-9]",  # 60-co
        ]
        if other_name and not pd.isna(other_name):
            # example of other_name: 'tritium' is usual name for 'hydrogen 3' (and is rarely called 'tritium 3')
            return names + number_strings + [other_name]
        else:
            return names + number_strings

    def extract_isotope(text, row):
        symbol_column = "Symbole"
        mass_number_column = "Numéro de masse isotope"
        name_column = "Élément"
        other_name_column = "Autre nom isotope"
        pattern = normalize_text(
            "|".join(
                get_variants(
                    row[symbol_column],
                    row[mass_number_column],
                    row[name_column],
                    row[other_name_column],
                )
            )
        )
        if re.search(pattern, text):  # compare strings in lowercase and ignore accents
            return {
                "mass number": int(row[mass_number_column]),
                "symbol": row[symbol_column],
            }  # example: {"mass number": 60, "symbol": "Co"}
        else:
            return None

    text_lower = normalize_text(text)
    return list(
        filter(
            None,
            [extract_isotope(text_lower, row) for _, row in isotopes_ref.iterrows()],
        )
    )


def build_isotopes_one_letter(
    letter: SiancedbLetter, isotopes_ref: pd.DataFrame
) -> List[SiancedbIsotope]:
    """
    Given a letter, extract all the mentioned isotopes names mentioned in it.
        Note that the number of mass of the isotope must be mentioned

    Args:
        letter (SiancedbLetter): an instance of letter model
        isotopes_ref (pd.DataFrame): a dataframe with the columns
        "Symbole, "Élément" and "Numéro de masse isotope"

    Returns:
        list[SiancedbIsotope] :the list of isotopes
    """

    found_isotopes = extract_isotopes(letter.text, isotopes_ref)

    return [
        SiancedbIsotope(
            id_letter=letter.id_letter,
            mass_number=isotope_dict["mass number"],
            symbol=isotope_dict["symbol"],
        )
        for isotope_dict in found_isotopes
    ]


def build_isotopes(db: Session):
    """
    For all letters for which no isotopes have been extracted, try to extract them and save them in the database
    Problem: A letter may contain no isotopes, so this function may often be called on these letters

    Args:
        db (Session): a Session to connect to the database
    """
    # filter letters for which isotopes have never been extracted yet.
    query = db.query(SiancedbLetter).filter(~SiancedbLetter.isotopes.any())
    letters = query.all()
    referential_df = get_isotopes_ref()

    for chunk_letters in chunker(100, letters):
        logger.info("Starting new chunk of letters for extracting isotopes")
        chunk_isotopes = []
        for letter in chunk_letters:
            db_isotopes = build_isotopes_one_letter(letter, referential_df)
            chunk_isotopes.extend(db_isotopes)
        db.add_all(chunk_isotopes)
        logger.info("Isotopes chunk built")
        db.commit()
        logger.info("Isotopes chunk committed")
