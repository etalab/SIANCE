from datetime import date, timedelta, datetime
import os
from typing import List, Dict, Iterable, Tuple

from siancedb.config import get_config


from siancebackend.letter_management.letter_acquisition import (
    RSSLetter,
    fetch_rss_letters,
    download_letter,
)
from siancedb.models import (
    SiancedbIsotope,
    SiancedbLetter,
    SiancedbSection,
    SiancedbDemand,
    SiancedbModel,
    SiancedbTrigram,
    SiancedbPrediction,
    SiancedbSIv2LettersMetadata,
    SiancedbPredictedMetadata,
    SiancedbInterlocutor,
    SessionWrapper,
)
from siancebackend.letters import build_one_letter
from siancebackend.siv2metadata import build_siv2metadata_one_letter
from siancebackend.sections_demands import build_sections_demands_one_letter
from siancebackend.trigrams import build_trigrams_one_letter, get_edf_trigrams_ref
from siancebackend.isotopes import build_isotopes_one_letter, get_isotopes_ref
from siancebackend.classifiers.classify_topics import (
    classify_topics_one_letter,
    load_pipeline,
    prepare_score_dict,
)
from siancebackend.classifiers.classify_themes import (
    prepare_classifier_encoder,
    classify_themes_one_letter,
)
from siancebackend.letter_management.sentencizer import prepare_sentencizer
from siancedb.elasticsearch.management import bulk_insert
from siancebackend.indexation import (
    letter_generator,
    labels_dict,
)

from siancebackend.ingest_cres import (
    build_one_cres,
    select_updatable_from_dump,
    index_cres,
)

from prefect import task, Task, Flow, context, Parameter


###
#  ALIAUME: some functional tasks for ingesting
#  siv2 dumps and adding them to the database
###

default_prefect_config = {
    "asn_interlocutor": "asn_interlocuteur.txt",
    "asn_cres": [
        "asn_evenmt_signif_inb.txt",
        "asn_evenmt_signif_np.txt",
    ],
}
PRF = get_config().get("prefect", default_prefect_config)


@task
def fetch_updatable_CRES():
    return [
        cres
        for dump_file in PRF["asn_cres"]
        for cres in select_updatable_from_dump(dump_file)
    ]


@task
def build_and_add_one_cres(siv2cres: Dict) -> int:
    interlocutor_file = PRF["asn_interlocutor"]
    with SessionWrapper() as db:
        cres, interlocutor = build_one_cres(siv2cres, interlocutor_file)
        db.add(interlocutor)
        db.add(cres)
        db.commit()
        return cres.id_cres


@task
def index_new_cres(id_cres: int):
    return index_cres([id_cres])


########


class FetchNewLetters(Task):
    def run(self) -> List[RSSLetter]:
        try:
            os.remove("/tmp/tika.log")
        except OSError:
            print("Was not able to delete /tmp/tika.log. It might not exist or it might belong to root")

        return list(fetch_rss_letters())


class Download(Task):
    def run(self, letter: RSSLetter) -> str:
        return download_letter(letter)


class BuildLetter(Task):
    def __init__(self, already_seen: Iterable[str] = None, **kwargs):
        if already_seen is None:
            already_seen = set()
        with SessionWrapper() as db:
            names = db.query(SiancedbLetter.name).all()
            already_seen = set(already_seen).union(row[0] for row in names)
        self.already_seen = already_seen
        super().__init__(**kwargs)

    def run(self, path: str) -> SiancedbLetter:
        # db_letter is assumed to be either empty either singleton
        # the function build directly writes in database
        name = os.path.basename(path)[:-4]
        with SessionWrapper() as db:
            old_letter = (
                db.query(SiancedbLetter)
                .filter(SiancedbLetter.name == name)
                .all()
            )
        if len(old_letter):
            self.already_seen.add(name)
            return old_letter[0]
        letter, _ = build_one_letter(
            pdf_path=path, already_seen=self.already_seen
        )  # possibly None
        with SessionWrapper() as db:
            db.add(letter)
            db.commit()
        return letter


class BuildSiv2MetadataInterlocutor(Task):
    def run(
        self, letter: SiancedbLetter
    ) -> Tuple[SiancedbSIv2LettersMetadata, SiancedbInterlocutor]:
        # if there is already siv2metadata or interlocutor in database, replace them
        with SessionWrapper() as db:
            old_metadata = (
                db.query(SiancedbSIv2LettersMetadata)
                .filter(SiancedbSIv2LettersMetadata.id_metadata == letter.id_letter)
                .all()
            )
            old_interlocutors = (
                db.query(SiancedbInterlocutor)
                .filter(SiancedbInterlocutor.id_interlocutor == letter.id_interlocutor)
                .all()
            )

            if len(old_metadata) and len(old_interlocutors):
                return old_metadata[0], old_interlocutors[0]

            siv2metadata, interlocutor = build_siv2metadata_one_letter(letter)

            if not len(old_metadata):
                db.add(siv2metadata)
            if interlocutor is not None and not len(old_interlocutors):
                db.add(interlocutor)
                letter.id_interlocutor = interlocutor.id_interlocutor
                db.add(letter)
            db.commit()
        return siv2metadata, interlocutor


class BuildSectionsDemands(Task):
    def __init__(self, **kwargs):
        self.sentencizer = prepare_sentencizer()
        super().__init__(**kwargs)

    def run(self, letter: SiancedbLetter):
        with SessionWrapper() as db:
            old_demands = (
                db.query(SiancedbDemand)
                .filter(SiancedbDemand.id_letter == letter.id_letter)
                .all()
            )
            old_sections = (
                db.query(SiancedbSection)
                .filter(SiancedbSection.id_letter == letter.id_letter)
                .all()
            )
        if len(old_demands) > 0 or len(old_sections) > 0:
            # equivalent to "the letter has already been cut in demands and sections"
            return letter, old_sections, old_demands
        sections, demands = build_sections_demands_one_letter(
            letter,
            n_previous_blocks=1,
        )
        with SessionWrapper() as db:
            db.add_all(sections)
            db.add_all(demands)
            db.commit()
            [db.refresh(section) for section in sections]
            [db.refresh(demand) for demand in demands]
        return letter, sections, demands


class BuildTrigrams(Task):
    def __init__(self, **kwargs):
        self.trigrams_ref = get_edf_trigrams_ref()
        super().__init__(**kwargs)

    def run(self, letter: SiancedbLetter) -> Iterable[SiancedbTrigram]:
        with SessionWrapper() as db:
            old_trigrams = (
                db.query(SiancedbTrigram)
                .filter(SiancedbTrigram.id_letter == letter.id_letter)
                .all()
            )
        if len(old_trigrams) > 0:
            # equivalent to "trigrams have already been extracted"
            return old_trigrams
        # the function build directly writes in database
        trigrams = build_trigrams_one_letter(letter, self.trigrams_ref)
        with SessionWrapper() as db:
            db.add_all(trigrams)
            db.commit()
            [db.refresh(trigram) for trigram in trigrams]
        return trigrams


class BuildIsotopes(Task):
    def __init__(self, **kwargs):
        self.isotopes_ref = get_isotopes_ref()
        super().__init__(**kwargs)

    def run(self, letter: SiancedbLetter) -> Iterable[SiancedbIsotope]:
        with SessionWrapper() as db:
            old_isotopes = (
                db.query(SiancedbIsotope)
                .filter(SiancedbIsotope.id_letter == letter.id_letter)
                .all()
            )
        if len(old_isotopes) > 0:
            # equivalent to "isotopes have already been extracted"
            return old_isotopes
        # the function build directly writes in database
        isotopes = build_isotopes_one_letter(letter, self.isotopes_ref)
        with SessionWrapper() as db:
            db.add_all(isotopes)
            db.commit()
            [db.refresh(isotope) for isotope in isotopes]
        return isotopes


class BuildPredictedMetadata(Task):
    def __init__(self, **kwargs):
        self.classifier, self.encoder = prepare_classifier_encoder()
        self.sentencizer = prepare_sentencizer()
        super().__init__(**kwargs)

    def run(self, divided_letter_tuple) -> SiancedbPredictedMetadata:
        letter, sections, demands = divided_letter_tuple
        with SessionWrapper() as db:
            old_metadata = (
                db.query(SiancedbPredictedMetadata)
                .filter(SiancedbPredictedMetadata.id_letter == letter.id_letter)
                .all()
            )
        if len(old_metadata) > 0:
            # equivalent to "metadata have already been predicted"
            return old_metadata[0]
        with SessionWrapper() as db:
            predicted_metadata = classify_themes_one_letter(
                letter=letter,
                sections=sections,  # sections of the same letter
                classifier=self.classifier,
                encoder=self.encoder,
                sentencizer=self.sentencizer,
            )
            db.add(predicted_metadata)
            db.commit()
            db.refresh(predicted_metadata)
        return predicted_metadata


class FetchLettersToRefresh(Task):
    def __init__(self, refresh_interval: timedelta = timedelta(days=10), **kwargs):
        self.refresh_interval = refresh_interval
        super().__init__(**kwargs)

    def run(self) -> List[SiancedbLetter]:
        try:
            os.remove("/tmp/tika.log")
        except OSError:
            print("Was not able to delete /tmp/tika.log. It might not exist or it might belong to root")

        today = date.today()
        to_refresh = []
        with SessionWrapper() as db:
            letters = db.query(SiancedbLetter).all()
            for letter in letters:
                if letter.last_touched + self.refresh_interval < today:
                    to_refresh.append(letter)
            return to_refresh


class RefreshSiv2MetadataInterlocutor(Task):
    def run(self, letter: SiancedbLetter) -> SiancedbLetter:
        # if there is already siv2metadata in database, replace them
        # if there is already interlocutor in database, it should be exactly the same due to memoization.
        # As interlocutors-letters relation is one-to-many, interlocutor must NOT be deleted during this process
        siv2metadata, interlocutor = build_siv2metadata_one_letter(letter)
        with SessionWrapper() as db:
            old_metadata = (
                db.query(SiancedbSIv2LettersMetadata)
                .filter(SiancedbSIv2LettersMetadata.id_metadata == letter.id_letter)
                .all()
            )
            if len(old_metadata):  # it is not empty, it is a singleton
                db.delete(old_metadata[0])
            db.add(siv2metadata)
            if interlocutor is not None:
                db.add(interlocutor)
            db.commit()
        with SessionWrapper() as db:
            if interlocutor is not None:
                letter.id_interlocutor = interlocutor.id_interlocutor
            letter.last_touched = datetime.now()
            db.add(letter)
            db.commit()
        return letter


@task
def build_predictions(
    divided_letter_tuple, id_model
) -> Tuple[Iterable[SiancedbPrediction], int]:
    letter, sections, demands = divided_letter_tuple
    sentencizer = prepare_sentencizer()

    with SessionWrapper() as db:
        siance_model = (
            db.query(SiancedbModel).filter(SiancedbModel.id_model == id_model).one()
        )
        pipeline = load_pipeline(siance_model.link)
        score_dict = prepare_score_dict(siance_model)

        old_predictions = (
            db.query(SiancedbPrediction)
            .filter(SiancedbPrediction.id_letter == letter.id_letter)
            .all()
        )
    if len(old_predictions) > 0:
        # equivalent to "topics for this letter have already been predicted"
        return old_predictions
    # the function classify does not commit
    with SessionWrapper() as db:
        predictions = classify_topics_one_letter(
            letter,
            sections,
            pipeline,
            id_model,
            score_dict,
            sentencizer,
        )
        db.add_all(predictions)
        db.commit()
        [db.refresh(prediction) for prediction in predictions]
    return predictions, id_model


@task
def fill_index(letter, id_model, labels=labels_dict()):
    # refreshing in "hard way" the letter to refresh all of its children
    with SessionWrapper() as db:
        letter = (
            db.query(SiancedbLetter)
            .filter(SiancedbLetter.id_letter == letter.id_letter)
            .first()
        )
        documents = letter_generator(letter, labels, id_model)
        bulk_insert(documents)


@task
def get_letters_no_predictions(id_model):
    with SessionWrapper() as db:
        return (
            db.query(SiancedbLetter)
            .filter(
                ~SiancedbLetter.predictions_dyn.any(
                    SiancedbPrediction.id_model == id_model
                )
            )
            .all()
        )
