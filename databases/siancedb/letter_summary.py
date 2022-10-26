from siancedb.models import SiancedbLetter, SiancedbLabel, SessionWrapper

from typing import List, Optional, Tuple, Sequence, Union
from pydantic import BaseModel

import re


import itertools

PREDICTION_MODE = "predictions"
TRAINING_MODE = "training"


class BlockSemantics(BaseModel):
    id_semantics: int
    kind: str
    value: Union[str, int]
    confidence: Optional[float]


class LetterBlock(BaseModel):
    start: int
    end: int
    semantics: List[BlockSemantics]


class TreeLeaf(BaseModel):
    leaf: str


class TreeNode(BaseModel):
    children: List[Union["TreeNode", TreeLeaf]]
    value: LetterBlock


TreeNode.update_forward_refs()

AnnotatedText = TreeNode

label_sep_char = " : "

with SessionWrapper() as db:
    LabelTranslate = {
        label.id_label: label.category.upper() + label_sep_char + label.subcategory
        for label in db.query(SiancedbLabel).all()
    }


def hydrate_letter(letter: SiancedbLetter, mode: str, id_model: int):
    """
    Transforms a flat letter into a enriched tree
    using the mode {mode} which can be either "predictions" or
    "training"
    We use the {id_model} version of the predictions to compute
    predictions...
    """

    #
    # Sections and demands are guaranteed
    # to be disjoint so we only sort them by
    # starting positions. For predictions/annotations
    # we are guaranteed that they are either
    # _completely overlapping_ or _completely disjoint_
    # so we just need to merge based on
    # the starting position.
    #

    sections = sorted(
        [
            LetterBlock(
                start=section.start,
                end=section.end,
                semantics=[
                    BlockSemantics(
                        id_semantics=section.id_section,
                        kind="sections",
                        value=f"{section.priority}",
                    )
                ],
            )
            for section in letter.sections
        ],
        key=lambda x: x.start,
    )

    demands = sorted(
        [
            LetterBlock(
                start=demand.start,
                end=demand.end,
                semantics=[
                    BlockSemantics(
                        id_semantics=demand.id_demand,
                        kind="demands",
                        value=demand.priority,
                    )
                ],
            )
            for index, demand in enumerate(letter.demands)
        ],
        key=lambda x: x.start,
    )

    last_demand_a = len(
        [demand for demand in demands if demand.semantics[0].value == "1"]
    )

    for num_demand, demand in enumerate(demands):
        if demand.semantics[0].value == "1":
            demand.semantics[0].value = f"{1  + num_demand}"
        elif demand.semantics[0].value == "2":
            demand.semantics[0].value = f"{1 + num_demand - last_demand_a}"

    sentences = sorted(
        [
            LetterBlock(
                start=sentence.start,
                end=sentence.end,
                semantics=[
                    BlockSemantics(
                        id_semantics=sentence.id_prediction
                        if mode == PREDICTION_MODE
                        else sentence.id_annotation,
                        kind=mode,
                        value=LabelTranslate[sentence.id_label],
                        confidence=sentence.decision_score,
                    )
                ],
            )
            for sentence in (
                letter.predictions if mode == PREDICTION_MODE else letter.training
            )
            # take all predictions in training mode and only the ones of the expected model in prediction mode
            if mode == TRAINING_MODE or sentence.id_model == id_model
        ],
        key=lambda x: x.start,
    )

    # we now group sentences by starting positions
    def repr_group(group):
        group = list(group)
        return LetterBlock(
            start=group[0].start,
            end=group[0].end,
            semantics=[
                prediction
                for predicted_sentence in group
                for prediction in predicted_sentence.semantics
            ],
        )

    sentences = [
        repr_group(g) for _, g in itertools.groupby(sentences, key=lambda x: x.start)
    ]

    return recursive_split(letter.text, sections, demands, sentences)


def recursive_split(
    text: str, *annotation_levels: List[List[LetterBlock]]
) -> List[AnnotatedText]:
    """
    Split the text using the annotations in the list,
    each annotation levels splits the text further into a tree.
    """
    if len(annotation_levels) == 0:
        return [TreeLeaf(leaf=text)]
    else:
        if (
            len(annotation_levels[0]) == 0
        ):  # base case. When we are at the thinest level of imbrications
            blocks = [LetterBlock(start=0, end=len(text), semantics=[])]
        else:
            annotations = annotation_levels[
                0
            ]  # 'myse en abime'. getting inside a thiner level of imbrication
            blocks = [LetterBlock(start=0, end=annotations[0].start, semantics=[])]
            blocks.extend(
                [
                    u
                    for a1, a2 in zip(annotations[:-1], annotations[1:])
                    for u in [
                        a1,
                        LetterBlock(start=a1.end, end=a2.start, semantics=[]),
                    ]
                ]
            )
            blocks.append(annotations[-1])
            blocks.append(
                LetterBlock(start=annotations[-1].end, end=len(text), semantics=[])
            )
            # at this point the 'blocks' consists of starting and ending positions. Then it is enriched with 'semantics' parameter
            blocks = list(filter(lambda x: x.end != x.start, blocks))
        # at this point, we assume that the start and stop of an inner block are included in its parent
        # in particular, this should be true with the cut in sections/demands (entirely included in a section)/sentences
        return [
            TreeNode(
                children=recursive_split(
                    text[block.start : block.end],
                    *[
                        [
                            LetterBlock(
                                semantics=u.semantics,
                                start=u.start - block.start,
                                end=u.end - block.start,
                            )
                            for u in l
                            if u.start >= block.start and u.end <= block.end
                        ]
                        for l in annotation_levels[1:]
                    ],
                ),
                value=block,
            )
            for block in blocks
        ]
