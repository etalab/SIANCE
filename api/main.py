#!/usr/bin/env python3

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware


from siancedb.models import (
    SiancedbActionLog,
    log_action,
)

from siancedb.config import get_config

from .schemes import (
    User,
    PostStatisticsLog,
)


from .routers.users import user_router
from .routers.auth import get_current_user, auth_router, check_download_token
from .routers.search import search_router
from .routers.dashboard import dashboard_router
from .routers.suggestions import suggestion_router
from .routers.exports import exports_router
from .routers.admin import admin_router
from .routers.observe import observe_router
from .routers.annotate import annotate_router
from .routers.trends import trends_router
from .routers.watch import watch_router


app = FastAPI(
    title="SIANCE - API",
    description="Access to all SIANCE data through a single api",
    version="1.0.0",
)
cfg = get_config()

logger = logging.getLogger("siance-api-log")

ES = get_config()["elasticsearch"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(suggestion_router)
app.include_router(admin_router)
app.include_router(exports_router)
app.include_router(search_router)
app.include_router(dashboard_router)
app.include_router(observe_router)
app.include_router(annotate_router)
app.include_router(trends_router)
app.include_router(watch_router)



@app.get("/")
def read_root():
    return {"ApiStatus": "Working"}


@app.post("/statistics", tags=["statistics"], response_model=PostStatisticsLog)
def append_new_action_log(
    action: PostStatisticsLog, user: User = Depends(get_current_user)
):
    log_action(
        SiancedbActionLog(
            id_user=user.id_user,
            action=action.action_type,
            details=action.details,
        )
    )
    return PostStatisticsLog
