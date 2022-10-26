from itertools import takewhile, starmap, islice, repeat
import pandas as pd

# operator.truth is *significantly* faster than bool for the case of
# exactly one positional argument
from operator import truth

from siancedb.models import Session


def write_from_pandas(df, objectCreator, db: Session):
    """Takes a pandas DataFrame and
    insert it in the database.
        df: pandas dataframe
        objectCreator: one of the ORM objects of SQLALCHEMY
    """
    try:
        db.add_all(objectCreator(**d) for d in df.to_dict(orient="records"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def import_objects_in_pandas(objectCreator, db: Session):
    """Builds the pandas dataframe of all letters
    pandas dataframe ready to be used.

    objectCreator: one of the ORM  objects of SQLALCHEMY
    """
    return pd.read_sql(db.query(objectCreator).statement, db.bind)


def chunker(n: int, iterable):
    """
    Builds a generator that returns a generator of « chunks »
    of size n or less for the (eventual) last chunk.
    This is particularly usefull for bulk insert in
    databases.
    """
    return takewhile(truth, map(tuple, starmap(islice, repeat((iter(iterable), n)))))
