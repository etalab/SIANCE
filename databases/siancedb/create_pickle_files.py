import pandas as pd, os, json, sys
from siancedb.models import (
    SiancedbIsotope,
    SiancedbLabel,
    SiancedbLetter,
    SiancedbTraining,
    SessionWrapper,
    SiancedbDocument,
    SiancedbSection,
    SiancedbDemand,
    SiancedbPrediction,
    SiancedbInterlocutor,
    SiancedbSIv2LettersMetadata,
    SiancedbModel,
    SiancedbTrigram,
)
from siancedb.config import get_config
from siancedb.pandas_writer import import_objects_in_pandas, write_from_pandas


def save_to_pickle(orm_object, path: str):
    """
    Save the database table to a pickle file.
    """
    with SessionWrapper() as db:
        df = import_objects_in_pandas(orm_object, db)
        df.to_pickle(path)


def load_from_pickle(orm_object, path: str):
    """
    Write pickle file to the database
    """
    with SessionWrapper() as db:
        try:
            df = pd.read_pickle(path)
        except:
            raise ValueError(f"Did you save the pickle to the path {path} ?")
        write_from_pandas(df, orm_object, db)


picklepath = get_config()["learning"]["pickles"]
TABLES = {
    name: (orm_object, os.path.join(picklepath, f"{name}.pkl"))
    for (orm_object, name) in [
        (SiancedbLabel, "ape_labels"),
        (SiancedbTraining, "ape_training"),
        (SiancedbLetter, "ape_letters"),
        (SiancedbDocument, "ape_documents"),
        (SiancedbPrediction, "ape_predictions"),
        (SiancedbDemand, "ape_demands"),
        (SiancedbSection, "ape_sections"),
        (SiancedbModel, "ape_models"),
        (SiancedbInterlocutor, "ape_interlocutors"),
        (SiancedbSIv2LettersMetadata, "ape_siv2"),
        (SiancedbTrigram, "ape_trigrams"),
        (SiancedbIsotope, "ape_isotopes"),
    ]
}
