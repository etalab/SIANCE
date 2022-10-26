"""
The function `evaluate_multi_output_classifier` accepts non-constant number of predictions per sentence.
Example of use:

>>> y_pred = [[0, 2, 3], [1, 2], [0, 2]]
>>> y_test = [[0], [1], [0]]
>>> evaluate_multi_output_classifier(y_test, y_pred)

"""

from collections.abc import Iterable
from sklearn.metrics import recall_score, precision_score


def evaluate_mono_output(y_true, y_pred):
    """
    The precision and the recall of the model.
    With the parameter `weighted`, sklearn functions compute metrics for each label,
    and find their average weighted by support (the number of true instances for each label).
    The `weighted` mod alters `macro` to account for label imbalance;
    it can result in an F-score that is not between precision and recall.


    Args:
        y_test (list[list[x]]): list of list of labels (the length equals to the number of samples to classify)
        y_pred (list[list[x]]): list of list of labels (the length equals to the number of samples to classify)

    Returns:
        float: precision score
        float: recall score
    """
    return precision_score(y_true, y_pred, average="weighted"), recall_score(
        y_true, y_pred, average="weighted"
    )


def evaluate_every_class(y_test, y_pred):
    """
    Args:
        y_test (list[list[x]]): list of list of labels (the length equals to the number of samples to classify)
        y_pred (list[list[x]]): list of list of labels (the length equals to the number of samples to classify)
    """
    true_positive_dict, false_positive_dict, false_negative_dict = {}, {}, {}
    # loop on the external loop
    for k, label_real_list in enumerate(y_test):
        label_pred_list = y_pred[k]
        # the casting below makes the function compatible with both mono-output and multi-output classifiers
        if not isinstance(label_pred_list, Iterable):
            label_pred_list = [label_pred_list]
        if not isinstance(label_real_list, Iterable):
            label_real_list = [label_real_list]
        for label_real in label_real_list:
            # if the real label was predicted, add it to the true positive dict. Otherwise it is a false negative
            if label_real in label_pred_list:
                true_positive_dict[label_real] = (
                    true_positive_dict.get(label_real, 0) + 1
                )
            else:
                false_negative_dict[label_real] = (
                    false_negative_dict.get(label_real, 0) + 1
                )
        for label_pred in label_pred_list:
            # the true positive case has already been treated. Check if is a false positive
            if label_pred not in label_real_list:
                false_positive_dict[label_pred] = (
                    false_positive_dict.get(label_pred, 0) + 1
                )

    recall_dict, precision_dict = {}, {}
    for label in true_positive_dict:
        recall_dict[label] = true_positive_dict[label] / (
            true_positive_dict[label] + false_negative_dict.get(label, 0)
        )
        precision_dict[label] = true_positive_dict[label] / (
            true_positive_dict[label] + false_positive_dict.get(label, 0)
        )

    true_positive = sum([true_positive_dict[label] for label in true_positive_dict])
    false_positive = sum([false_positive_dict[label] for label in false_positive_dict])
    false_negative = sum([false_negative_dict[label] for label in false_negative_dict])

    recall = true_positive / (true_positive + false_negative)
    precision = true_positive / (true_positive + false_positive)

    return precision_dict, recall_dict, precision, recall


def evaluate_multi_output_classifier(y_test, y_pred):
    """
    Function computing metrics about false positive and true positive for multioutput classification.
    These scores does not match stricto sensu the mathematical definitions of precision and recall.
    Here, our scores equals to the average of precision per class (resp. recall per class),
    weighted with the number of samples for every class.

    See below the explanation (in French) formatted in Latex

    Formulas (in LateX format) :

    Let $\mathbb{L}$ be the set of labels
    and let $\mathbb{S}$ be the set of sentences.
    The function $p : \mathbb{S} \to \mathcal{P}(\mathbb{L})$
    if the function learnt by the model.
    The function $f : \mathbb{S} \to \mathcal{P}(\mathbb{L})$
    is the real function we want to retrieve.

    \begin{equation}
        \textrm{TP}
        =
        \sum_{s \in \mathbb{S}}
        \sum_{l \in \mathbb{L}}
        \mathbb{1}(l \in p(s))
    \end{equation}

    \begin{equation}
        \textrm{FP}
        =
        \sum_{s \in \mathbb{S}}
        \sum_{l \in \mathbb{L}}
        \mathbb{1}(l \not \in p(s))
    \end{equation}

    \begin{equation}
        \textrm{FN}
        =
        \sum_{s \in \mathbb{S}}
        \sum_{l \in \mathbb{L}}
        \mathbb{1}(l \not \in p(s) \wedge l \in f(s))
    \end{equation}


    Args:
        y_test (list[list[x]]): list of list of labels (the length equals to the number of samples to classify)
        y_pred (list[list[x]]): list of list of labels (the length equals to the number of samples to classify)

    Returns:
        float: kind of precision score for multiclass multioutput
        float: kind of recall score for multiclass multioutput
    """
    # true_positive = sum_sentences sum_GroundLabel  bool(label)
    true_positive, false_positive, false_negative = 0, 0, 0
    # loop on the external loop
    for k, label_real_list in enumerate(y_test):
        label_pred_list = y_pred[k]
        true_positive += sum(
            [(label_real in label_pred_list) for label_real in label_real_list]
        )
        false_negative += sum(
            [(label_real not in label_pred_list) for label_real in label_real_list]
        )
        false_positive += sum(
            [(label_pred not in label_real_list) for label_pred in label_pred_list]
        )
    recall = true_positive / (true_positive + false_negative)
    precision = true_positive / (true_positive + false_positive)
    return precision, recall
