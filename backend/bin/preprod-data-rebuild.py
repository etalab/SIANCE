import os

from siancebackend.prefect_tasks import (
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
from prefect import Flow, Parameter, unmapped
from siancedb.config import set_config_file, get_config
import os

CONFIG_PREPROD = "config.preprod.json"
set_config_file(CONFIG_PREPROD)
cfg = get_config()

def get_old_download_paths():
    return [
        os.path.join(cfg["letters"]["data"]["letters_pdf"], filename)
        for filename in os.listdir(cfg["letters"]["data"]["letters_pdf"])
    ]
            
def rebuild_preprod_data(id_model=None):
    build_letter = BuildLetter()
    build_siv2metadata = BuildSiv2MetadataInterlocutor()
    build_demands = BuildSectionsDemands()
    build_trigrams = BuildTrigrams()
    build_isotopes = BuildIsotopes()
    build_predicted_metadata = BuildPredictedMetadata()

    with Flow("RebuildPreprod") as flow:
        try:
            os.remove("/tmp/tika.log")
        except OSError:
            print("Was not able to delete /tmp/tika.log. It might not exist or it might belong to root")
        if id_model is None:
            id_model = get_active_model_id()
        letter_paths = get_old_download_paths()
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
    flow.run()

if __name__ == "__main__":
    rebuild_preprod_data(29)