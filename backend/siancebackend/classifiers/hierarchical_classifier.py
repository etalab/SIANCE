import numpy as np
from scipy.sparse import csr_matrix
from typing import Dict, Tuple, List, Iterable
from sklearn.base import BaseEstimator, clone
from sklearn.preprocessing import LabelBinarizer
from sklearn_hierarchical_classification.classifier import HierarchicalClassifier
from sklearn_hierarchical_classification.constants import ROOT


class HierarchicalCategoryClassifier(HierarchicalClassifier):
    """
    Class embedding a sklearn-based tool for hierarchical classification.
    In practice, we now use a custom hierarchical model class to control thiner how it is done

    """

    def __init__(self, base_estimator: BaseEstimator, inverted_class_hierarchy: Dict):
        """

        Args:
            base_estimator (BaseEstimator): sklearn base estimator
            inverted_class_hierarchy (dict): keys are classes, and values are the groups of classes they belong to
        """
        class_hierarchy = {}
        for bottom, top in inverted_class_hierarchy.items():
            try:
                class_hierarchy[ROOT].append(top)
            except KeyError:
                class_hierarchy[ROOT] = [top]
            try:
                class_hierarchy[top].append(bottom)
            except KeyError:
                class_hierarchy[top] = [bottom]

        self.class_hierarchy = class_hierarchy

        self.classifier = HierarchicalClassifier(
            base_estimator=base_estimator,
            class_hierarchy=class_hierarchy,
        )

    def fit(self, x, y):
        self.classifier = self.classifier.fit(x, y)
        return self

    def predict(self, x):
        return self.classifier.predict(x)


class CustomHierarchicalCategoryClassifier(BaseEstimator):
    """
    A custom class for 2 level hierarchical classification.
    We first classify the sentences in "categories" of topics (str) and then classify the sentences in "id_labels" (int)

    """

    def __init__(
        self,
        base_top_estimator: BaseEstimator,
        base_bottom_estimator: BaseEstimator,
        inverted_class_hierarchy: Dict,
        top_n: int = 1,
    ):
        """
        Initialize instance of hierarchical classifier

        Args:
            inverted_class_hierarchy (dict): keys are classes, and values are the groups of classes they belong to
            top_n (int, optional): for each sentence, the finally predicted `id_labels` is chosen among to top_n
                most probable `categories` predicted by the top level of the model. When equals to 1, it is a basic
                classification. When > 1, there is a "safetynet" mechanism.
                Defaults to 1.
        """
        class_hierarchy = {}
        for bottom, top in inverted_class_hierarchy.items():
            if top not in class_hierarchy:
                class_hierarchy[top] = [bottom]
            else:
                class_hierarchy[top].append(bottom)

        self.class_hierarchy = class_hierarchy
        self.inverted_class_hierarchy = inverted_class_hierarchy
        self.encoder = LabelBinarizer(sparse_output=True)
        self.top_n = top_n
        self.top_classifier = base_top_estimator
        self.bottom_classifiers = {
            top: clone(base_bottom_estimator, safe=True) for top in class_hierarchy
        }

    def fit(self, x: np.array, y: np.array):
        # shape of `x`: (samples, size(embeddings). shape of `y`: (samples, 1)
        y_flat = np.ravel(y)
        y_top = np.reshape(
            [self.inverted_class_hierarchy[label] for label in y_flat], (-1, 1)
        )  # shape of `y_top`: (samples, 1)
        y_encoded = self.encoder.fit_transform(
            y_top
        )  # shape of `y_top`: (samples, size(encodings))
        self.top_classifier = self.top_classifier.fit(x, y_encoded)
        # fit all classifiers of subcategories
        for top_level_class in self.class_hierarchy:
            mask = [
                True if label in self.class_hierarchy[top_level_class] else False
                for label in y_flat
            ]
            if len(y[mask]) > 0:
                self.bottom_classifiers[top_level_class] = self.bottom_classifiers[
                    top_level_class
                ].fit(x[mask], y[mask])
            else:
                print(
                    f"There is no example for the category: {top_level_class}."
                    f" No specific classifier can be trained for it"
                )
        return self

    def predict(self, x: np.array) -> Iterable[int]:
        return predict_with_safetynet(
            x, self.top_classifier, self.bottom_classifiers, self.encoder, self.top_n
        )


def predict_top_level(
    x: np.array, classifier: BaseEstimator, encoder: LabelBinarizer, top_n: int = 1
) -> Tuple[np.array, np.array]:
    """
    For each sample, compute classification scores and indicates the names (strings) of the `top_n` best candidates

    Args:
        x (np.array): the vectors to classify
        classifier (BaseEstimator): a classifier trained on encoded labels
        encoder (LabelBinarizer): a encoder trained to encode the initial labels in vectors (target of the classifier)
        top_n (int, optional): the number of top classes returned for each sentence. Defaults to 1.
    Returns:
        np.array (2 dimensions): for each sample, indicates the names (strings) of the top_n classes,
                np.array (2 dimensions): for each sample, give the probability associated  to the class

    """
    # `classes_` attribute gives the order of the classes in the output of `predict_proba` method
    probabilities = classifier.predict_proba(x)
    best_probabilities = np.sort(-probabilities, axis=-1)[:, :top_n]
    ids_ranking = np.argsort(-probabilities, axis=-1)[:, :top_n]
    # `ids_ranking` gives us indices of most probable classes. It must be turned into actual classes
    classes_order = (
        classifier.classes_
    )  # sklearn attribute: order of class labels match the order in predict_proba
    size_encodings = len(encoder.classes_)
    classes_ranking = np.array(
        [
            [
                classes_order[id_] for id_ in top_ids_one_sample
            ]  # shape `classes_order`: (categories, size(encodings))
            for top_ids_one_sample in ids_ranking
        ]
    )  # shape of `classes_ranking`: (samples, top_n))
    # warning: dtype=object enables to have regular strings, while dtype=str only keeps the first character!
    categories_ranking = np.zeros(shape=classes_ranking.shape, dtype=object)
    # Turn these actual classes into (categorical) class names understandable for the user
    for k in range(ids_ranking.shape[1]):
        # csr_matrix inputs: ((data, (row, col)), shape=(samples, size(encodings))
        encoding_matrix = csr_matrix(
            (
                np.ones(ids_ranking.shape[0], dtype=int),
                (range(ids_ranking.shape[0]), classes_ranking[:, k]),
            ),
            shape=(ids_ranking.shape[0], size_encodings),
        )
        categories_ranking[:, k] = encoder.inverse_transform(
            encoding_matrix
        ).ravel()  # shape `categories_ranking`: (samples, top_n)
    # size of both output arrays: (number of samples, top_n)
    return categories_ranking, best_probabilities


def predict_with_safetynet(
    x: np.array,
    top_classifier: BaseEstimator,
    bottom_classifiers: Dict[object, BaseEstimator],
    encoder: LabelBinarizer,
    top_n: int = 3,
) -> np.array:
    """ "
    Hierarchically classify sentences in bottom level classes, using a "safety net" mechanism :
       the bottom level class is searched among the subclasses of the `top_n` most probable top level classes

    Args:
        x (np.array): the embeddings of the sentence to classify in categories
        top_classifier (BaseEstimator): a classifier trained for the top level classification task
        bottom_classifiers (Dict[top level class, BaseEstimator]):
            dictionary of classifiers trained for the bottom level classification task
        encoder (LabelBinarizer): an encoder for top level labels
        top_n (int, optional): for each sentence, the predicted `id_labels` belongs too the top_n most probable category
            predicted by the top level of the model. Defaults to 1.
    """
    top_level_ranking, top_level_probabilities = predict_top_level(
        x, classifier=top_classifier, encoder=encoder, top_n=top_n
    )
    y_pred = np.empty((len(x), 1), dtype=int)
    if top_n == 1:
        # for `conventional` predictions
        for top in bottom_classifiers.keys():
            mask = (top_level_ranking == top).ravel()
            if len(x[mask]) > 0:
                try:
                    y_pred[mask] = np.reshape(
                        bottom_classifiers[top].predict(x[mask]),
                        (-1, 1),
                    )
                except KeyError:
                    print(
                        f"Even though the model is supposed to be hierarchical, "
                        f"no classifier has ever been trained on the category {top}"
                    )
                    y_pred[mask] = -1
    else:
        # for `weighted` predictions with safety net
        best_probabilities = np.zeros((len(x), top_n), dtype=float)
        best_candidates = np.zeros((len(x), top_n), dtype=int)
        # for every `top_n` most probable top level classes, give the most probable corresponding bottom level classes
        # and the associated probability
        
        def score(bottom_score: float, top_score: float):
            return bottom_score * top_score
        
        def score_probas(bottom_scores: np.array, top_probas: np.array):
            # a = number of samples where 'top' class in a good candidate
            # b = number of possible bottom classes for this 'top' class
            a, b = bottom_scores.shape
            a, = top_probas.shape
            combined_scores = np.empty_like(bottom_scores, dtype=float)
            for j in range(b):
                combined_scores[:, j] = bottom_scores[:, j] * top_probas
            return combined_scores

            
        
        
        for k in range(top_n):
            for top in bottom_classifiers.keys():
                mask = (top_level_ranking[:, k] == top).ravel() # the considered top classifier is ranked k-th
                if len(x[mask]) > 0:
                    bottom_probas = bottom_classifiers[top].predict_proba(x[mask]) # size: (len(x[mask]), nb of bottom classes for this top class)
                    combined_probas = score_probas(
                        bottom_probas,
                        top_level_probabilities[:, k][mask]
                    )
                        
                    """
                    # `best_probabilities` gives the score of bottom level classification only
                    
                    best_probabilities[mask, k] = np.max(
                        all_probas, axis=-1
                    )
                    """
                    # `best_probabilities` combines scores of bottom and top level classifications
                    best_probabilities[mask, k] = np.max(combined_probas, axis=-1)
                    best_candidates[mask, k] = np.argmax(combined_probas, axis=-1)
        # for every sample, indices gives the index of the best top level class among the top_n top level classes
        # there are 2 solutions: either only considering the score of bottom level classification

        indices = np.argmax(
            best_probabilities, axis=-1
        )  # shape of `indices` : (samples)
        # TODO: put again the multiplication in score
        y_pred = np.reshape(
            [best_candidates[sample, indices[sample]] for sample in range(len(x))],
            (-1, 1),
        )
    return y_pred
