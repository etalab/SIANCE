import numpy as np
from typing import Iterable
import time
import os
from siancedb.config import get_config
from siancedb.models import (
    SessionWrapper,
    SiancedbTraining,
)
from siancedb.pandas_writer import (
    import_objects_in_pandas,
)
from sentence_transformers import SentenceTransformer

# logger
import logging

logger = logging.getLogger("embeddings")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("logs/embeddings.log")


def get_embeddings_sentences(sentences: Iterable[str]) -> np.array:
    """Compute embeddings at the scope of the sentence
    Today this function is using a multilingual sentence transformer

    Args:
        sentences (Iterable[str]): list of sentences to be embedded

    Returns:
        numpy.array[numpy.array[float]]: list of vectors of embeddings (one vector per sentence)
    """
    # The `distiluse-base-multilingual-cased` model supports many languages including English and French
    embedder = SentenceTransformer("distiluse-base-multilingual-cased")
    # embedder = SentenceTransformer("paraphrase-multilingual-mnpet-base-v2") # could be the new best embedding model for us. Must be tested December 2021
    embeddings = embedder.encode(sentences)
    return embeddings


def recompute_embeddings():
    recompute_embeddings_mono_output()
    recompute_embeddings_multi_output()


def recompute_embeddings_multi_output():
    """
    This function pre-compute embeddings for all the training sentences,
    and save them at the dedicated location on the disk.
    If the training set has been significantly modified, this function can be called
    before training or evaluating new models.
    """
    with SessionWrapper() as db:
        training_df = import_objects_in_pandas(SiancedbTraining, db)
        # the `groupby` hereby is necessary to group labels defined on the same sentence
        training_df = (
            training_df.groupby(["name", "start", "end", "sentence"])["id_label"]
            .apply(list)
            .reset_index()  # the output DataFrame have columns id_label, name, start, end, sentence
        )
        sentences = training_df.sentence.values
        multi_id_labels = training_df.id_label.values
        del training_df

    # path of the folder where to save the regenerated embeddings
    base_path = get_config()["learning"]["precomputed"]
    time_embed = time.time()
    embeddings = get_embeddings_sentences(sentences)
    logger.info(
        "Time to create the required embeddings: {0:.2f}".format(
            time.time() - time_embed
        )
    )
    np.save(os.path.join(base_path, "multi_output_embeddings.npy"), embeddings)
    np.save(os.path.join(base_path, "multi_output_labels.npy"), multi_id_labels)


def recompute_embeddings_mono_output():
    """
    This function pre-compute embeddings for all the training sentences,
    and save them at the dedicated location on the disk.
    If the training set has been significantly modified, this function can be called
    before training or evaluating new models.
    """
    with SessionWrapper() as db:
        training_df = import_objects_in_pandas(SiancedbTraining, db)
        sentences = training_df.sentence.values
        id_labels = training_df.id_label.values
        del training_df

    basepath = get_config()["learning"]["precomputed"]
    time_embed = time.time()
    embeddings = get_embeddings_sentences(sentences)
    logger.info(
        "Time to create the required embeddings: {0:.2f}".format(
            time.time() - time_embed
        )
    )
    np.save(os.path.join(basepath, "mono_output_embeddings.npy"), embeddings)
    np.save(os.path.join(basepath, "mono_output_labels.npy"), id_labels)
