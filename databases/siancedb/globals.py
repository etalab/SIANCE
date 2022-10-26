from siancedb.models import Base, Session, SiancedbUser
from sqlalchemy import create_engine, select, MetaData

import itertools

import getpass


def create_all_tables():
    """
    Tries to create all the tables
    in the database.

    This operation is idempotent: running it twice
    does nothing, and running it on tables
    already existing does nothing.
    """
    Base.metadata.create_all()


def cleanup_dabatases(db: Session):
    tables_to_drop = [
        "ape_predictions",
        "ape_trigrams",
        "ape_isotopes",
        "ape_demands",
        "ape_sections",
        "ape_siv2_letters_metadata",
        "ape_letters",
        "ape_documents",
        "ape_interlocutors",
        "ape_predicted_metadata",
    ]
    for tablename in tables_to_drop:
        db.execute(f"DROP TABLE {tablename} CASCADE")
    db.commit()


def cleanup_prod_dabatases(db: Session):
    tables_to_drop = [
        "ape_labels",
        "ape_models",
        "ape_documents",
        "ape_interlocutors",
        "ape_cres",
        "ape_trigrams",
        "ape_isotopes",
        "ape_predicted_metadata",
        "ape_letters",
        "ape_siv2_letters_metadata",
        "ape_raw_annotation",
        "ape_training",
        "ape_predictions",
        "ape_demands",
        "ape_sections",
    ]
    for tablename in tables_to_drop:
        db.execute(f"DROP TABLE {tablename} CASCADE")
    db.commit()


def fill_databases_from_preprod_to_prod():
    # FIXME: does not use config files
    tables_to_fill = [
        "ape_labels",
        "ape_models",
        "ape_documents",
        "ape_interlocutors",
        "ape_letters",
        "ape_trigrams",
        "ape_isotopes",
        "ape_predicted_metadata",
        "ape_siv2_letters_metadata",
        "ape_raw_annotation",
        "ape_training",
        "ape_predictions",
        "ape_demands",
        "ape_sections",
        "ape_cres",
    ]
    password_prod = getpass.getpass("Prod password: ")
    password_preprod = getpass.getpass("Preprod password: ")

    def pg_access_url(u, p, host):
        return f"postgresql://{u}:{p}@{host}:5432/siancedb"

    engine_preprod = create_engine(
        pg_access_url("siance", password_preprod, "192.168.210.171")
    )
    engine_prod = create_engine(
        pg_access_url("siance", password_prod, "192.168.210.198")
    )

    meta_prod = MetaData()
    meta_prod.reflect(bind=engine_prod)

    meta_preprod = MetaData()
    meta_preprod.reflect(bind=engine_preprod)

    with engine_prod.connect() as conn_prod:
        with engine_preprod.connect() as conn_preprod:
            for table in tables_to_fill:
                print("Filling table {}".format(table))
                prod_table = meta_prod.tables[table]
                preprod_table = meta_preprod.tables[table]
                data = (
                    dict(row) for row in conn_preprod.execute(select(preprod_table.c))
                )
                args = [iter(data)] * 1000
                for chunk in itertools.zip_longest(*args, fillvalue=None):
                    u = tuple(chunk)
                    if u[-1] is None:
                        u = [x for x in u if x is not None]

                    conn_prod.execute(prod_table.insert().values(u))
