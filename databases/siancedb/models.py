#!/usr/bin/env python3
"""
    This file contains all the Sqlalchemy models
    interfacing with the database of SIANCE.

    This includes the letters, demands,
    interlocutors and many more.

    Note that for compatibility purposes, this module
    also exposes the interfaces to use the *old*
    and *deprecated* tables of the shape `dw_*`.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Text,
    BigInteger,
    Date,
    ForeignKey,
    JSON,
    Integer,
    Float,
    String,
    UnicodeText,
    create_engine,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, DOUBLE_PRECISION
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List
from siancedb.config import get_config

## Builds the configuration
# to talk to the postgres database.

PG = get_config()["postgres"]

PG_ACCESS_USER = PG["user"]
PG_ACCESS_PASS = PG["pass"]
PG_ACCESS_HOST = PG["host"]
PG_ACCESS_PORT = PG["port"]
PG_ACCESS_DBNAME = PG["dbname"]

PG_ACCESS_URL = (
    "postgresql://"
    + PG_ACCESS_USER
    + ":"
    + PG_ACCESS_PASS
    + "@"
    + PG_ACCESS_HOST
    + ":"
    + PG_ACCESS_PORT
    + "/"
    + PG_ACCESS_DBNAME
)

## To talk to the postgres database using SQLAlchemy
# we create an "engine" whose purpose is to
# translate queries and dialog with the database
engine = create_engine(PG_ACCESS_URL, pool_pre_ping=True, echo=False)

## To talk to the postgres database using SQLAlchemy
# we also create a "sessionmaker" that will handle
# the actual "connection" to the database, and use the "engine"
# to translate the queries.
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


## To define all the tables,
# we use the "declarative" version of SQLAlchemy
# allowing us to have some kind of ORM
# we bind it to the engine
Base = declarative_base(bind=engine)

UNKNOWN = "INCONNU·E·S"
UNKNOWN_DATE = datetime(1970, 1, 1)


class SessionWrapper:
    def __enter__(self):
        self.sess = SessionLocal()
        return self.sess

    def __exit__(self, type, value, tb):
        # pylint: disable=maybe-no-member
        self.sess.close()


## To launch a session,
# we ask for a temporary connection with the database
# this will be closed when we are done with our requests.
def get_db():
    """Temporary requests a db session
    this is used with Fast-API as a dependency and
    can be used in regular python code with

    for db in get_db():
        # use the database

    This automatically closes the database afterwards.
    Note that this is not a with statement because
    Fast-API excpects a generator...
    """
    db = SessionLocal()
    try:
        yield db
    except:  # if something went wrong, rollback!
        # pylint: disable=maybe-no-member
        db.rollback()
    finally:
        db.close()  # pylint: disable=maybe-no-member


def get_active_model_id() -> int:
    with SessionWrapper() as db:
        try:
            id_model = (
                db.query(SiancedbModel).filter(SiancedbModel.is_active).first()
            ).id_model
        except AttributeError:
            id_model = 0
    return id_model


class SiancedbUser(Base):
    """
    This table lists all the users
    of the SIANCE app along with their
    respective permissions.

    This will allow to track the actions
    done by users (like, dislike, annot...)
    as well as count the number of _unique_
    connections.
    """

    __tablename__ = "ape_users"
    id_user = Column(Integer, primary_key=True)
    "The unique id of a user"
    username = Column(UnicodeText, nullable=False)
    fullname = Column(UnicodeText, nullable=True)
    is_admin = Column(Boolean, nullable=False)
    prefs = Column(UnicodeText, nullable=False, default="{}")
    creation_date = Column(Date, nullable=False, default=func.now())


class SiancedbUserStoredSearch(Base):
    """
    This table lists all the saved user searches
    that are used to build notifications
    when new letters are fetched.
    """

    __tablename__ = "ape_user_stored_searches"
    id_stored_search = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey("ape_users.id_user"), nullable=False)
    name = Column(UnicodeText, nullable=False)
    query = Column(JSON, nullable=True)
    last_seen = Column(DateTime(timezone=True), default=func.now(), nullable=False)


class SiancedbActionLog(Base):
    """
    This table lists all the actions
    made by users at given dates in order
    to build statistics of usage.
    """

    __tablename__ = "ape_actions_logs"
    id_action = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey("ape_users.id_user"), nullable=False)
    date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    action = Column(UnicodeText, nullable=False)
    """ This action can only be one of the following:
        SEARCH, USER_CREATION, USER_CONNECTION,
        OPEN_PDF, OPEN_SIV2,
        OPEN_TRAINING, OPEN_OBSERVE
    """
    details = Column(UnicodeText)


class SiancedbLabel(Base):
    """
    This table lists the available labels
    for training / prediction and
    gives a description along with
    "categories" to classify those labels
    """

    __tablename__ = "ape_labels"
    id_label = Column(Integer, primary_key=True, unique=True, nullable=False)
    "The unique id to identify every possible class (these classes are notably used in classification model)"
    category = Column(UnicodeText, nullable=False)
    subcategory = Column(String, nullable=False)
    research = Column(Boolean, nullable=False, default=True)
    fishbone = Column(Boolean, nullable=False, default=False)
    is_rep = Column(Boolean, nullable=False)
    is_ludd = Column(Boolean, nullable=False)
    is_npx = Column(Boolean, nullable=False)
    is_transverse = Column(Boolean, nullable=False)
    description = Column(String)
    creation_date = Column(Date, nullable=False, default=func.now())


class SiancedbPredictedMetadata(Base):
    """
    This table lists the metadata predicted from the content of the letters (completing missing SI metadata)
    """

    __tablename__ = "ape_predicted_metadata"
    id_predicted_metadata = Column(
        Integer, primary_key=True, unique=True, nullable=False
    )
    id_letter = Column(Integer, ForeignKey("ape_letters.id_letter"))
    theme = Column(UnicodeText, nullable=True)


class SiancedbThemeValorisation(Base):
    """
    This table lists
    for each possible value of raw_theme
    in ape_letters the corresponding
    'valorisations'
    1. A « cleaned » version of the theme name
    2. A group name
    3. A subgroup name
    4. Domains (REP, LUDD, OA...) that are associated

    This table is build from /Prototypage/dominique_utf8.csv
    """

    __tablename__ = "ape_theme_valorisation"

    id_valorisation = Column(Integer, primary_key=True)
    raw_theme = Column(UnicodeText, nullable=False)
    domain = Column(ARRAY(UnicodeText), nullable=False)
    cleaned_theme = Column(UnicodeText, nullable=False)
    group = Column(UnicodeText, nullable=False)
    subgroup = Column(UnicodeText, nullable=False)
    concept = Column(UnicodeText, nullable=False)
    subconcept = Column(UnicodeText, nullable=False)
    creation_date = Column(Date, nullable=False, default=func.now())


class SiancedbDocument(Base):
    """
    This table lists the documents
    that are manually fed to the database
    by users. It is needed to keep track of said
    documents after their processing
    that extracts relevant information
    in the table `ape_indicators` for instance.
    """

    __tablename__ = "ape_documents"

    id_document = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    creation_date = Column(Date, nullable=False, default=func.now())
    user = Column(Integer, ForeignKey("ape_users.id_user"), nullable=False)
    " The user that added this document "
    nature = Column(UnicodeText, nullable=False)
    " Description of the nature of the document (Letter/Indicator/PIC)"
    link = Column(UnicodeText, nullable=True)
    "The link of the PDF on the server"


class SiancedbModel(Base):
    """
    This table lists all the trained classifiers (machine learning models)
    """

    __tablename__ = "ape_models"

    id_model = Column(Integer, primary_key=True)
    is_active = Column(Boolean, nullable=False)
    "A boolean indicating which machine learning model to use in production"
    name = Column(UnicodeText, nullable=True)
    "(Optional) a name describing the model"
    link = Column(UnicodeText, nullable=False)
    "The link of the model on the server"
    creation_date = Column(Date, nullable=False, default=func.now())
    "The date the model was inserted by database"
    score = Column(Float, nullable=True)
    "A score describing how much the model is reliable"
    id_labels = Column(ARRAY(Integer), nullable=False)
    "The list of id labels the model was train on"
    score_labels = Column(ARRAY(Float), nullable=True)
    """The corresponding score for every class. If the score is unknown, e.g if there is no example in validation set,
    the value is None. `id_labels` and `score_labels` must be aligned"""
    is_multi_output = Column(Boolean, nullable=True)
    "Boolean indicating whether the model is multi-label"

    user = Column(Integer, ForeignKey("ape_users.id_user"), nullable=False)
    "Who trained the model"


class SiancedbSection(Base):
    """
    This table lists the sections extracted from
    the letters in ape_letters.
    """

    __tablename__ = "ape_sections"

    id_section = Column(Integer, primary_key=True)
    id_letter = Column(Integer, ForeignKey("ape_letters.id_letter"))
    priority = Column(Integer, nullable=False)
    """The priority of the demand, it can be 
    0 -> « Synthèse de l'inspection »
    1  -> A « demandes d’actions correctives »
    2  -> B « demandes d’informations complémentaires »
    3 -> C « Observations »
    """
    start = Column(Integer, nullable=False)
    """The index of the start of the section with respect
    to the text in ape_letters
    """
    end = Column(Integer, nullable=False)
    """The index of the end of the section with respect
    to the text in ape_letters"""


class SiancedbDemand(Base):
    """
    This table lists the demands extracted from
    the letters in ape_letters.
    """

    __tablename__ = "ape_demands"

    id_demand = Column(Integer, primary_key=True)
    id_letter = Column(Integer, ForeignKey("ape_letters.id_letter"))
    priority = Column(Integer, nullable=False)
    """The priority of the demand, it can be 
    1  -> A « demandes d’actions correctives »
    2  -> B « demandes d’informations complémentaires »
    """
    start = Column(Integer, nullable=False)
    """The index of the start of the demand with respect
    to the text in ape_letters
    """
    end = Column(Integer, nullable=False)
    """The index of the end of the demand with respect
    to the text in ape_letters"""

    letter = relationship("SiancedbLetter", uselist=False, viewonly=True)
    """ The letter that is referenced """


class SiancedbTrigram(Base):
    """
    This table lists the trigrams extracted from
    the letters in ape_letters.
    """

    __tablename__ = "ape_trigrams"

    id_trigram = Column(Integer, primary_key=True)
    id_letter = Column(Integer, ForeignKey("ape_letters.id_letter"))
    trigram = Column(UnicodeText, nullable=False)
    """The trigram extracted from the letter"""
    trigram_full_name = Column(UnicodeText, nullable=True)
    """The `Libellé` of the extracted trigram"""

    letter = relationship("SiancedbLetter", uselist=False, viewonly=True)
    """ The letter that is referenced """


class SiancedbIsotope(Base):
    """
    This table lists the isotopes extracted from
    the letters in ape_letters.
    """

    __tablename__ = "ape_isotopes"
    id_isotope = Column(Integer, primary_key=True)
    id_letter = Column(Integer, ForeignKey("ape_letters.id_letter"), nullable=False)
    mass_number = Column(Integer, nullable=False)  # example 60
    symbol = Column(UnicodeText, nullable=False)  # example: Co


class SiancedbInterlocutor(Base):
    """
    The table containing all the intelocutors
    that the ASN ever had.
    It can be the site of a nuclear powerplant,
    a vet, a hospital, etc...
    A letter is bound to have some interlocutor.
    """

    __tablename__ = "ape_interlocutors"

    id_interlocutor = Column(Integer, primary_key=True)
    siren = Column(UnicodeText, nullable=False)
    siret = Column(UnicodeText, nullable=False)

    name = Column(UnicodeText, nullable=True)
    " Name of the local entity (siren)"

    creation_date = Column(Date, nullable=False, default=func.now())
    "The date the interlocutor was inserted by database"
    lon = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    postal_code = Column(Integer, nullable=True)
    city = Column(UnicodeText, nullable=True)
    main_site = Column(UnicodeText, nullable=True)
    region = Column(UnicodeText, nullable=True)
    """
    Warning this is the region written as a number
    """


class SiancedbInb(Base):
    """
    The table containing all the intelocutors
    that the ASN ever had.
    It can be the site of a nuclear powerplant,
    a vet, a hospital, etc...
    A letter is bound to have some interlocutor.
    """

    __tablename__ = "ape_inb"
    id_inb = Column(Integer, primary_key=True)
    siret = Column(UnicodeText, nullable=False)
    code_inb = Column(Integer, nullable=False)
    ludd_level = Column(UnicodeText, nullable=True)
    palier = Column(UnicodeText, nullable=True)
    site_name = Column(UnicodeText, nullable=True)
    cnpe_name = Column(UnicodeText, nullable=True)
    inb_name = Column(UnicodeText, nullable=True)
    inb_nature = Column(UnicodeText, nullable=True)
    is_seashore = Column(Boolean, nullable=True)


class SiancedbSIv2LettersMetadata(Base):
    """
    Ths table lists the extracted metadatas from
    the SIv2.
    """

    __tablename__ = "ape_siv2_letters_metadata"

    id_metadata = Column(Integer, ForeignKey("ape_letters.id_letter"), primary_key=True)
    letter = relationship("SiancedbLetter", uselist=False, viewonly=True)

    theme = Column(UnicodeText, nullable=True)
    """The theme of the inspection. It contains only fields from
    the table ape_theme_valorisation. """

    doc_id = Column(UnicodeText, nullable=True)
    """
    The object id of the inspection in the SIV2, useful to
    get back to the document afterwards.
    """

    date_ins_end = Column(Date, nullable=True)
    "The date of the end of the inspection"

    date_mail = Column(Date, nullable=True)
    "The date at which the mail was sent to the operator"

    nb_days = Column(DOUBLE_PRECISION, nullable=True)
    "The number of days the inspection took"

    responsible_entity = Column(UnicodeText)
    "The entity responsible for the inspection (entité responsable)"

    pilot_entity = Column(ARRAY(UnicodeText))
    "The entity that was piloting the inspection"

    pilot_agents = Column(ARRAY(UnicodeText))
    "The main agent (inspecteur pilote)"

    copilot_agents = Column(ARRAY(UnicodeText))
    "The list of copilots that were  with the agent"

    inspection_type = Column(UnicodeText)
    "The type of the inspection (courante, revue etc...) "

    sectors = Column(ARRAY(String(255)), nullable=True)
    "The sector of the inspection (LUDD, REP, NPX, ESP, TSR)"

    domains = Column(ARRAY(String(255)), nullable=True)
    "The domain of the inspection (OA, LA, Industrie, Médical, TSR, OA, Vétérinaire, RP...)"

    cnpe_name = Column(UnicodeText, nullable=True)
    inb_name = Column(UnicodeText, nullable=True)
    inb_num = Column(UnicodeText, nullable=True)
    cnpe_palier = Column(UnicodeText, nullable=True)
    ludd_criticity = Column(UnicodeText, nullable=True)
    inb_nature = Column(UnicodeText, nullable=True)

    was_programmed = Column(Boolean, nullable=True)
    "Is the inspection programmed or not ?"

    was_unexpected = Column(Boolean, nullable=True)
    "Is it an « inspection inopinée »"

    was_local = Column(Boolean, nullable=True)
    "Is it a local or a national priority ?"

    priority = Column(Integer, nullable=True)
    "The level of priority from 1 to 3"

    site = Column(UnicodeText, nullable=True)
    "The name of the site, if known"

    theme_group = Column(UnicodeText, nullable=True)
    """The theme group (regroupement) as written in the SIv2
    when not known it is set to Inconnu·e·s"""


class SiancedbCres(Base):
    """
    This table lists the CRES contained
    in the database, with all the basic informations.

    Note that because informations in the SIv2 are evolving,
    some fields are merged, some are not considered
    and some are "cleaned" before their insertion.
    """

    __tablename__ = "ape_cres"

    id_cres = Column(
        Integer,
        primary_key=True,
        unique=True,
        nullable=False,
    )

    id_interlocutor = Column(
        Integer, ForeignKey("ape_interlocutors.id_interlocutor"), nullable=True
    )
    """
    The interlocutor of the ASN for this inspection, it is uniquely identified
    because an inspection only deals with one interlocutor.
    """

    name = Column(UnicodeText, unique=True, index=True, nullable=False)
    "name is the inspection name (eg: INSSN-BDX-0000). NB: the field is used as a 'false joint' to retrieve annotations"

    siv2 = Column(UnicodeText, unique=True, index=True, nullable=False)
    "the object id obtained from the SIv2"

    summary = Column(UnicodeText, nullable=False)
    "The description of the event"

    date = Column(Date, nullable=True)
    """ The approximate date of the event (can be set to the date
        of reception if none is provided)
    """

    natures = Column(ARRAY(UnicodeText), nullable=True)
    """
        The natures of the CRES, for now, a simple 
        array of strings containing informations such as « Médecine Nucléaire »
        « CNPE », « REP-02: Mise en service d'un système de prodection ou
        de sauvegarde non souhaitée » etc...
    """

    inb_information = Column(ARRAY(UnicodeText), nullable=True)
    """ The informations relative to the potential INB. Note
    that this should be a join with the INB table...
    """
    
    site = Column(UnicodeText, nullable=True)
    "The name of the site, if known"

    last_touched = Column(Date, nullable=False, default=func.now())
    """ When was the last time meta-data information about
    the letter was fetched ? """

    # Now the links to the other tables (many-to-one)
    interlocutor = relationship("SiancedbInterlocutor", uselist=False)
    "The interlocutor associated with this letter"


class SiancedbLetter(Base):
    """
    This table lists the letters contained
    in the database, with all the basic informations.

    As a rule of thumb, all information that comes directly
    from the letter or the metadata in the SIv2 are present.
    All extracted, inferred, annotated informations are obtained
    through dedicated tables.

    Note that because informations in the SIv2 are evolving,
    some fields are merged, some are not considered
    and some are "cleaned" before their insertion.
    """

    __tablename__ = "ape_letters"

    id_letter = Column(
        Integer,
        ForeignKey("ape_documents.id_document"),
        primary_key=True,
        unique=True,
        nullable=False,
    )

    name = Column(UnicodeText, unique=True, index=True, nullable=False)
    "name is the inspection name (eg: INSSN-BDX-YYYY-0000). NB: the field is used as a 'false joint' to retrieve annotations"

    codep = Column(UnicodeText, unique=False, nullable=False)
    "The almost unique identifier of the codep CODEP-xxxx-LYO-xxx"
    # codep is not always unique because in practice for some cases several inspection folders where opened
    # on SIv2 for only one codep

    text = Column(UnicodeText, nullable=False)
    "The full text of the letter, after preprocessing of the pdf text"

    id_interlocutor = Column(
        Integer, ForeignKey("ape_interlocutors.id_interlocutor"), nullable=True
    )
    """
    The interlocutor of the ASN for this inspection, it is uniquely identified
    because an inspection only deals with one interlocutor.
    """

    last_touched = Column(Date, nullable=False, default=func.now())
    """ When was the last time meta-data information about
    the letter was fetched ? """

    sent_date = Column(Date, nullable=False)
    """ The date when the mail was sent to the interlocutor """

    nb_pages = Column(Integer, nullable=True)
    "The number of pages in the letter"

    # Now the links to the other tables (many-to-one)
    interlocutor = relationship("SiancedbInterlocutor", uselist=False)
    "The interlocutor associated with this letter"
    predictions_dyn = relationship("SiancedbPrediction", lazy="dynamic", viewonly=True)
    predictions = relationship("SiancedbPrediction")
    "The predictions associated with this letter"
    metadata_si = relationship("SiancedbSIv2LettersMetadata", uselist=False)
    "The metadatas from the SIv2"
    metadata_dyn = relationship(
        "SiancedbPredictedMetadata", lazy="dynamic", viewonly=True
    )
    metadata_predicted = relationship("SiancedbPredictedMetadata", uselist=False)
    document = relationship("SiancedbDocument", uselist=False)
    "The unique document corresponding to this letter"
    demands = relationship("SiancedbDemand", uselist=True)
    "The demands inside the letter"
    sections = relationship("SiancedbSection", uselist=True)
    "The sectionning of the letter"
    trigrams = relationship("SiancedbTrigram", uselist=True)
    """ The Trigrams in the letter """
    isotopes = relationship("SiancedbIsotope", uselist=True)
    """ The isotopes in the letter """


class SiancedbRawAnnotation(Base):
    """
    This table contains the raw annotations on letters.
    An annotation is simply a selection of text that is assigned
    to a label.
    """

    __tablename__ = "ape_raw_annotation"
    id_raw_annotation = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    " The name here is supposed to aligned with the one of ape_letters. It is a kind of 'low JOINT' between " "the tables that must be maintained if the names of letter has to change in time. It is not a foreign key so " "that ape_letters can be erased and replaced without impacting annotations (provided the joint is conserved)"
    start = Column(Integer, nullable=False)
    " The start **relative to the text in ape_letters** of the extracted text "
    end = Column(Integer, nullable=False)
    " The end **relative to the text in ape_letters** of the extracted text "
    text = Column(UnicodeText, nullable=False)
    " The text of the annotation "
    id_label = Column(Integer, ForeignKey("ape_labels.id_label"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    "When was this label inserted in the database?"
    user = Column(Integer, ForeignKey("ape_users.id_user"), nullable=False)
    "Who is responsible this annotation?"


class SiancedbTraining(Base):
    """
    This table contains the training data for the ML algorithm.
    A row is a _sentence_ along with an _annotation_ of this sentence using a _label_.
    Note that this table is entirely constructed
    using the table "ape_raw_annotation", but it is very convenient
    to have a separate one containing the actual training data to test, train and evaluate the models.

    If it was not clear at first, the main difference is that now annotations
    are linked to _sentences_ in the letter, rather than arbitrary text selections.
    """

    __tablename__ = "ape_training"
    id_annotation = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    " The name here is supposed to aligned with the one of ape_letters. It is a kind of 'low JOINT' between " "the tables that must be maintained if the names of letter has to change in time. It is not a foreign key so " "that ape_letters can be erased and replaced without impacting annotations (provided the joint is conserved)"
    start = Column(Integer, nullable=False)
    " The start **relative to the text in ape_letters** of the extracted text "
    end = Column(Integer, nullable=False)
    " The end **relative to the text in ape_letters** of the extracted text "
    sentence = Column(UnicodeText, nullable=False)
    # terms = Column(UnicodeText, nullable=False)
    id_label = Column(Integer, ForeignKey("ape_labels.id_label"), nullable=False)
    date = Column(Date, nullable=False, default=func.now())
    "When was this training data inserted?"


class SiancedbPrediction(Base):
    """
    This table contains the predicted labels for the sentences in the letters.
    This table is filled by the ML algorithm. It takes a letter
    and then for each sentence in the letter, determines all the labels
    that should be associated. For each label, we have a tuple
    (id_lettre, sentence, label).
    """

    __tablename__ = "ape_predictions"
    id_prediction = Column(Integer, primary_key=True)
    id_letter = Column(Integer, ForeignKey("ape_letters.id_letter"), nullable=False)
    start = Column(Integer, nullable=False)
    " The start **relative to the text in ape_letters** of the extracted text "
    end = Column(Integer, nullable=False)
    " The end **relative to the text in ape_letters** of the extracted text "
    sentence = Column(UnicodeText, nullable=False)
    id_label = Column(Integer, ForeignKey("ape_labels.id_label"), nullable=False)
    date = Column(Date, nullable=False, default=func.now())
    "When was the prediction generated?"
    id_model = Column(Integer, ForeignKey("ape_models.id_model"), nullable=True)
    "The id of the model that made this prediction"
    decision_score = Column(Float, nullable=True)
    "In the range [0,1], the score of the decision function"


class SiancedbPipeline(Base):
    """
    OUTDATED : the object pipeline has turned useless after the use of Prefect.
    An object to manage and display the advancement of a data acquisition pipeline (for interface administration)

    """

    __tablename__ = "ape_pipelines"
    id_pipeline = Column(Integer, primary_key=True)
    "The id identifying a pipeline"
    completed_runs = Column(Integer, default=0)
    "The number of runs that have been successfully finished since the first time the pipeline was launched"
    between_runs_hours = Column(Integer, nullable=True)
    "The integer number of hours to wait between two runs. Can be null if the pipeline is set to run only once"
    id_model = Column(Integer, nullable=False)
    "The id of the model to use to classify letters"
    creation_time = Column(DateTime, default=datetime.utcnow)
    "The date the pipeline was first launched"
    last_launched_time = Column(DateTime, nullable=True)
    "The most recent time the pipeline was launched (considering a pipeline is launched when created)"
    last_finished_time = Column(DateTime, nullable=True)
    "The most recent time the pipeline finished"
    building_letters = Column(Float, default=0)
    "The percentage of advancement in the building letters step (if relevant)"
    building_trigrams = Column(Float, default=0)
    "The percentage of advancement in the building trigrams step (if relevant)"
    building_sections_demands = Column(Float, default=0)
    "The percentage of advancement in the building sections and demands step (if relevant)"
    building_si_metadata = Column(Float, default=0)
    "The percentage of advancement in the building of SI metadata (if relevant)"
    building_predicted_metadata = Column(Float, default=0)
    "The percentage of advancement in the building of complementary metadata (if relevant)"
    building_predictions = Column(Float, default=0)
    "The percentage of advancement in the predictions of letters (if relevant)"
    indexing = Column(Float, default=0)
    "The percentage of advancement in the indexation process (if relevant)"


class SiancedbCatSousCat(Base):
    """The schema
    of dw_mapping_catsouscat_columnname
    in the production and recette database
    """

    __tablename__ = "dw_mapping_catsouscat_columnname"

    categorie = Column(UnicodeText)
    sous_categorie = Column(UnicodeText)
    is_REP = Column(BigInteger)
    is_LUDD = Column(BigInteger)
    is_NPX = Column(BigInteger)
    nb_annotations = Column(UnicodeText)
    tp = Column("type", UnicodeText)
    column_name = Column(UnicodeText, primary_key=True)
    precision = Column(DOUBLE_PRECISION)


class SiancedbDWLettre(Base):
    """The schema
    of dw_lettres, this is for transition purpose only.
    """

    __tablename__ = "dw_lettres"

    id_lettre = Column(DOUBLE_PRECISION, primary_key=True)
    nom_lettre = Column(Text)
    lettre = Column(Text)

    ville = Column(Text)
    departement = Column(Text)

    date = Column(Text)
    date_fin_inspect = Column(Text)
    date_env_let_suite = Column(Text)

    nb_pages = Column(Integer)
    nb_jour = Column(Integer)

    entite_resp = Column(Text)
    entite_pilote = Column(Text)

    agent_charge = Column(Text)
    agent_charge_resp = Column(Text)
    agent_copilote = Column(Text)

    type_inspect = Column(Text)
    scope = Column(Text)
    inspect_prog = Column(Text)
    domaine = Column(Text)
    inspect_inop = Column(Text)
    inspect_priorite = Column(Text)

    theme_principal = Column(Text)
    theme_principal_corr = Column(Text)
    regroupement = Column(Text)
    reference_event = Column(Text)


def log_action(action: SiancedbActionLog):
    with SessionWrapper() as db:
        db.add(action)
        db.commit()

def write_training(annotations: List[SiancedbTraining]):
    with SessionWrapper() as db:
        [db.add(annotation) for annotation in annotations]
        db.commit()