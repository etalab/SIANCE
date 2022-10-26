from siancebackend.prefect_tasks import (
    FetchLettersToRefresh,
    RefreshSiv2MetadataInterlocutor,
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

PREPROD_PROJECT_NAME = "siance-preprod"
CONFIG_PREPROD = "config.preprod.json"
set_config_file(CONFIG_PREPROD)


def register_flow():
    with Flow("RefreshLettersData") as flow:
        try:
            os.remove("/tmp/tika.log")
        except OSError:
            print("Was not able to delete /tmp/tika.log. It might not exist or it might belong to root")
        # get active model id
        id_model = Parameter(
            "Model of the predictions to store in the index. Default: the last 'activated' model",
            default=get_active_model_id(),
        )
        fetch_letters = FetchLettersToRefresh()
        refresh_metadata = RefreshSiv2MetadataInterlocutor()
        letters = fetch_letters.run()
        metadata_interlocutor_tuple = refresh_metadata.map(letters)
        fill_index.map(
            letters,
            id_model=unmapped(id_model),
            labels=unmapped(labels_dict()),
            upstream_tasks=[metadata_interlocutor_tuple],
        )
    flow.register(project_name=PREPROD_PROJECT_NAME)


if __name__ == "__main__":
    register_flow()
