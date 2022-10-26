from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException

from siancedb.pandas_writer import import_objects_in_pandas

from siancedb.models import (
    SessionWrapper,
    SiancedbLetter,
    SiancedbActionLog,
    SiancedbSIv2LettersMetadata,
    SiancedbTraining,
    SiancedbPrediction,
)
from siancedb.models import get_active_model_id

from siancedb.config import get_config

from .auth import get_current_user

from ..admin_stats import (
    get_user_stats,
    get_letter_consultation_stats,
    get_bean_stats,
)

from ..schemes import (
    User,
    TrainingExample,
    DatabaseStatus,
    MachineLearningStatus,
    SianceGlobalStatistics,
)

ES = get_config()["elasticsearch"]


def check_admin(user: User = Depends(get_current_user)):
    if user.is_admin:
        return True
    else:
        raise HTTPException(
            status_code=403,
            detail="You are required to be administrator",
        )


admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(check_admin)],
)


@admin_router.get("/stats/raw-annotations", response_model=List[TrainingExample])
def admin_stats(
    limit: int, id_label: Optional[int] = None, user: User = Depends(get_current_user)
):
    with SessionWrapper() as db:
        if id_label:
            # pylint: disable=maybe-no-member
            return list(
                db.query(SiancedbTraining)
                .filter(SiancedbTraining.id_label == id_label)
                .limit(limit)
            )
        else:
            return list(
                db.query(SiancedbTraining).limit(limit)  # pylint: disable=no-member
            )


@admin_router.get("/db_status", response_model=DatabaseStatus)
def get_db_status(user: User = Depends(get_current_user)):
    with SessionWrapper() as db:
        # pylint: disable=no-member
        total_letters = db.query(SiancedbLetter).count()
        total_siv2 = db.query(SiancedbSIv2LettersMetadata).count()
        return DatabaseStatus(total_siv2=total_siv2, total_letters=total_letters)


@admin_router.get("/ml_status", response_model=MachineLearningStatus)
def get_ml_status():
    with SessionWrapper() as db:
        # pylint: disable=no-member
        total_letters = db.query(SiancedbLetter).count()
        # unique identifier of training letters is "name" (and not id_letter... which is created later in process) 
        total_annotated_letters = db.query(SiancedbTraining.name).distinct().count()
        total_annotations = db.query(SiancedbTraining).count()
        total_predictions = (
            db.query(SiancedbPrediction)
            .filter(SiancedbPrediction.id_model == get_active_model_id())
            .count()
        )

        return {
            "total_letters": total_letters,
            "total_annotated_letters": total_annotated_letters,
            "total_annotations": total_annotations,
            "total_predictions": total_predictions,
        }


@admin_router.get("/", response_model=SianceGlobalStatistics)
def fetch_stats(user: User = Depends(get_current_user)):
    with SessionWrapper() as db:
        logs = import_objects_in_pandas(SiancedbActionLog, db)

        user_connections = get_user_stats(logs.copy())
        preferred_buttons = get_letter_consultation_stats(logs.copy())
        preferred_filters = get_bean_stats(logs.copy())

        return {
            "weekUsers": user_connections["users_7d"],
            "monthUsers": user_connections["users_30d"],
            "launchUsers": user_connections["users_always"],
            "weeklyTraffic": user_connections["connections_7d"],
            "monthlyTraffic": user_connections["connections_30d"],
            "launchTraffic": user_connections["connections_always"],
            "exportSeries": preferred_buttons,
            "filterSeries": preferred_filters,
        }
