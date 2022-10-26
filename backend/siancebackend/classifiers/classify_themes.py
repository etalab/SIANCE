import os
import pandas as pd
import numpy as np
import pickle
from typing import Iterable
import spacy
from sklearn.preprocessing import LabelEncoder
from sklearn import linear_model, neural_network, base
from sklearn.multiclass import OneVsOneClassifier, OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from siancedb.config import get_config

from siancedb.models import (
    UNKNOWN,
    Session,
    SessionWrapper,
    SiancedbLetter,
    SiancedbSection,
    SiancedbPredictedMetadata,
)


from siancedb.pandas_writer import write_from_pandas, import_objects_in_pandas, chunker

from siancebackend.letter_management.sentencizer import prepare_sentencizer
from siancebackend.classifiers.embeddings import get_embeddings_sentences
from siancebackend.pipe_logger import update_log_state

import logging

logger = logging.getLogger("classify-themes")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/classify_themes.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

path_themes = "ape_first_sentences.pkl"
path_embeddings = "first_sentences_embeddings.npy"


def train_themes(embeddings=None, themes=None):
    if embeddings is None:
        embeddings = np.load(
            os.path.join(
                get_config()["learning"]["themes_models"],
                "first_sentences_embeddings.npy",
            )
        )
    if themes is None:
        themes = pd.read_pickle(
            os.path.join(
                get_config()["learning"]["themes_models"], "ape_first_sentences.pkl"
            ).theme.values
        )

    embeddings = embeddings[themes != UNKNOWN]
    themes = themes[themes != UNKNOWN]

    encoder = LabelEncoder()
    themes_encoded = encoder.fit_transform(themes)

    x_train, x_test, y_train, y_test = train_test_split(
        embeddings, themes_encoded, train_size=0.75, random_state=42
    )
    model = OneVsRestClassifier(neural_network.MLPClassifier())
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    score = accuracy_score(y_test, y_pred)
    logger.info(f"Global score of the toy model for theme classification: {score}")

    classifier_path = os.path.join(
        get_config()["learning"]["themes_models"], "themes_classifier.pkl"
    )
    with open(classifier_path, "wb") as file:
        pickle.dump(model, file)

    encoder_path = os.path.join(
        get_config()["learning"]["themes_models"], "themes_encoder.pkl"
    )
    with open(encoder_path, "wb") as file:
        pickle.dump(encoder, file)


def prepare_classifier_encoder():
    encoder_path = os.path.join(
        get_config()["learning"]["themes_models"], "themes_encoder.pkl"
    )
    with open(encoder_path, "rb") as file:
        encoder = pickle.load(file)

    classifier_path = os.path.join(
        get_config()["learning"]["themes_models"], "themes_classifier.pkl"
    )
    with open(classifier_path, "rb") as file:
        classifier = pickle.load(file)
    return classifier, encoder


def build_themes(db: Session, pipe_logger=None):
    classifier, encoder = prepare_classifier_encoder()
    # load a dataframe of sections
    with SessionWrapper() as database:
        sections_df = import_objects_in_pandas(SiancedbSection, database)

    # load letters generator
    query = db.query(SiancedbLetter).filter(~SiancedbLetter.metadata_dyn.any())
    letters = query.all()
    n_documents = query.count()

    letters_count = 0
    for chunk_letters in chunker(1000, letters):
        chunk_df = pd.DataFrame(
            [(letter.id_letter, letter.text) for letter in chunk_letters],
            columns=["id_letter", "text"],
        )
        letters_count += len(chunk_df)

        logger.debug("Start new chunk of predictions")

        metadata_df = classify_themes(
            classifier=classifier,
            encoder=encoder,
            letters_df=chunk_df,
            sections_df=sections_df[
                sections_df.id_letter.isin(chunk_df.id_letter.values)
            ],
        )

        write_from_pandas(metadata_df, SiancedbPredictedMetadata, db)
        update_log_state(
            pipe=pipe_logger,
            progress=letters_count / n_documents,
            step="predicted_metadata",
        )


def classify_themes_one_letter(
    letter: SiancedbLetter,
    sections: Iterable[SiancedbSection],  # sections of the same letter
    classifier: base.BaseEstimator,
    encoder: LabelEncoder,
    sentencizer: spacy.language.Language,
) -> SiancedbPredictedMetadata:
    start, end = None, None
    for section in sections:
        if section.priority == 0 and section.id_letter == letter.id_letter:
            start, end = section.start, section.end

    if start is None or end is None:
        # cannot predict themes if there is no synthesis (according to the current model)
        return None
    synthesis = letter.text[start:end]
    first_sentence = next(sentencizer(synthesis).sents).text
    embeddings = get_embeddings_sentences([first_sentence])
    y_pred = classifier.predict(embeddings)
    theme = encoder.inverse_transform(y_pred)[0]
    return SiancedbPredictedMetadata(id_letter=int(letter.id_letter), theme=str(theme))


def classify_themes(classifier, encoder, letters_df, sections_df, sentencizer=None):
    """
    This function is used to predict the theme of a letter from the first sentence of synthesis
    The sentencizing step (slow step) is performed sentence by sentence,
     while the embedding and the theme predictions steps (quicker steps) are performed directly on a batch

    Args:
        encoder (sklearn.preprocessing.LabelEncoder): encode-decode the themes categories into sklearn classes
        classifier (sklearn.base.BaseEstimator): a trained sklearn classifier
        letters_df (pandas.DataFrame): structured as the table `ape_letters`
        sections_df (pandas.DataFrame): structured as the table `ape_sections`

    Returns:
        pandas.DataFrame: a table with the 2 columns "id_letter", "theme"
    """
    if sentencizer is None:
        sentencizer = prepare_sentencizer()

    # loop to extract first sentences of synthesis, when there is one
    first_sentences = []
    # the mask is True when we succeed in extracting the first sentence of the synthesis
    # the id_letters list here should equal to `letters_df.id_letter`
    mask, id_letters = [], []
    for _, letter in letters_df.iterrows():
        # the starting and the ending characters of the synthesis section (reminder: synthesis <=> priority=0)
        id_letters.append(letter.id_letter)
        try:
            bounds = sections_df[
                (sections_df.id_letter == letter.id_letter)
                & (sections_df.priority == 0)
            ][["start", "end"]].values[0]
            start, end = bounds
            synthesis = letter.text[start:end]
            first_sentence_synthesis = next(sentencizer(synthesis).sents).text
            first_sentences.append(first_sentence_synthesis)
            mask.append(True)
        except:
            mask.append(False)

    # predict themes for the letters having a synthesis including at least one sentence...
    embeddings = get_embeddings_sentences(first_sentences)
    y_pred = classifier.predict(embeddings)
    themes_pred = encoder.inverse_transform(y_pred)
    # fill `metadata_df` with the predicted themes, or empty string where there is no predicted theme
    # warning: dtype=object enables to have regular strings, while dtype=str only keeps the first character!
    themes_pred_padded = np.zeros(len(letters_df), dtype=object)
    # the lists `id_letters` and `themes_pred_padded` are synchronized by construction
    themes_pred_padded[mask] = themes_pred
    themes_df = pd.DataFrame(
        data={"id_letter": id_letters, "theme": themes_pred_padded}
    )
    return themes_df
