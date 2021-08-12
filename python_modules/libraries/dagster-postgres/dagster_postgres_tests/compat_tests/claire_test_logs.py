# pylint: disable=protected-access

import os
import re
import subprocess
import tempfile


from os import path

import pytest
from dagster import AssetKey, AssetMaterialization, Output, execute_pipeline, pipeline, solid
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster.utils import file_relative_path
from sqlalchemy import create_engine


def test_init_with_logger(hostname, conn_string):
    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')
        print(log_file_path)
        print(os.getcwd())

        instance = DagsterInstance.from_config(tempdir)

        @solid
        def noop_solid(_):
            instance.logger.error('hello logger')

        @pipeline
        def noop_pipeline():
            noop_solid()

        result = execute_pipeline(noop_pipeline, instance=instance)

    assert False
