from siancebackend.classifiers.classify_topics import (
    build_new_model,
)
from prefect import task, Task, Flow, context, Parameter
from siancebackend.classifiers.embeddings import recompute_embeddings
from siancedb.config import set_config_file

logger = context.get("logger")

PROD_PROJECT_NAME = "siance-prod"
CONFIG_PROD = "config.prod.json"
set_config_file(CONFIG_PROD)


@task
def prepare_embeddings(must_regenerate_embeddings: bool = False):
    if must_regenerate_embeddings:
        recompute_embeddings()


@task
def build_save_model(architecture: str = "grid-search", top_n: int = 1):
    build_new_model(architecture=architecture, top_n=top_n)


def register_flow():
    with Flow("Train a new model") as flow:
        architecture = Parameter("Choice of architecture", default="grid-search").run()
        must_refresh = Parameter(
            "Refresh new embeddings before training model", default=False
        ).run()
        top_n = Parameter(
            "In case of custom hierarchical model, number of categories to consider",
            default=1,
        )
        prepare_embeddings(must_regenerate_embeddings=must_refresh)
        build_save_model(
            architecture=architecture, top_n=top_n, upstream_tasks=[prepare_embeddings]
        )
    flow.register(PROD_PROJECT_NAME)


if __name__ == "__main__":
    register_flow()
