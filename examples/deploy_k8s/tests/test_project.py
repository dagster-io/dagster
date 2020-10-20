import os

import yaml
from dagster import execute_pipeline
from dagster.utils import file_relative_path

from ..example_project.example_repo.repo import example_pipe


def test_example_project():
    with open(
        file_relative_path(
            __file__, os.path.join("..", "example_project", "run_config", "pipeline.yaml")
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
        assert execute_pipeline(example_pipe, run_config=run_config).success
