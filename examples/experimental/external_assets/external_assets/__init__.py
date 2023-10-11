import os

import kubernetes
from dagster import (
    Definitions,
)
from dagster_k8s import PipesK8sClient

from .external_assets import get_lake_external_assets
from .pipes import (
    telem_post_processing,
    telem_post_processing_check,
    telem_post_processing_job,
    telem_post_processing_sensor,
)

config_file = os.path.expanduser("~/.kube/config")

kubernetes.config.load_kube_config(config_file)

defs = Definitions(
    assets=[*get_lake_external_assets(), telem_post_processing],
    sensors=[telem_post_processing_sensor],
    jobs=[telem_post_processing_job],
    asset_checks=[telem_post_processing_check],
    resources={
        "k8s_pipes_client": PipesK8sClient(),
    },
)
