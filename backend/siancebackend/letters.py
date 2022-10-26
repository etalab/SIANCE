"""

Parse letters content and save it in the letters SIANCE TABLE

"""

import os

import pandas as pd

import logging

from siancebackend.pipe_logger import update_log_state
from siancebackend.letter_management.letter_cleaning import (
    clean_text_content,
    extract_codep,
    extract_sent_date,
)


from siancedb.models import (
    Session,
    SessionWrapper,
    SiancedbLetter,
    SiancedbDocument,
    SiancedbDWLettre,
    UNKNOWN,
)

from siancedb.pandas_writer import chunker

from siancedb.config import get_config

from tika import parser

logger = logging.getLogger("letters")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/letters.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

CONFIG = get_config()
SIV2 = get_config()["siv2"]


def build_one_letter(pdf_path: str, already_seen=None):
    """
    This is the main function of this document.
    It builds the letter / doc / metadata / interlocutor
    using the info passed as arguments.
    This function checks the letter is not already in the database

    """
    if already_seen is None:
        already_seen = set()

    # PARSE PDF WITH TIKA
    url_tika_local = f"http://{CONFIG['tika']['host']}:{CONFIG['tika']['port']}"
    raw = parser.from_file(pdf_path, url_tika_local)
    # Exclude scanned PDF (content = None) and PDF with encodings that TIKA does not know
    if (
        raw["content"] is not None
        and raw["metadata"].get("producer") is not None
        and not raw["metadata"].get("producer").startswith("Jaws")
    ):
        text = raw["content"]
    else:
        text = ""
    # filename is the text before the extension
    name = os.path.basename(pdf_path)[:-4]
    nb_pages = raw["metadata"].get("xmpTPg:NPages")

    logger.debug(f"Building letter {name}")

    # CODEP is a mandatory field. If is unknown, take the default value UNKNOWN
    codep = extract_codep(text)
    if codep is None:
        codep = UNKNOWN

    date_sent_letter = extract_sent_date(text)

    # Création des documents
    doc = SiancedbDocument(
        name=name,
        user=1,  #  superuser
        nature="INS-LETTER",
    )

    letter = SiancedbLetter(
        name=name,
        text=clean_text_content(text),
        codep=codep,
        sent_date=date_sent_letter,
        nb_pages=int(nb_pages or 0),
        document=doc,
    )

    if name in already_seen:
        logger.info(
            f"Not adding {name} because it has already been seen and saved in base"
        )
        return letter, True
    else:
        already_seen.add(name)
        return letter, False


def build_letters(db: Session, pipe_logger=None):
    """

    Args:
        db (Session): a Session to connect to the database
        pipe_logger (SiancedbPipeline): an object logging in PostgreSQL the advancement of data ingestion steps

    """

    already_seen = db.query(SiancedbLetter.name).all()
    already_seen = set(row[0] for row in already_seen)
    logger.debug(f"How many letter ids already in base: {len(already_seen)}")

    documents_list = [
        filename
        for filename in os.listdir(CONFIG["letters"]["data"]["letters_pdf"])
        if filename[:-4] not in already_seen
    ]

    n_documents = len(documents_list)
    letters_count = 0
    chunk_size = 100
    letters = []
    for chunk in chunker(chunk_size, documents_list):
        logger.info("Starting new chunk of data")

        for filename in chunk:
            letter, is_old = build_one_letter(
                f"{CONFIG['letters']['data']['letters_pdf']}/{filename}",
                already_seen,
            )
            if not is_old:
                db.add(letter)
                letters.append(letter)
        letters_count += chunk_size
        update_log_state(
            pipe=pipe_logger, progress=letters_count / n_documents, step="letters"
        )
        logger.info("Letters chunk built")
        db.commit()
        logger.info("Letters chunk committed")
    return letters


def build_old_letters_df():
    try:
        with SessionWrapper() as db:
            id_letters_df = pd.DataFrame(
                data=list(
                    db.query(SiancedbDWLettre.id_lettre, SiancedbDWLettre.nom_lettre)
                    .distinct(SiancedbDWLettre.nom_lettre)
                    .all()
                ),
                columns=["id_lettre", "nom_lettre"],
            )
            id_letters_df.id_lettre = id_letters_df.id_lettre.astype(int)
            id_letters_df.nom_lettre = id_letters_df.nom_lettre.str.replace(".txt", "")
            return id_letters_df
    except Exception as e:
        return pd.DataFrame()
