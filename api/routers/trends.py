from fastapi import APIRouter
from ..trends.topics import (
    prepare_topics_chart,
    prepare_themes_chart,
    highlight_topics
)
from typing import List, Dict

trends_router = APIRouter(
    prefix="/trends",
    tags=["trends"],
)

@trends_router.get("/topics/highlight", response_model=List[str]) # topics less seen than before
def get_highlight():
    return highlight_topics()


@trends_router.post("/topics")  # response_model=StreamingResponse)
def get_topics(
    subcategories: List[str],
    sectors: List[str] = None,
):
    return prepare_topics_chart(subcategories, sectors)


@trends_router.post("/themes")  # response_model=StreamingResponse)
def get_themes(themes: List[str]):
    return prepare_themes_chart(themes)
