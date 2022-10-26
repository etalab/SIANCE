from siancebackend.prefect_tasks import (
    build_predictions,
    BuildSectionsDemands,
    get_letters_no_predictions,
)
from siancedb.models import get_active_model_id

from prefect import unmapped, Flow, context, Parameter
from siancedb.config import set_config_file
import os
logger = context.get("logger")

PREPROD_PROJECT_NAME = "siance-preprod"
CONFIG_PREPROD = "config.preprod.json"
set_config_file(CONFIG_PREPROD)


def register_flow():

    with Flow("Only save required predictions in database (but NOT in index)") as flow:
        try:
            os.remove("/tmp/tika.log")
        except OSError:
            print("Was not able to delete /tmp/tika.log. It might not exist or it might belong to root")
        id_model = Parameter(
            "Model to use for predictions. Default: the last 'activated' model",
            default=get_active_model_id(),
        )
        build_sections_demands = BuildSectionsDemands()
        letters = get_letters_no_predictions.run()
        # to get the necessary cut in sections and demands before predicting
        divided_letter_tuple = build_sections_demands.map(letters)
        predictions = build_predictions.map(
            divided_letter_tuple, id_model=unmapped(id_model)
        )
    flow.register(project_name=PREPROD_PROJECT_NAME)


if __name__ == "__main__":
    register_flow()
