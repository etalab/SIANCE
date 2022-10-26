import pandas as pd
import re
import numpy as np
from siancebackend.pipe_logger import update_log_state

from siancedb.models import Session, SessionWrapper, SiancedbLetter, SiancedbTrigram
from siancedb.pandas_writer import chunker
from siancedb.config import get_config

import logging

logger = logging.getLogger("trigrams")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/trigrams.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

CONFIG = get_config()


def build_trigrams(db: Session, pipe_logger=None):
    """
    For all letters for which no trigrams have been extracted, try to extract them and save them in the database
    Problem: A letter may contain no trigrams, so this function may often be called on these letters

    Args:
        db (Session): a Session to connect to the database
        pipe_logger (SiancedbPipeline): an object logging in PostgreSQL the advancement of data ingestion steps. Defaults to None
    """
    # filter letters for which trigrams have never been extracted yet.
    query = db.query(SiancedbLetter).filter(~SiancedbLetter.trigrams.any())
    letters = query.all()
    n_documents = query.count()

    trigrams_ref = get_edf_trigrams_ref()

    letters_count = 0
    for chunk_letters in chunker(100, letters):
        logger.info("Starting new chunk of letters for extracting trigrams")
        chunk_trigrams = []
        for letter in chunk_letters:
            db_trigrams = build_trigrams_one_letter(letter, trigrams_ref)
            chunk_trigrams.extend(db_trigrams)
        db.add_all(chunk_trigrams)
        logger.info("Trigrams chunk built")

        letters_count += 100
        update_log_state(
            pipe=pipe_logger, progress=letters_count / n_documents, step="trigrams"
        )

        db.commit()
        logger.info("Trigrams chunk committed")


def get_edf_trigrams_ref():
    edf_trigrams_df = pd.read_excel(
        CONFIG["letters"]["trigrams"]["edf"], engine="openpyxl"
    )
    cleaned_trigrams_df = clean_edf_trigrams(edf_trigrams_df)
    return cleaned_trigrams_df


def clean_edf_trigrams(trigrams_df: pd.DataFrame):
    """
    Read the `trigrams referentiel` excel, check its format, extract trigrams without duplicates
    and return a table of possible trigrams to search in documents

    Args:
        trigrams_df (pd.DataFrame): the raw table from the `trigrams referentiel` excel

    Returns:
        pd.DataFrame: the cleaned table of trigrams
    """
    pattern = r"[A-Z]{3}"
    trigram_column = "Code"
    full_name_column = "Libellé"
    assert (
        trigram_column in trigrams_df.columns
        and full_name_column in trigrams_df.columns
    ), f"The referentiel must contain at least the columns {trigram_column} and {full_name_column}"
    trigrams_df = trigrams_df.dropna(subset=[trigram_column])
    trigrams_df[trigram_column] = trigrams_df[trigram_column].str.strip()
    mask = trigrams_df[trigram_column].str.match(pattern, case=True, na=False)
    mask.loc[
        trigrams_df[trigram_column] == "STE"
    ] = False  # deactivate trigram "STE" due to homonyms
    mask.loc[
        trigrams_df[trigram_column] == "STR"
    ] = False  # deactivate "STR" due to ambiguity with "Strasbourg"
    mask.loc[
        trigrams_df[trigram_column] == "DSI"
    ] = False  # deactivate "DSI" due to several homonyms
    # the deactivation above is done in source code instead of referentiel file, as we do not control this input
    return trigrams_df[mask].drop_duplicates(subset=trigram_column)


def extract_edf_trigrams(text: str, cleaned_trigrams_df: pd.DataFrame):
    """
    Extract (without duplicates) all the EDF trigrams mentioned in a text, and return the list
    of concerned trigrams and their `Libellé`
    Nota Bene: the casing is important. Trigrams are supposed to be uppercase in the text,

    Args:
        text (str): a text (in its original casing) that may contain trigrams
        cleaned_trigrams_df (pd.DataFrame): the cleaned table of trigrams

    Returns:
        list[str], list[str]: the list of trigrams fomound in the text,
            and the corresponding full names (`Libellé`)
    """
    trigram_column = "Code"
    full_name_column = "Libellé"
    trigrams_list = cleaned_trigrams_df[trigram_column].unique()
    trigrams_dict = cleaned_trigrams_df.set_index(trigram_column).to_dict("index")
    # force the presence of blanks before and after the trigram (to avoid upper-case names containing these letters)
    patterns = [r"[^A-Za-z0-9]" + trigram + "[^A-Za-z0-9]" for trigram in trigrams_list]
    trigrams_pattern = r"|".join(patterns)
    text = re.sub(
        r"\s", " ", text
    )  # in order not to consider the 'n' in '\n' to be alphanumeric
    text = (
        " " + text + " "
    )  # in order to manage the (rare) case of trigrams at the very beginning or end of the text
    candidate_trigrams = re.findall(pattern=trigrams_pattern, string=" " + text + " ")
    # the previously extracted trigrams may contain special characters before or after the trigram. ex: "SEC".
    # the following line keeps ony the real trigram letters inside these candidates
    found_trigrams = re.findall(
        pattern=r"|".join(trigrams_list), string=" ".join(candidate_trigrams)
    )  # in the
    found_trigrams = np.unique([trigram.strip() for trigram in found_trigrams])
    found_full_names = [
        trigrams_dict[trigram][full_name_column] for trigram in found_trigrams
    ]
    return found_trigrams, found_full_names


def build_trigrams_one_letter(
    letter: SiancedbLetter, cleaned_trigrams_df: pd.DataFrame
):
    """
    Given a letter about REP, extract all the EDF trigrams mentioned in it,
        and return a list of SiancedbTrigram instances

    Args:
        letter (SiancedbLetter): an instance of letter model
        cleaned_trigrams_df (pd.DataFrame): a dataframe with the columns "Code" and "Libellé"
            containing all possible trigrams and their full names

    Returns:
        list[SiancedbTrigram] :the EDF trigrams mentioned in the letter content
    """

    # TODO: the lines below about the sectors must be adapted when we have trigrams for all sectors
    try:
        sectors = letter.metadata_si.sectors
    except:
        sectors = []
    db_trigrams = []

    if "REP" in sectors:
        logger.debug(f"SECTOR REP was found in {sectors}")
        found_trigrams, found_full_names = extract_edf_trigrams(
            letter.text, cleaned_trigrams_df
        )
    else:
        logger.debug(f"SECTOR REP was not in {sectors}")
        found_trigrams, found_full_names = [], []

    for k, trigram in enumerate(found_trigrams):
        trigram_full_name = found_full_names[k]
        db_trigrams.append(
            SiancedbTrigram(
                id_letter=letter.id_letter,
                trigram=trigram,
                trigram_full_name=trigram_full_name,
            )
        )
    return db_trigrams
