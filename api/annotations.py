# utils for annotations
# copied from our backend respository 

import numpy as np
import pickle
from spacy.lang.fr import French
from sklearn.pipeline import Pipeline
from typing import Iterable
from sentence_transformers import SentenceTransformer

def load_pipeline(model_path: str) -> Pipeline:
    """
    Wrapper to load pickled pipeline from memory

    Args:
        model_path (str): absolute path of the pickle

    Returns:
        Pipeline: previously saved scikit-learn pipeline object
    """
    with open(model_path, "rb") as file:
        pipeline = pickle.load(file)
    return pipeline

def classify_sentences(pipeline: Pipeline, sentences: np.array) -> np.array:
    """
    The most important function for Production :  this function takes as input
        the pipeline (stored into memory) and a list of sentences (strings),
        and return all the corresponding id_labels

    Args:
        pipeline (Pipeline): must contain a `classifier`, and may also contain a `binarizer`
        sentences (np.array[str]): the array of sentences to make predictions on

    Returns:
        np.array: array of labels predictions, of the same length
    """
    embeddings = get_embeddings_sentences(sentences)
    if "binarizer" in pipeline:
        y = pipeline["classifier"].predict(embeddings)
        id_labels = pipeline["binarizer"].inverse_transform(y)
        return id_labels
    elif "classifier_technical" in pipeline and "classifier_transverse" in pipeline:
        return np.concatenate(
            (
                pipeline["classifier_technical"].predict(embeddings),
                pipeline["classifier_transverse"].predict(embeddings),
            ),
            axis=1,
        )
    else:
        return pipeline["classifier"].predict(embeddings)


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
    embeddings = embedder.encode(sentences)
    return embeddings


def prepare_sentencizer_training():
    """
    This variant of sentencizer also cuts long sentences in shorter strings (e.g: ";" is considered as a separator)
    As a consequence, when only a few words are labelled by an inspector, the label can be expanded merely to the relevant part of the sentence
    """
    punct_chars = [
        "!",
        ".",
        "?",
        "։",
        "؟",
        "۔",
        "܀",
        "܁",
        "܂",
        "߹",
        "।",
        "॥",
        "၊",
        "။",
        "።",
        "፧",
        "፨",
        "᙮",
        "᜵",
        "᜶",
        "᠃",
        "᠉",
        "᥄",
        "᥅",
        "᪨",
        "᪩",
        "᪪",
        "᪫",
        "᭚",
        "᭛",
        "᭞",
        "᭟",
        "᰻",
        "᰼",
        "᱾",
        "᱿",
        "‼",
        "‽",
        "⁇",
        "⁈",
        "⁉",
        "⸮",
        "⸼",
        "꓿",
        "꘎",
        "꘏",
        "꛳",
        "꛷",
        "꡶",
        "꡷",
        "꣎",
        "꣏",
        "꤯",
        "꧈",
        "꧉",
        "꩝",
        "꩞",
        "꩟",
        "꫰",
        "꫱",
        "꯫",
        "﹒",
        "﹖",
        "﹗",
        "！",
        "．",
        "？",
        "𐩖",
        "𐩗",
        "𑁇",
        "𑁈",
        "𑂾",
        "𑂿",
        "𑃀",
        "𑃁",
        "𑅁",
        "𑅂",
        "𑅃",
        "𑇅",
        "𑇆",
        "𑇍",
        "𑇞",
        "𑇟",
        "𑈸",
        "𑈹",
        "𑈻",
        "𑈼",
        "𑊩",
        "𑑋",
        "𑑌",
        "𑗂",
        "𑗃",
        "𑗉",
        "𑗊",
        "𑗋",
        "𑗌",
        "𑗍",
        "𑗎",
        "𑗏",
        "𑗐",
        "𑗑",
        "𑗒",
        "𑗓",
        "𑗔",
        "𑗕",
        "𑗖",
        "𑗗",
        "𑙁",
        "𑙂",
        "𑜼",
        "𑜽",
        "𑜾",
        "𑩂",
        "𑩃",
        "𑪛",
        "𑪜",
        "𑱁",
        "𑱂",
        "𖩮",
        "𖩯",
        "𖫵",
        "𖬷",
        "𖬸",
        "𖭄",
        "𛲟",
        "𝪈",
        "｡",
        "。",
        "\n\n",
        ";",
    ]
    config = {"punct_chars": punct_chars}
    nlp = French()
    nlp.add_pipe("sentencizer", config=config)
    return nlp
