from typing import Optional, List, Union, Tuple, Dict
from pydantic import BaseModel, Field
import datetime

from siancedb.models import Base

class GeoPoint(BaseModel):
    lat: float
    lon: float


class ELetter(BaseModel):
    id_letter: int

    id_interlocutor: Optional[int]

    name: str
    content: str = ""
    date: datetime.date

    site_name: List[str]
    complementary_site_name: Optional[str]
    interlocutor_name: Optional[str]
    interlocutor_city: Optional[str]

    identifiers: List[int]

    theme: Optional[str]
    sectors: List[str]
    domains: List[str]
    natures: List[str]
    paliers: List[str]

    pilot_entity: Optional[str]
    resp_entity: Optional[str]

    demands_a: int
    demands_b: int

    topics: List[str]
    complementary_topics: List[str]
    low_confidence_topics: List[str]

    equipments_trigrams: List[str]
    equipments_full_names: List[str]
    isotopes: List[str]

    siv2: Optional[str]

    point: Optional[GeoPoint]
    region_code: Optional[str]
    region: Optional[str]


class EDemand(BaseModel):
    id_letter: int
    id_demand: int
    id_interlocutor: Optional[int]

    name: str
    content: str
    summary: str
    date: datetime.date

    site_name: List[str]
    complementary_site_name: Optional[str]
    interlocutor_name: Optional[str]
    interlocutor_city: Optional[str]

    identifiers: List[int]

    theme: Optional[str]
    sectors: List[str]
    domains: List[str]
    natures: List[str]
    paliers: List[str]

    pilot_entity: Optional[str]
    resp_entity: Optional[str]

    demand_type: str
    topics: List[str]
    complementary_topics: List[str]
    low_confidence_topics: List[str]

    equipments_trigrams: List[str]
    equipments_full_names: List[str]
    isotopes: List[str]

    siv2: Optional[str]

    point: Optional[GeoPoint]
    region_code: Optional[str]
    region: Optional[str]

EValue = Union[List[str], str]


class EFilter(BaseModel):
    site_name: EValue = []
    interlocutor_name: EValue = []
    theme: EValue = []
    sectors: EValue = []
    domains: EValue = []
    natures: EValue = []
    paliers: EValue = []
    resp_entity: EValue = []
    pilot_entity: EValue = []
    topics: EValue = []
    equipments_trigrams: EValue = []
    isotopes: EValue = []
    region: EValue = []


class QuerySorting(BaseModel):
    key: str = Field(..., description="date or _score")
    order: str = Field(..., description="asc or desc")


class EQuery(BaseModel):
    sentence: str = Field(
        ...,
        description="""The sentence of the fulltext search,
            ultimately processed using elasticsearch's simple_query_string""",
    )

    filters: EFilter = Field(
        ...,
        description="""Dictionnary of key values pairs
            such that keys are in the list of keys of our demand/letter
            that are LIST OF STRINGS""",
    )

    daterange: Optional[Union[datetime.datetime, Tuple[int, int]]] = None

    sorting: Optional[QuerySorting] = None


class FieldValuesPost(BaseModel):
    value: str
    requested_fields: List[str] = Field(..., alias="fields")

    
class Annotation(BaseModel):
    """ An annotation to be added to a letter """
    start: int
    end: int
    id_label: int
    id_letter: int
    sentence: str
    category: str
    subcategory: str
    letter_name: str


class ECres(BaseModel):
    id_cres: int
    id_interlocutor: int
    name: str = Field(
        ...,
        description="name is the inspection name (eg: INSSN-BDX-0000). NB: the field is used as a 'false joint' to retrieve annotations",
    )

    siv2: str = Field(..., description="the object id obtained from the SIv2")

    summary: str = Field(..., description="The description of the event")

    date: datetime.date = Field(
        ...,
        description=""" The approximate date of the event (can be set to the date
        of reception if none is provided)
    """,
    )

    natures: List[str] = Field(
        ...,
        description="""
        The natures of the CRES, for now, a simple 
        array of strings containing informations such as « Médecine Nucléaire »
        « CNPE », « REP-02: Mise en service d'un système de prodection ou
        de sauvegarde non souhaitée » etc...
    """,
    )

    inb_information: List[str] = Field(
        ...,
        description="""
        The informations relative to the potential INB. Note
        that this should be a join with the INB table...
    """,
    )
    siret: str
    interlocutor_name: str
    site_name: Optional[str]
