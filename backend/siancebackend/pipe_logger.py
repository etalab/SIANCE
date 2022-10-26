from siancedb.models import SiancedbPipeline, SessionWrapper
from datetime import datetime


def reinitialize_log_state(pipe: SiancedbPipeline):
    with SessionWrapper() as db:
        pipe.last_launched_time = datetime.utcnow()
        pipe.building_letters = 0.0
        pipe.building_trigrams = 0.0
        pipe.building_sections_demands = 0.0
        pipe.building_predictions = 0.0
        pipe.indexing = 0.0
        db.add(pipe)
        db.commit()


def increment_log_state(pipe: SiancedbPipeline):
    with SessionWrapper() as db:
        pipe.last_finished_time = datetime.utcnow()
        pipe.completed_runs = pipe.completed_runs + 1
        db.add(pipe)
        db.commit()


def update_log_state(pipe: SiancedbPipeline, progress: float, step: str):
    # progress cannot be over 1. or below 0.
    progress = min(1.0, progress)
    progress = max(0.0, progress)
    if isinstance(pipe, SiancedbPipeline):
        if step == "letters":
            pipe.building_letters = progress
        elif step == "si_metadata":
            pipe.building_si_metadata = progress
        elif step == "sections_demands":
            pipe.building_sections_demands = progress
        elif step == "trigrams":
            pipe.building_trigrams = progress
        elif step == "predictions":
            pipe.building_predictions = progress
        elif step == "predicted_metadata":
            pipe.building_predicted_metadata = progress
        elif step == "indexing":
            pipe.indexing = progress
        with SessionWrapper() as db:
            db.add(pipe)
            db.commit()
