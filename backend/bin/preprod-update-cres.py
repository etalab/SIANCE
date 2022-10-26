from prefect import task, Task, Flow, context, Parameter
from siancedb.config import set_config_file
from siancebackend.prefect_tasks import (
    fetch_updatable_CRES,
    build_and_add_one_cres,
    index_new_cres,
)

# from prefect.executors import LocalDaskExecutor


logger = context.get("logger")

PREPROD_PROJECT_NAME = "siance-preprod"
CONFIG_PREPROD = "config.preprod.json"
set_config_file(CONFIG_PREPROD)


def register_flow():
    with Flow("Ingest new data from CRES dumps") as flow:
        find_new_cres = fetch_updatable_CRES()
        cres_ids = build_and_add_one_cres.map(siv2cres=find_new_cres)
        index_new_cres.map(id_cres=cres_ids)
        # Uses the default scheduler (threads)
    flow.register(PREPROD_PROJECT_NAME)


if __name__ == "__main__":
    register_flow()
