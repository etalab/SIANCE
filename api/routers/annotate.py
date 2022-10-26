from typing import List

from fastapi import APIRouter, Depends
import json

from siancedb.pandas_writer import import_objects_in_pandas

from siancedb.models import SessionWrapper, SiancedbLetter, SiancedbLabel, SiancedbModel, SiancedbPrediction, SiancedbTraining, write_training
from  sqlalchemy.sql.expression import func
from siancedb.config import get_config
from .auth import get_current_user

from ..schemes import Annotation, AnnotationsGet, AnnotationsPost, User
import numpy as np
from pydantic import parse_obj_as

import logging
logger = logging.getLogger("siance-api-log")

ES = get_config()["elasticsearch"]


annotate_router = APIRouter(
    prefix="/annotate",
    tags=["annotate"],
    dependencies=[Depends(get_current_user)],
)


@annotate_router.post("/annotation", response_model=AnnotationsPost)
def post_annotation(query: AnnotationsPost, user: User = Depends(get_current_user)):
    annotations = [parse_obj_as(Annotation, annotation) for annotation in query.annotations]
    training_examples = [
        SiancedbTraining(
            name=annotation.letter_name,
            start=annotation.start,
            end=annotation.end,
            sentence=annotation.sentence,
            id_label=annotation.id_label
        ) for annotation in annotations 
    ]
    write_training(training_examples)
    return query
    



@annotate_router.post("/samples", response_model=List[Annotation])
def sample_predictions(query: AnnotationsGet) -> List[Annotation]:
    category = query.category
    with SessionWrapper() as db:
        exploit_preds = list(
            db.query(SiancedbPrediction, SiancedbLabel, SiancedbLetter)\
            .filter(SiancedbPrediction.id_label == SiancedbLabel.id_label)\
            .filter(SiancedbPrediction.id_letter == SiancedbLetter.id_letter)\
            .filter(SiancedbLabel.category == category)\
            .order_by(func.random())\
            .limit(15).all()
        )
        explo_preds = list(
            db.query(SiancedbPrediction, SiancedbLabel, SiancedbLetter)\
            .filter(SiancedbPrediction.id_label == SiancedbLabel.id_label)\
            .filter(SiancedbPrediction.id_letter == SiancedbLetter.id_letter)\
            .filter(SiancedbLabel.category != category)\
            .order_by(func.random())\
            .limit(5).all()
        )
            
        annotations = [
            Annotation(
                start=pred.start,
                end=pred.end,
                id_label=pred.id_label,
                id_letter=pred.id_letter,
                sentence=pred.sentence,
                category=label.category,
                subcategory=label.subcategory,
                letter_name=letter.name,
                exploration=False
            ) for pred, label, letter in exploit_preds
        ] + [
            Annotation(
                start=pred.start,
                end=pred.end,
                id_label=pred.id_label,
                id_letter=pred.id_letter,
                sentence=pred.sentence,
                category=label.category,
                subcategory=label.subcategory,
                letter_name=letter.name,
                exploration=True
            ) for pred, label, letter in explo_preds
        ]
        return annotations
