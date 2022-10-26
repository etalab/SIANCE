from typing import Optional


from fastapi import APIRouter, Depends, HTTPException, Query

import elasticsearch as es

from siancedb.letter_summary import hydrate_letter, PREDICTION_MODE
from siancedb.elasticsearch.queries import (
    build_explain_query,
)

from siancedb.elasticsearch.schemes import EQuery

from siancedb.models import (
    SessionWrapper,
    SiancedbLetter,
)
from siancedb.models import get_active_model_id

from siancedb.config import get_config

from .auth import get_current_user

from ..schemes import (
    User,
    Interlocutor,
    MetadataSI,
    ObservableLetter,
    ESExplainResponse,
)

ES = get_config()["elasticsearch"]


observe_router = APIRouter(
    prefix="/observe",
    tags=["observe"],
    dependencies=[Depends(get_current_user)],
)


def observe_letter_mode(id_letter: int, mode: str, id_model=None):
    """
    Observe hydrated letter using the given mode (prediction or training)
    """
    # if id_model is None:
    id_model = get_active_model_id()

    with SessionWrapper() as db:
        res = (
            # pylint: disable=no-member
            db.query(SiancedbLetter)
            .filter(SiancedbLetter.id_letter == id_letter)
            .all()
        )
        for letter in res:
            result = {
                "id_letter": letter.id_letter,
                "name": letter.name,
                "codep": letter.codep,
                "content": hydrate_letter(letter, mode=mode, id_model=id_model),
                "date": letter.sent_date,
                "nb_pages": letter.nb_pages,
                "interlocutor": Interlocutor.from_orm(letter.interlocutor)
                if letter.interlocutor is not None
                else None,
                "metadata_si": MetadataSI.from_orm(letter.metadata_si)
                if letter.metadata_si is not None
                else None,
            }
            return result
    raise HTTPException(status_code=404, detail="The letter does not seem to exist")


@observe_router.get("/letter", response_model=ObservableLetter)
def observe_letter(
    id_letter: int,
    id_model: Optional[str] = None,
    user: User = Depends(get_current_user),
):

    return observe_letter_mode(id_letter, mode=PREDICTION_MODE, id_model=id_model)


@observe_router.post("/explain/letter", response_model=ESExplainResponse)
def explain_letter(query: EQuery, letter_id: int):
    realq = build_explain_query(query)
    conn = es.Elasticsearch(
        hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
    )

    res = conn.explain(ES["letters"], letter_id, body=realq)
    return res
