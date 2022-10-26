import os
import pickle
import time
import pandas as pd
import numpy as np
from datetime import date

from siancebackend.classifiers.embeddings import get_embeddings_sentences
from siancebackend.classifiers.architectures import prepare_classifier

from siancebackend.classifiers.evaluate_classifier import (
    evaluate_mono_output,
    evaluate_every_class,
    evaluate_multi_output_classifier,
)
from siancebackend.letter_management.sentencizer import prepare_sentencizer
from siancebackend.pipe_logger import update_log_state

from siancedb.config import get_config
from siancedb.models import (
    Session,
    SessionWrapper,
    SiancedbLetter,
    SiancedbLabel,
    SiancedbSection,
    SiancedbTraining,
    SiancedbModel,
    SiancedbPrediction,
    SiancedbPipeline,
)
from siancedb.pandas_writer import write_from_pandas, import_objects_in_pandas, chunker

from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import (
    MultiLabelBinarizer,
)

# for typing
import spacy
from typing import Dict, Iterable, Tuple

# logger
import logging

logger = logging.getLogger("classify-topics")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("logs/classify_topics.log")
logger.addHandler(fh)

# the minimal length of a sentence to be predicted (arbitrary hyperparameter)
MIN_LENGTH_FOR_PREDICTION = 64


def prepare_score_dict(siance_model: SiancedbModel) -> Dict[int, float]:
    """
    Return a dictionary where keys are id_labels and values are model training set(!) scores on these id_labels
    """
    score_dict = dict()
    id_labels = siance_model.id_labels
    score_labels = siance_model.score_labels
    if score_labels is not None:
        for k, id_label in enumerate(id_labels):
            score_dict[id_label] = score_labels[k]
    return score_dict


def train_save_pipeline_from_embeddings(
    model_path: str,
    architecture: str,
    embeddings: np.array,
    id_labels: np.array,
    labels_hierarchy: Dict = None,
    labels_transverse: Dict = None,
    top_n: int = 1,
) -> Pipeline:
    """

    Args:
        model_path (str): absolute path of the NLP model pickle
        architecture (str): possible values among [basic, grid-search, hierarchical, multi-output, custom-hierarchical]
        embeddings (numpy.array): the array of embeddings to make predictions on
        id_labels (numpy.array): the array of labels (one or more per sample, if the model is mono- or multi-output)
        labels_hierarchy (dict, Optional): the association of top level (dict values) and bottom level classes (keys)
        labels_transverse (dict, Optional): keys are (bottom) classes and values boolean telling if it is "transverse"
        top_n (int, Optional):
    Returns:
        Pipeline: contain a `classifier`, and may also contain a `binarizer`
    """
    # if the parent directory of the model path does not exist, create it
    dir_name = os.path.dirname(model_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    time_learning = time.time()

    if architecture == "dual":
        technical_labels = {
            k: v if not labels_transverse[k] else None
            for k, v in labels_hierarchy.items()
        }
        transverse_labels = {
            k: v if labels_transverse[k] else None for k, v in labels_hierarchy.items()
        }
        technical_classifier = prepare_classifier(
            architecture="dual", labels_hierarchy=technical_labels, top_n=top_n
        )
        transverse_classifier = prepare_classifier(
            architecture="dual", labels_hierarchy=transverse_labels, top_n=top_n
        )
        pipeline = Pipeline(
            steps=[
                ("classifier_technical", technical_classifier),
                ("classifier_transverse", transverse_classifier),
            ]
        )
        mask_technical = id_labels == technical_labels.keys()
        mask_transverse = id_labels == technical_labels.keys()
        pipeline["classifier_technical"].fit(
            embeddings[mask_technical], id_labels[mask_technical]
        )
        pipeline["classifier_transverse"].fit(
            embeddings[mask_transverse], id_labels[mask_transverse]
        )

    elif architecture == "multi-output":
        classifier = prepare_classifier(
            architecture="multi-output",
        )
        pipeline = Pipeline(
            steps=[
                ("binarizer", MultiLabelBinarizer(sparse_output=True)),
                ("classifier", classifier),
            ]
        )

        y = pipeline["binarizer"].fit_transform(id_labels)
        pipeline["classifier"].fit(embeddings, y)
    else:
        classifier = prepare_classifier(
            architecture=architecture, labels_hierarchy=labels_hierarchy, top_n=top_n
        )
        pipeline = Pipeline(
            steps=[
                ("classifier", classifier),
            ]
        )
        pipeline["classifier"].fit(embeddings, id_labels)

    logger.info(
        "Time to train the required classification model(s): {0:.2f}".format(
            time.time() - time_learning
        )
    )

    with open(model_path, "wb") as file:
        pickle.dump(pipeline, file)
    return pipeline


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


def classify_embeddings(pipeline: Pipeline, embeddings: np.array) -> np.array:
    """
    Almost the same function as `classify_sentences`. To be used for quick tests (and not for PROD)
    Accept directly pre-computed embeddings instead of sentences

    Args:
        pipeline (Pipeline): must contain a `classifier`, and may also contain a `binarizer`
        embeddings (np.array): the array of pre-computed embeddings corresponding to sentences

    Returns:
        numpy.array: array of labels predictions, of the same length
    """
    y = pipeline["classifier"].predict(embeddings)
    if "binarizer" in pipeline:
        id_labels = pipeline["binarizer"].inverse_transform(y)
        return id_labels
    else:
        return y


def classify_topics_one_letter(
    letter: SiancedbLetter,
    sections: Iterable[SiancedbSection],
    pipeline: Pipeline,
    id_model: int,
    score_dict: Dict,
    sentencizer: spacy.language.Language,
) -> Iterable[SiancedbPrediction]:
    starts, ends = [], []
    for section in sections:
        starts.append(section.start)
        ends.append(section.end)
    if len(starts) > 0 and len(ends) > 0:
        start_first_section, end_last_section = int(np.min(starts)), int(np.max(ends))
        text = letter.text[start_first_section:end_last_section]
    else:
        start_first_section = 0
        text = letter.text

    sentences, sent_starts, sent_ends = [], [], []
    for sent in sentencizer(text).sents:
        sentences.append(sent.text)
        sent_starts.append(sent.start_char + start_first_section)
        sent_ends.append(sent.end_char + start_first_section)

    sentences = np.array(sentences)
    # create a mask for the sentences to predict
    # mask = np.ones(len(sentences), dtype=bool)
    mask = np.array(
        [
            ((sent_ends[k] - start) >= MIN_LENGTH_FOR_PREDICTION)
            for k, start in enumerate(sent_starts)
        ]
    )
    # `predicted_labels` is a list of list of labels (one cell per sentence and per predicted label)
    try:
        predicted_labels = classify_sentences(pipeline, sentences[mask])
    except Exception as e:
        logger.debug(
            f"An exception occurred while predicting classes on the letter {letter.id_letter} : {e}"
        )
        predicted_labels = [[]] * np.sum(mask)

    db_predictions = []
    sentences_idx = 0
    prediction_idx = 0
    while sentences_idx < len(sentences):
        if not mask[sentences_idx]:  # if the sentence was not supposed to be predicted
            sentences_idx += 1
            break
        else:
            id_labels_one_sentence = predicted_labels[prediction_idx]
            sentences_idx += 1
            prediction_idx += 1
            if not isinstance(id_labels_one_sentence, Iterable) or isinstance(id_labels_one_sentence, str):  # for monoinput models, put labels in singletons
                id_labels_one_sentence = [id_labels_one_sentence]
            # check the confidence score of the prediction is not null
            for id_label in id_labels_one_sentence:
                if id_label in score_dict and score_dict[id_label] is not None:
                    score = float(score_dict[id_label])
                else:
                    score = None
                db_predictions.append(
                    SiancedbPrediction(
                        id_letter=int(letter.id_letter),
                        start=int(sent_starts[sentences_idx]),
                        end=int(sent_ends[sentences_idx]),
                        id_label=int(id_label),
                        sentence=str(sentences[sentences_idx]),
                        id_model=int(id_model),
                        decision_score=score,
                    )
                )
    return db_predictions


def classify_topics(pipeline: Pipeline, letters_df: pd.DataFrame) -> pd.DataFrame:
    """
    This function is used for the generation/filling of the predictions database
    It uses the table of letters ("lettres de suites"), cut the texts into sentences,
    and predict labels for each sentence using a trained NLP model

    This function is not optimized to predict heavy volumes of data

    This operation results in a new pandas.DataFrame that is returned

    Args:
        pipeline (Pipeline): must contain a `classifier`, and may also contain a `binarizer`
        letters_df (pd.DataFrame): structured as the table `ape_letters`

    Returns:
        pd.DataFrame: a table with the 6 columns "id_letter", "sentence",
            "id_label", "terms", "start", "end"
    """

    nlp = prepare_sentencizer()
    n = len(letters_df)
    letter_k = 1
    data = []

    with SessionWrapper() as db:
        sections_df = import_objects_in_pandas(SiancedbSection, db)
        sections_df = sections_df[
            sections_df.id_letter.isin(letters_df.id_letter.values)
        ]

    for id_letter, row in letters_df.set_index("id_letter").iterrows():
        logger.info("Predicting letter {}/{} -- id {}".format(letter_k, n, id_letter))
        letter_k += 1

        # find the beginning of the first saved section (generally the synthesis)
        # and the end of the last saved session (generally the observations)
        try:
            bounds = sections_df[(sections_df.id_letter == id_letter)][["start", "end"]]
            start, end = bounds["start"].min(), bounds["end"].max()
            text = row["text"]
            text = text[start:end]
        except TypeError:
            # exception if no section bounds were found for this letter
            start = 0
            text = row["text"]

        doc = nlp(text)  # field name to be changed
        # doc.sents is a generator. The lines below stores information in arrays
        sentences, sent_starts, sent_ends = [], [], []
        for sent in doc.sents:
            sentences.append(sent.text)
            sent_starts.append(sent.start_char + start)
            sent_ends.append(sent.end_char + start)
        # `predicted_labels` is a list of list of labels (one cell per sentence and per predicted label)
        try:
            predicted_labels = classify_sentences(pipeline, sentences)
        except Exception as e:
            logger.debug(
                f"An exception occurred while predicting classes on the letter {id_letter} : {e}"
            )
            predicted_labels = [[]] * len(sentences)

        predictions_count = 0
        for k in range(len(sentences)):
            id_labels_one_sentence = predicted_labels[k]
            sentence = sentences[k]
            start = sent_starts[k]
            end = sent_ends[k]
            if not isinstance(id_labels_one_sentence, Iterable):
                id_labels_one_sentence = [id_labels_one_sentence]
            for id_label in id_labels_one_sentence:
                predictions_count += 1
                data.append(
                    [
                        int(id_letter),
                        sentence,
                        id_label,
                        start,
                        end,
                    ]
                )
        logger.info(
            "Predict {} labels in the letter with id {}".format(
                predictions_count, n, id_letter
            )
        )

    return pd.DataFrame(
        data=data,
        columns=[
            "id_letter",
            "sentence",
            "id_label",
            "start",
            "end"
            #    "date"
        ],
    )  # .drop_duplicates()


def prepare_features_labels(
    multi_output: bool = True,
) -> Tuple[np.array, np.array, Dict, Dict]:
    """
    Return the features and the target to use to train multi-output classifiers

    Args:
        multi_output (bool): boolean specifying if labels should be grouped by the sentences they tag,
        for multi-output classifier training

    Returns:
        numpy.array[float] (2 dimensions), numpy.array[list[int]], dict[int, str] :
            the embeddings of training sentences,
            the array of labels (for each sentence, give the list of corresponding labels),
            a dictionary where a key is `id_label` and value is the name of the category it belongs to
            a dictionary where a key is `id_label` and value is a boolean specifying if the id_label is "transverse"

    """
    with SessionWrapper() as db:
        labels_df = import_objects_in_pandas(SiancedbLabel, db)
    labels_dict = (
        labels_df[["category", "subcategory", "id_label", "is_transverse"]]
        .set_index("id_label")
        .to_dict("index")
    )
    labels_hierarchy = {id_label: v["category"] for id_label, v in labels_dict.items()}
    labels_transverse = {
        id_label: v["is_transverse"] for id_label, v in labels_dict.items()
    }

    # at this point a key is a label id (int), and a value becomes a category name (str)

    basepath = get_config()["learning"]["precomputed"]
    if multi_output:
        features = np.load(os.path.join(basepath, "multi_output_embeddings.npy"))
        multi_id_labels = np.load(
            os.path.join(basepath, "multi_output_labels.npy"), allow_pickle=True
        )
        return features, multi_id_labels, labels_hierarchy, labels_transverse
    else:
        features = np.load(os.path.join(basepath, "mono_output_embeddings.npy"))
        id_labels = np.reshape(
            np.load(os.path.join(basepath, "mono_output_labels.npy")), (-1, 1)
        )
        return features, id_labels, labels_hierarchy, labels_transverse


def build_new_model(
    architecture: str = "multi-output",
    top_n: int = 1,
):
    """
    Args:
        architecture (str): possible values among [basic, grid-search, hierarchical, multi-output, custom-hierarchical]
        top_n (int):
    Create a new instance of SiancedbModel, train it with the features and target from the training set,
    save the pipeline in a pkl file and store the SiancedbModel and its training metrics in database
    """
    x, y, labels_hierarchy, labels_transverse = prepare_features_labels(
        multi_output=architecture == "multi-output"
    )

    date_str = date.today().__str__()
    model_path = os.path.join(
        get_config()["learning"]["topics_models"], "{}_pipeline.pkl".format(date_str)
    )
    name = date_str + "_model"

    pipeline = train_save_pipeline_from_embeddings(
        model_path,
        architecture,
        embeddings=x,
        id_labels=y,
        labels_hierarchy=labels_hierarchy,
        labels_transverse=labels_transverse,
        top_n=top_n,
    )

    # compute predictions on evaluation set. Here we evaluate on the training set itself (the cross-validation has been
    # previously performed in more academical conditions) to store these training metrics for comparison purposes

    y_pred = classify_embeddings(pipeline=pipeline, embeddings=x)
    precision_dict, recall_dict, precision, recall = evaluate_every_class(
        y_test=y, y_pred=y_pred
    )
    logger.info(f"Weighted average scores on evaluation set: {precision} and {recall}")

    unique_labels = list(set(labels_hierarchy.keys()))
    # a label can be missing in the `prediction_dict` if ever it is never predicted in practice. In this case, the score
    # will be None (i.e. undefined)
    score_labels = [precision_dict.get(label, None) for label in unique_labels]

    siance_model = SiancedbModel(
        name=name,
        link=model_path,
        id_labels=unique_labels,
        score_labels=score_labels,
        score=precision,
        is_multi_output=architecture == "multi-output",
        is_active=False,
        user=1,  # test user in database
    )
    with SessionWrapper() as db:
        db.add(siance_model)
        db.commit()


def evaluate_model_with_id_model(id_model: int) -> Tuple[float, float, float]:
    """
    This function is not compulsory anymore, as an evaluation is done on a proper evaluation set during the training
    From the unique `id_model`, retrieve a stored model and evaluate it on the training set
    Here validation set = training set, that may be improved

    Args:
        id_model (int): the unique id used to retrieve a previously saved model

    Returns:
        float, float, float: precision, recall and accuracy of the model calculated on the training set
        (or sort of precision and recall in the case of multi-output model)
    """
    with SessionWrapper() as db:
        training_df = import_objects_in_pandas(SiancedbTraining, db)
        predictions_df = import_objects_in_pandas(SiancedbPrediction, db)
        predictions_df = predictions_df[
            predictions_df.apply(
                lambda row: int(row["id_model"]) == int(id_model), axis=1
            )
        ]
        model = db.query(SiancedbModel).filter(SiancedbModel.id_model == id_model).one()
        model_name = model.name

    # keep only the predicted sentences for which there is a match between annotated training set and testing set
    tmp_df = pd.merge(
        training_df,
        predictions_df,
        on=["id_letter", "start", "end"],
        how="inner",
        suffixes=["_train", "_test"],
    )
    # by construction, the three list `sentences`, `y_true`, `y_pred` are aligned
    tmp_group = tmp_df.groupby(["id_letter", "start", "end"])
    sentences = tmp_group["sentence_train"].first()
    y_true = tmp_group["id_label_train"].apply(list).values
    y_pred = tmp_group["id_label_test"].apply(list).values
    del tmp_df, tmp_group
    # due to join, there are artificial duplicates. Remove them
    y_true = [list(set(labels)) for labels in y_true]
    y_pred = [list(set(labels)) for labels in y_pred]

    # save output of model in excel for analysis
    evaluation_filename = model_name + ".xlsx"
    evaluation_path = os.path.join(
        get_config()["learning"]["evaluations"], evaluation_filename
    )
    pd.DataFrame(
        data={"sentence": sentences, "ground truth": y_true, "predictions": y_pred}
    ).to_excel(evaluation_path, index=False)

    # compute a precision and a recall for every class, and also a general precision and a general recall
    # using metrics from the submodule `evaluate_classifier`
    precisions_dict, recall_dict, precision, recall = evaluate_every_class(
        y_true, y_pred
    )
    accuracy = accuracy_score(y_true, y_pred)

    # below: former function computing a precision and a recall for the model
    # precision, recall = evaluate_multi_output_classifier(y_true, y_pred)
    print(
        f"Evaluation of model (id_model {id_model}) on {len(sentences)} sentences:"
        f" precision={precision}, recall={recall}, accuracy={accuracy}"
        f"Detailed recall scores is: {recall_dict}"
    )
    return precision, recall, accuracy


def build_predictions(db: Session, siance_model: SiancedbModel, pipe_logger=None):
    """
    OLD FUNCTION THAT CAN BE CALLED THROUGH backend/bin BASH SCRIPTS.
    NOT CALLED BY PREFECT PIPELINE (the function called by prefect pipelines is `classify_topics_one_letter`)

    For all letters for which no predictions has been done with the input SianceModel
       (predictions may have been done through other models), cut the letter into sentences, classify them in `id_labels`,
       and save the predictions in PostreSQL

    Args:
        db (Session): a Session to connect to the database
        siance_model (SiancedbModel): an object to identify a model and its output. Its attributes indicates
           the path of the model, the classes met during the training and the model performances on evaluation samples
        pipe_logger (SiancedbPipeline): an object logging in PostgreSQL the advancement of data ingestion steps
    """
    pipeline = load_pipeline(siance_model.link)

    score_dict = {}
    id_labels = siance_model.id_labels
    score_labels = siance_model.score_labels
    if score_labels is not None:
        for k, id_label in enumerate(id_labels):
            score_dict[id_label] = score_labels[k]

    predictions_count = 0

    query = db.query(SiancedbLetter).filter(
        ~SiancedbLetter.predictions_dyn.any(
            SiancedbPrediction.id_model == siance_model.id_model
        )
    )
    letters = query.all()
    n_documents = query.count()

    letters_count = 0
    for chunk in chunker(100, letters):

        chunk_df = pd.DataFrame(
            [(letter.id_letter, letter.text) for letter in chunk],
            columns=["id_letter", "text"],
        )
        letters_count += len(chunk_df)

        logger.debug("Start new chunk of predictions")
        predictions_df = classify_topics(pipeline, chunk_df)
        predictions_df["id_model"] = siance_model.id_model

        # add decision score in the predictions table, on the basis of the score per class saved in the model table
        for id_label in predictions_df.id_label.unique():
            predictions_df.loc[
                predictions_df.id_label == id_label, "decision_score"
            ] = score_dict[id_label]
        write_from_pandas(predictions_df, SiancedbPrediction, db)
        predictions_count += len(predictions_df)
        logger.debug("Committed new chunk of predictions")

        update_log_state(
            pipe=pipe_logger, progress=letters_count / n_documents, step="predictions"
        )

    logger.debug(
        "Finished writing {} entries in {}".format(predictions_count, "ape_predictions")
    )


def build_predictions_with_id_model(
    db: Session, id_model: int, pipe_logger: SiancedbPipeline = None
):
    model = db.query(SiancedbModel).filter(SiancedbModel.id_model == id_model).one()
    build_predictions(db, model, pipe_logger=pipe_logger)


def build_predictions_with_model_name(
    db: Session, model_name: str, pipe_logger: SiancedbPipeline = None
):
    model = db.query(SiancedbModel).filter(SiancedbModel.model_name == model_name).one()
    build_predictions(db, model, pipe_logger=pipe_logger)


def predict_last_letters_with_model(siance_model: SiancedbModel) -> pd.DataFrame:
    id_labels = siance_model.id_labels
    score_labels = siance_model.score_labels

    with SessionWrapper() as db:
        previous_predicted_letters = (
            db.query(SiancedbPrediction.id_letter)
            .distinct(SiancedbPrediction.id_letter)
            .filter(SiancedbPrediction.id_model == siance_model.id_model)
            .all()
        )
        # turn the generator of letters into a list of id_letters
        previous_predicted_letters = [
            letter[0] for letter in previous_predicted_letters
        ]
        letters_df = import_objects_in_pandas(SiancedbLetter, db)
        # select only the letters for which there is no predictions generated with desired model (id_model)
    letters_df = letters_df[
        letters_df.apply(
            lambda row: row.id_letter not in previous_predicted_letters, axis=1
        )
    ]
    logger.debug(f"Begin predicting concepts for {len(letters_df)} new letters")
    pipeline = load_pipeline(siance_model.link)
    predictions_df = classify_topics(pipeline, letters_df)
    predictions_df["id_model"] = siance_model.id_model

    score_dict = {}
    if score_labels is not None:
        for k, id_label in enumerate(id_labels):
            score_dict[id_label] = score_labels[k]

    # add decision score in the predictions table, on the basis of the score per class saved in the model table
    for id_label in predictions_df.id_label.unique():
        predictions_df.loc[
            predictions_df.id_label == id_label, "decision_score"
        ] = score_dict[id_label]

    with SessionWrapper() as db:
        write_from_pandas(predictions_df, SiancedbPrediction, db)
        db.commit()
    logger.debug(
        f"Finished writing {len(predictions_df)} new entries in ape_predictions"
    )
    return predictions_df


def predict_last_letters_with_id_model(id_model: int) -> pd.DataFrame:
    """
    Directly write predictions in database. Also return them for convenience.
    """
    with SessionWrapper() as db:
        model = db.query(SiancedbModel).filter(SiancedbModel.id_model == id_model).one()
    return predict_last_letters_with_model(model)


def predict_last_letters_with_model_name(model_name: str) -> pd.DataFrame:
    """
    Directly write predictions in database. Also return them for convenience.
    """
    with SessionWrapper() as db:
        model = db.query(SiancedbModel).filter(SiancedbModel.name == model_name).one()
    return predict_last_letters_with_model(model)


def classify_topics_default_model() -> pd.DataFrame:
    """
    Directly write predictions in database. Also return them for convenience.
    """
    modelspath = get_config()["learning"]["topics_models"]
    picklepath = get_config()["learning"]["pickles"]
    model_path = os.path.join(modelspath, "2020-12-10_multibert_pipeline.pkl")

    prediction_time = time.time()
    logger.debug("Loaded letters in memory")
    pipeline = load_pipeline(model_path)
    with SessionWrapper() as db:
        letters_df = import_objects_in_pandas(SiancedbLetter, db)

    predictions_df = classify_topics(pipeline, letters_df)

    predictions_df.to_pickle(os.path.join(picklepath, "ape_predictions.pkl"))

    logger.debug(f"Prediction Time: {time.time() - prediction_time}")
    with SessionWrapper() as db:
        write_from_pandas(predictions_df, SiancedbPrediction, db)
        db.commit()
    logger.debug(f"Finished writing {len(predictions_df)} entries in ape_predictions")
    return predictions_df
