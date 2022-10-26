"""
Returned architectures must inherrit from sklearn BaseEstimator
"""

from sklearn.base import BaseEstimator
from sklearn import neural_network
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import GridSearchCV
from siancebackend.classifiers.hierarchical_classifier import (
    HierarchicalCategoryClassifier,
    CustomHierarchicalCategoryClassifier,
)
from typing import Dict


def get_default_architecture() -> neural_network.MLPClassifier:
    return neural_network.MLPClassifier(
        activation="relu",
        learning_rate="adaptive",
        solver="adam",
        max_iter=200,
        hidden_layer_sizes=100,
        alpha=1e-4,
    )


def get_gridsearch_architecture() -> GridSearchCV:
    base_estimator = neural_network.MLPClassifier(
        activation="relu",
        learning_rate="adaptive",
        solver="adam",
        max_iter=200,
    )
    parameters = {
        "hidden_layer_sizes": [
            (
                50,
                20,
            ),
            (100,),
        ],
        "alpha": [1e-5, 1e-4, 1e-3],
    }
    mlp_gridsearch = GridSearchCV(
        estimator=base_estimator, param_grid=parameters, n_jobs=-1, cv=3
    )
    return mlp_gridsearch


def get_hierarchical_architecture(
    labels_dict: Dict[int, Dict[str, str]]
) -> HierarchicalCategoryClassifier:
    assert isinstance(labels_dict, dict), (
        "The dictionary label_dict is necessary for hierarchical classification"
        "It must indicate the hierarchy of classes"
    )

    base_estimator = neural_network.MLPClassifier(
        activation="relu",
        learning_rate="adaptive",
        solver="adam",
        max_iter=200,
    )
    parameters = {
        "hidden_layer_sizes": [
            (
                50,
                20,
            ),
            (100,),
        ],
        "alpha": [1e-5, 1e-4, 1e-3],
    }
    base_estimator = GridSearchCV(
        estimator=base_estimator, param_grid=parameters, n_jobs=-1, cv=3
    )
    return HierarchicalCategoryClassifier(base_estimator, labels_dict)


def get_custom_hierarchical_architecture(
    labels_dict: Dict[int, Dict[str, str]], top_n=2
) -> CustomHierarchicalCategoryClassifier:
    assert isinstance(
        labels_dict, dict
    ), "The parameter label dict is necessary for hierarchical classification"
    base_estimator = neural_network.MLPClassifier(
        activation="relu",
        learning_rate="adaptive",
        solver="adam",
        max_iter=200,
    )
    parameters = {
        "hidden_layer_sizes": [
            (
                50,
                20,
            ),
            (100,),
        ],
        "alpha": [1e-5, 1e-4, 1e-3],
    }
    base_top_estimator = GridSearchCV(
        estimator=base_estimator, param_grid=parameters, n_jobs=-1, cv=3
    )
    base_bottom_estimator = neural_network.MLPClassifier(
        activation="relu",
        learning_rate="adaptive",
        solver="adam",
        max_iter=200,
        hidden_layer_sizes=100,
        alpha=1e-4,
    )

    return CustomHierarchicalCategoryClassifier(
        base_top_estimator, base_bottom_estimator, labels_dict, top_n
    )


def get_multioutput_architecture():
    estimator = neural_network.MLPClassifier(
        activation="relu",
        learning_rate="adaptive",
        solver="adam",
        max_iter=200,
        hidden_layer_sizes=100,
        alpha=1e-4,
    )
    return OneVsRestClassifier(estimator=estimator, n_jobs=-1)


def prepare_classifier(
    architecture: str = "grid-search",
    labels_hierarchy: Dict = None,
    top_n: int = 1,
) -> BaseEstimator:
    """
    Given a specified architecture, initialize an untrained model with already chosen hyper-parameters
    Can work with normal "flat" labels, and also with some "hierarchical" labels

    Args:
        architecture (str, optional): name of architecture (see configs in this module). Defaults to "grid-search".
        labels_hierarchy (Dict, optional): For hierarchical classification.
            The association of top level (dict values) and bottom level classes (dict keys).
        top_n (int, optional): For hierarchical classification.
    Returns:
        BaseEstimator: a model (an instance of a class inheriting from sklearn base estimator)
    """
    assert architecture in [
        "basic",
        "dual",
        "grid-search",
        "hierarchical",
        "multi-output",
        "custom-hierarchical",
    ], "The model architecture you asked for it not implemented. Ask for another"

    if architecture == "basic":
        return get_default_architecture()
    elif architecture == "grid-search":
        return get_gridsearch_architecture()

    elif architecture == "hierarchical":
        assert labels_hierarchy is not None, (
            "If the architecture is set to `hierarchical`, "
            "`labels_dict` cannot be None and must indicate the hierarchy of classes"
        )
        return get_hierarchical_architecture(labels_hierarchy)

    elif architecture == "custom-hierarchical":
        assert labels_hierarchy is not None, (
            "If the architecture is set to `hierarchical`, "
            "`labels_dict` cannot be None and must indicate the hierarchy of classes"
        )
        return get_custom_hierarchical_architecture(labels_hierarchy, top_n)

    elif architecture == "multi-output":
        return get_multioutput_architecture()
