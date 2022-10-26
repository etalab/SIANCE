from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

import json

from sqlalchemy.orm.exc import NoResultFound

import elasticsearch as es

from siancedb.elasticsearch.queries import (
    build_paginated_query,
)
from siancedb.elasticsearch.schemes import EQuery

from siancedb.models import (
    SessionWrapper,
    SiancedbActionLog,
    SiancedbUser,
    SiancedbUserStoredSearch,
)

from siancedb.config import get_config

from .auth import get_current_user

from ..schemes import (
    User,
    UserStoredSearch,
    UserPreStoredSearch,
    UserStoredSearchWithNewCount,
)

ES = get_config()["elasticsearch"]


user_router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(get_current_user)],
)


@user_router.get("/last_search", response_model=List[EQuery])
def get_last_search(user: User = Depends(get_current_user)):
    with SessionWrapper() as db:
        last_search = (
            db.query(SiancedbActionLog)
            .filter(
                SiancedbActionLog.id_user == user.id_user,
                SiancedbActionLog.action == "SEARCH",
            )
            .order_by(SiancedbActionLog.date.desc())
            .limit(2)
        )

        def try_read_query(x: Dict):
            try:
                return EQuery(**x)
            except:
                return None

        possible_last_searches = [
            try_read_query(json.loads(q.details)) for q in last_search
        ]

        return [x for x in possible_last_searches if x is not None]


@user_router.put("/saved_search", response_model=UserStoredSearch)
def save_my_search(
    user_search: UserPreStoredSearch, user: User = Depends(get_current_user)
):
    with SessionWrapper() as db:
        user_search_orm = SiancedbUserStoredSearch(**jsonable_encoder(user_search))
        db.add(user_search_orm)
        db.commit()
        return UserStoredSearch.from_orm(user_search_orm)


@user_router.post("/saved_search", response_model=UserStoredSearch)
def update_my_search(
    user_search: UserStoredSearch, user: User = Depends(get_current_user)
):
    with SessionWrapper() as db:
        try:
            user_search_orm = (
                db.query(SiancedbUserStoredSearch)
                .filter(
                    SiancedbUserStoredSearch.id_stored_search
                    == user_search.id_stored_search
                )
                .one()
            )
        except NoResultFound:
            raise HTTPException(404, "Saved search does not exist")

        superdict = jsonable_encoder(user_search)
        user_search_orm.query = superdict["query"]
        user_search_orm.last_seen = superdict["last_seen"]
        db.add(user_search_orm)
        db.commit()
        return UserStoredSearch.from_orm(user_search_orm)


@user_router.delete("/saved_search", response_model=UserStoredSearch)
def delete_my_search(
    user_search: UserStoredSearch, user: User = Depends(get_current_user)
):
    with SessionWrapper() as db:
        for obj in (
            db.query(SiancedbUserStoredSearch)
            .filter(
                SiancedbUserStoredSearch.id_stored_search
                == user_search.id_stored_search
            )
            .all()
        ):
            db.delete(obj)
        db.commit()
        return user_search


@user_router.get("/saved_search", response_model=List[UserStoredSearchWithNewCount])
def get_my_search(user: User = Depends(get_current_user)):
    def check_if_new_results(s: UserStoredSearch):
        realq = build_paginated_query(
            EQuery(
                sentence=s.query.sentence,
                filters=s.query.filters,
                daterange=datetime.now(),  # s.last_seen,
            ),
            0,
            ["content"],
        )

        conn = es.Elasticsearch(
            hosts=[{"host": ES["host"], "port": ES["port"]}], timeout=30
        )

        res = conn.search(index=ES["letters"], body=realq)
        try:
            return res["hits"]["total"]["value"]
        except KeyError:
            return 0

    with SessionWrapper() as db:
        res = (
            db.query(SiancedbUserStoredSearch)
            .filter(SiancedbUserStoredSearch.id_user == user.id_user)
            .all()
        )

        return [
            {
                "stored_search": UserStoredSearch.from_orm(s),
                "new_results": check_if_new_results(UserStoredSearch.from_orm(s)),
            }
            for s in res
        ]
