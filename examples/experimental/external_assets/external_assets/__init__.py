import os

import kubernetes
from dagster import (
    Definitions,
)
from dagster_k8s import PipesK8sClient

from .external_assets import external_asset_defs
from .pipes import (
    telem_post_processing,
    telem_post_processing_job,
    telem_post_processing_sensor,
)

config_file = os.path.expanduser("~/.kube/config")

kubernetes.config.load_kube_config(config_file)

defs = Definitions(
    assets=[*external_asset_defs, telem_post_processing],
    sensors=[telem_post_processing_sensor],
    jobs=[telem_post_processing_job],
    resources={
        "k8s_pipes_client": PipesK8sClient(),
    },
)
