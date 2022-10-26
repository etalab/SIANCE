from siancebackend.prefect_tasks import (
    FetchNewLetters,
    Download,
    BuildLetter,
    BuildSiv2MetadataInterlocutor,
    BuildSectionsDemands,
    BuildTrigrams,
    BuildIsotopes,
    build_predictions,
    BuildPredictedMetadata,
    fill_index,
)
from siancedb.models import get_active_model_id
from siancebackend.indexation import (
    labels_dict,
)
from prefect import Flow, context, Parameter, unmapped
from siancedb.config import set_config_file
import os
logger = context.get("logger")

PROD_PROJECT_NAME = "siance-prod"
CONFIG_PROD = "config.prod.json"
set_config_file(CONFIG_PROD)


def register_flow():

    fetch_new_letters = FetchNewLetters()
    download = Download()
    build_letter = BuildLetter()
    build_siv2metadata = BuildSiv2MetadataInterlocutor()
    build_demands = BuildSectionsDemands()
    build_trigrams = BuildTrigrams()
    build_isotopes = BuildIsotopes()
    build_predicted_metadata = BuildPredictedMetadata()

    with Flow("ProcessLettersData") as flow:
        try:
            os.remove("/tmp/tika.log")
        except OSError:
            print("Was not able to delete /tmp/tika.log. It might not exist or it might belong to root")
        id_model = Parameter(
            "Model to use for predictions. Default: the last 'activated' model",
            default=get_active_model_id(),
        )
        rss_letters = fetch_new_letters.run()
        letter_paths = download.map(rss_letters)
        letters = build_letter.map(letter_paths)
        metadata_interlocutor_tuple = build_siv2metadata.map(letters)
        trigrams = build_trigrams.map(letters)
        isotopes = build_isotopes.map(letters)
        divided_letter_tuple = build_demands.map(letters)
        predicted_metadata = build_predicted_metadata.map(divided_letter_tuple)
        predictions = build_predictions.map(
            divided_letter_tuple=divided_letter_tuple, id_model=unmapped(id_model)
        )
        fill_index.map(
            letters,
            id_model=unmapped(id_model),
            labels=unmapped(labels_dict()),
            upstream_tasks=[
                metadata_interlocutor_tuple,
                predictions,
                predicted_metadata,
                trigrams,
                isotopes,
            ],
        )
    flow.register(project_name=PROD_PROJECT_NAME)


if __name__ == "__main__":
    register_flow()
