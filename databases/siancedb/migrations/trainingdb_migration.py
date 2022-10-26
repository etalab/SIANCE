"""
Itil functions to transform historical annotations into new format and to generate ape_training
"""
import pandas as pd
from siancedb.models import (
    SiancedbLetter,
    SiancedbTraining,
    SiancedbRawAnnotation,
    SessionWrapper,
)
from siancedb.pandas_writer import write_from_pandas
from siancebackend.letter_management.sentencizer import (
    prepare_sentencizer,
    prepare_sentencizer_training,
)
from siancedb.pandas_writer import import_objects_in_pandas
import datetime as dt


def migrate_annotation_df():
    """
    Request annotations saved in database and return them
    Returns:
        pandas.DataFrame: annotations from database, plus a column `topic_subtopic` merging topic and sub_topic fields
    """
    sql_query = (
        f"select * from dw_annotation left join ape_labels on"
        f"(dw_annotation.categorie = ape_labels.category and dw_annotation.sous_categorie = ape_labels.subcategory)"
    )

    with SessionWrapper() as db:
        dw_annotation = pd.read_sql_query(sql_query, con=db.bind)
    dw_annotation = dw_annotation.drop_duplicates().dropna(subset=["id_label"])

    annotations = []
    for _, row in dw_annotation.iterrows():
        name = row["nom_lettre"].replace(".txt", "").strip()
        text = row["terms"]
        start, end = row["start_terms"], row["end_terms"]
        date = dt.date.today()
        id_label = row["id_label"]
        user = 1  # id of admin
        annotations.append([name, id_label, text, start, end, date, user])

    with SessionWrapper() as db:
        write_from_pandas(
            pd.DataFrame(
                data=annotations,
                columns=["name", "id_label", "text", "start", "end", "date", "user"],
            ).drop_duplicates(),
            SiancedbRawAnnotation,
            db,
        )


def get_letters():
    """
    Outdated - Use instead db.query(SiancedbLetter, Session())

    Request letters ("lettres de suites") from PostgreSQL and apply
    basic cleaning before returning them

    Returns:
        pandas.DataFrame: TABLE with (cleaned) lettres de suites content. The primary key is DataFrame index
    """
    table = "ape_letters"
    sql_query = "select id_letter,  text from {}".format(table)
    with SessionWrapper() as db:
        df = pd.read_sql_query(sql_query, con=db.bind)
    return df


def intersect_sentence_terms(
    sentence_start: int, sentence_end: int, terms_start: int, terms_end: int
):
    """
    Using integers marking the boundaries of strings of interest (usually sentences)
    and terms of interest (usually tokens), return True if the bounds of the terms
    intersect the bounds of the sentences.
    As annotations may be imperfect, a margin of 3 characters is considered on the bounds
    of selected tokens
    Example: if the sentence goes from characters 28 to 80, and selected terms from characters 15 to 35,
    the function returns True. Due to the margin, the function also returns True where selected terms goes
    (for example) from characters 15 to 26

    Args:
        sentence_start (int): number of the starting character of the sentence (since the beginning of the letter)
        sentence_end (int): number of the ending character of the sentence (since the beginning of the letter)
        terms_start (int): number of the starting character of the selected terms (since the beginning of the letter)
        terms_end (int): number of the ending character of the selected terms (since the beginning of the letter)

    Returns:
        boolean: True or False
    """
    margin = 5
    # the labelled terms begins in the current sentence (but not in the last `margin` characters)
    if sentence_start <= terms_start < sentence_end - margin:
        return True
    # the current sentence is fully included in the labelled terms
    if terms_start <= sentence_start and sentence_end <= terms_end:
        return True
    # the labelled terms ends in the current sentence (but not in the last `margin` characters)
    if sentence_start < terms_end <= sentence_end:
        return True


def prepare_sentence_labels(letters_df: pd.DataFrame, raw_labels_df: pd.DataFrame):
    """
    This function is used for the creation of the sentences database (today: `ape_training`)
    It uses the table of letters ("lettres de suites") and the table of raw annotations,
    then cut the text of the letters into sentences, and expand labels to complete sentences

    This operation results in a new pandas.DataFrame that is returned

    Example: if a word of the sentence "Il conviendrait d’inscrire les dates limites d’utilisation
    sur les produits de décontamination" has been manually annotated with the label "RP travailleur",
    then the whole sentence is labelled with "RP travailleur"

    This function should still be optimized to save deployment time

    Args:
        letters_df (pd.DataFrame): slice from ape_letters
        raw_labels_df (pd.DataFrame): slice from ape_raw_annotation

    Returns:
        pandas.DataFrame: a table with the 6 columns "id_letter", "sentence",
        "id_label", "terms", "start", "end"
    """

    sentencizer = prepare_sentencizer_training()
    data = []
    for _, letter in letters_df.iterrows():
        doc = sentencizer(letter["text"])  # field name to be changed
        # columns of annotations: name, text, id_label, start, end, date, user
        letter_annotations = raw_labels_df[raw_labels_df["name"] == letter["name"]]
        for sentence in doc.sents:
            # if an annotation is inside a sentence, labellize the whole sentence
            for _, label in letter_annotations.iterrows():
                if intersect_sentence_terms(
                    sentence.start_char,
                    sentence.end_char,
                    label["start"],
                    label["end"],
                ):
                    data.append(
                        [
                            letter["name"],
                            label["id_label"],
                            sentence.text,
                            sentence.start_char,
                            sentence.end_char,
                            label["date"],
                        ]
                    )
    return pd.DataFrame(
        data=data,
        columns=["name", "id_label", "sentence", "start", "end", "date"],
    ).drop_duplicates()


def build_training():
    """
    Fill ape_training with annotated sentences. When some words in a sentence were annotated with a given label
    (in the historical database), the whole sentence gets the label

    """
    with SessionWrapper() as db:
        letters_df = import_objects_in_pandas(SiancedbLetter, db)
        raw_labels_df = import_objects_in_pandas(SiancedbRawAnnotation, db)
    prepared_df = prepare_sentence_labels(letters_df, raw_labels_df)
    with SessionWrapper() as db:
        write_from_pandas(prepared_df, SiancedbTraining, db)
    print("Finished writing {} entries in {}".format(len(prepared_df), "ape_training"))


if __name__ == "__main__":
    # migrate_annotation_df()
    build_training()
