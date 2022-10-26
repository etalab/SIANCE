#!/usr/bin/env python3
# This file contains all the schemas
# used to talk to the API as well as
# the API responses

from typing import Optional, List, Union, Tuple, Dict
from fastapi.param_functions import Query
from pydantic import BaseModel, Field
from datetime import datetime, date

from siancedb.elasticsearch.schemes import EQuery, ELetter, EDemand

from siancedb.letter_summary import AnnotatedText


class User(BaseModel):
    """ An authenticated user """

    id_user: int = Field(
        ..., description="SIANCE's unique identifier for the current user"
    )
    username: str = Field(
        ..., description=" The name of the user that is authenticated"
    )

    fullname: str = Field(
        ...,
        description="Full name of the user as obtained through the Active Directory",
    )

    is_admin: bool = Field(..., description="Is the current user an admin ?")


class UserToken(BaseModel):
    """The authentication token is an encrypted timed certificate
    of the fact that the user has (successfully) logged.
    """

    access_token: str = Field(
        ...,
        description="A HS256 encoding of a JSON object containing username and expiration date",
    )

    user: User = Field(..., description="The user’s configuration")

    token_type: str = Field(
        ...,
        description="The type of token used in the app, in our case it is a Bearer token",
    )


class DownloadToken(BaseModel):
    """ A temporary token for downloads """

    download_token: str = Field(
        ...,
        description="A HS256 encoding of a JSON object containing username and expiration date",
    )


class UserPreStoredSearch(BaseModel):
    """ A request for storing a SIANCE search """

    id_user: int = Field(
        ..., description="Unique identifier of the user who saved the search"
    )
    query: EQuery = Field(..., description="The search that was saved")
    name: str = Field(..., description="The name given to the search by the user")


class UserStoredSearch(BaseModel):
    """ A stored search saved by a SIANCE user """

    id_stored_search: Optional[int] = Field(
        ..., description="Unique identifier of the stored search"
    )
    id_user: int = Field(
        ..., description="Unique identifier of the user who saved the search"
    )
    query: EQuery = Field(..., description="The search that was saved")
    name: str = Field(..., description="The name given to the search by the user")
    last_seen: Optional[datetime] = Field(
        ...,
        description="Last datetime where the user fetched the results from this search",
    )

    class Config:
        orm_mode = True


class UserStoredSearchWithNewCount(BaseModel):
    """UserStoredSearch enriched with the number of
    new elements
    """

    stored_search: UserStoredSearch
    new_results: int


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
    exploration: Optional[bool] = None # if true, mean this annotation was proposed for "machine learning exploration" purpose


class WatchQueries(BaseModel):
    queries: List[EQuery]
    
    
class AnnotationsPost(BaseModel):
    annotations: List[Annotation] = Field(
        ...,
        description="the list of validated annotations to save in database"
    )


class AnnotationsGet(BaseModel):
    category: str = Field(
        ...,
        description="The category of (high-level class) we want to annotate"
    )
    
    
class SearchLog(BaseModel):
    action_type: str = "SEARCH"
    details: EQuery


class OpenPDFLog(BaseModel):
    class OpenPDFLogDetails(BaseModel):
        pdf_id: str = Field(
            ..., description="Name of the pdf file to fetch, like INSSN-XXX-2020-XXXX"
        )

    action_type: str = "OPEN_PDF"
    details: OpenPDFLogDetails


class OpenSIV2Log(BaseModel):
    class OpenSIV2LogDetails(BaseModel):
        letter_id: int = Field(
            ..., description="The SIANCE unique identifier of the letter opened"
        )

    action_type: str = "OPEN_SIV2"
    details: OpenSIV2LogDetails


class OpenObserveLog(BaseModel):
    class OpenObserveLogDetails(BaseModel):
        letter_id: int = Field(
            ..., description="The SIANCE unique identifier of the letter opened"
        )

    action_type: str = "OPEN_OBSERVE"
    details: OpenObserveLogDetails


PostStatisticsLog = Union[OpenObserveLog, OpenPDFLog, OpenSIV2Log]


class Suggestion(BaseModel):
    value: str
    count: Optional[int]
    id: Optional[Union[int, str]]


class SuggestFiltersResponse(BaseModel):
    site_name: List[Suggestion]
    interlocutor_name: List[Suggestion]
    theme: List[Suggestion]
    sectors: List[Suggestion]
    pilot_entity: List[Suggestion]
    resp_entity: List[Suggestion]
    topics: List[Suggestion]
    equipments_trigrams: List[Suggestion]
    isotopes: List[Suggestion]
    domains: List[Suggestion]
    natures: List[Suggestion]
    paliers: List[Suggestion]
    region: List[Suggestion]


class SuggestResponse(SuggestFiltersResponse):
    date: List[Tuple[datetime, int]] = Field(
        ..., description="Date histogram repartition of results"
    )
    dym: List[str] = Field(
        ...,
        description="Suggestions of « did you mean » to correct spelling for instance",
    )


class ProjectIndicators(BaseModel):
    """The project’s indicators
    -> number of searches per day
    -> number of unique client connections per day
    -> number of SIv2 extractions per day
    -> number of refreshes
    -> total number of users ever logged
    """

    search: List[Tuple[date, int]]
    ucpd: List[Tuple[date, int]]
    open_siv2: List[Tuple[date, int]]
    user_refresh: List[Tuple[date, int]]
    total_users: int


class Interlocutor(BaseModel):
    """ SIANCE interlocutor """

    id_interlocutor: int
    siren: str
    siret: str
    name: Optional[str]
    lon: Optional[int]
    lat: Optional[int]
    postal_code: Optional[int]
    city: Optional[str]
    main_site: Optional[str]
    region: Optional[str]

    class Config:
        orm_mode = True


class MetadataSI(BaseModel):
    id_metadata: int
    theme: Optional[str]
    doc_id: Optional[str]

    date_ins_end: Optional[date]
    date_mail: Optional[date]

    sectors: List[str]
    domains: Optional[List[str]]

    cnpe_name: Optional[str]
    inb_name: Optional[str]
    inb_num: Optional[str]
    cnpe_palier: Optional[str]
    ludd_criticity: Optional[str]
    inb_nature: Optional[str]

    site: Optional[str]

    class Config:
        orm_mode = True


class ObservableLetter(BaseModel):
    """Enriched letter for observation.
    Beware that `content` is built around a recursive
    type!
    """

    id_letter: int
    name: str
    codep: Optional[str]
    content: List[AnnotatedText]
    date: Optional[date]
    nb_pages: Optional[int]
    interlocutor: Optional[Interlocutor]
    metadata_si: Optional[MetadataSI]


class ESExplainResponse(BaseModel):
    """ Elasticsearch's explain response type """

    matched: bool
    # FIXME: is there anywhere a description of elasticsearch's
    # explain output schema ?
    explanation: Dict


class SianceSubcategory(BaseModel):
    subcategory: str
    category: str
    id_label: int
    research: bool
    fishbone: bool
    is_rep: bool
    is_ludd: bool
    is_npx: bool
    is_transverse: bool
    description: Optional[str]
    creation_date: date

    class Config:
        orm_mode = True


class SianceCategory(BaseModel):
    category: str
    subcategories: List[SianceSubcategory]


class TrainingExample(BaseModel):
    id_annotation: int
    id_letter: int
    start: int
    end: int
    sentence: str
    id_label: int
    date: date


class DatabaseStatus(BaseModel):
    total_siv2: int
    total_letters: int


class MachineLearningStatus(BaseModel):
    total_letters: int
    total_annotated_letters: int
    total_annotations: int
    total_predictions: int


class UsageStatisticSeries(BaseModel):
    name: str
    users: int
    first: int = Field(..., alias="25%")
    second: int = Field(..., alias="50%")
    third: int = Field(..., alias="75%")


class SianceGlobalStatistics(BaseModel):
    weekUsers: int
    monthUsers: int
    launchUsers: int
    weeklyTraffic: int
    monthlyTraffic: int
    launchTraffic: int
    exportSeries: List[UsageStatisticSeries]
    filterSeries: List[UsageStatisticSeries]


class LettersSearchResult(BaseModel):
    doc_id: int
    highlight: List[str]
    source: ELetter = Field(..., alias="_source")
    score: int = Field(..., alias="_score")


class DemandsSearchResult(BaseModel):
    doc_id: int
    highlight: List[str]
    source: EDemand = Field(..., alias="_source")
    score: int = Field(..., alias="_score")


class LettersSearchResponse(BaseModel):
    total: int
    hits: List[LettersSearchResult]


class DemandsSearchResponse(BaseModel):
    total: int
    hits: List[DemandsSearchResult]


class CRES(BaseModel):
    id_cres: Optional[str]
    siv2: Optional[str]
    content: Optional[str]
    site_name: Optional[str]
    etablissement: Optional[str]
    date: date


class DashboardRegion(BaseModel):
    name: str
    code: str
    count: int
    nb_interlocutors: int


class DashboardRegions(BaseModel):
    region_11: DashboardRegion = Field(..., alias="11", description="Île-de-France")
    region_24: DashboardRegion = Field(
        ..., alias="24", description="Centre-Val de Loire"
    )
    region_27: DashboardRegion = Field(
        ..., alias="27", description="Bourgogne-Franche-Comté"
    )
    region_28: DashboardRegion = Field(..., alias="28", description="Normandie")
    region_32: DashboardRegion = Field(..., alias="32", description="Hauts-de-France")
    region_44: DashboardRegion = Field(..., alias="44", description="Grand Est")
    region_52: DashboardRegion = Field(..., alias="52", description="Pays de la Loire")
    region_53: DashboardRegion = Field(..., alias="53", description="Bretagne")
    region_75: DashboardRegion = Field(
        ..., alias="75", description="Nouvelle-Aquitaine"
    )
    region_01: DashboardRegion = Field(..., alias="01", description="Guadeloupe")
    region_02: DashboardRegion = Field(..., alias="02", description="Martinique")
    region_03: DashboardRegion = Field(..., alias="03", description="Guyane")
    region_04: DashboardRegion = Field(..., alias="04", description="La Réunion")
    region_06: DashboardRegion = Field(..., alias="06", description="Mayotte")
    region_76: DashboardRegion = Field(..., alias="76", description="Occitanie")
    region_84: DashboardRegion = Field(
        ..., alias="84", description="Auvergne-Rhône-Alpes"
    )
    region_93: DashboardRegion = Field(
        ..., alias="93", description="Provence-Alpes-Côte d'Azur"
    )
    region_94: DashboardRegion = Field(..., alias="94", description="Corse")


class LocBucket(BaseModel):
    id_interlocutor: Optional[int]
    id_inb: Optional[int]
    point: Optional[Tuple[int, int]]
    name: Optional[str]
    code_inb: Optional[int]
    site_name: Optional[str]
    cnpe_name: Optional[str]
    inb_name: Optional[str]
    inb_nature: Optional[str]
    is_seashore: Optional[bool]


class LuddAndRep(BaseModel):
    key: str
    count: int
    properties: LocBucket


class DashboardMap(BaseModel):
    regions: DashboardRegions
    ludd_and_rep: List[LuddAndRep]


class DashboardResponse(BaseModel):
    suggest_letters: SuggestResponse
    suggest_demands: SuggestResponse
    dashboard: DashboardMap


class CresSearch(BaseModel):
    id_interlocutor: Optional[List[int]]
    interlocutor_name: Optional[List[str]]
    site_name: Optional[List[str]]
