import os
import sys
import tempfile
from io import BytesIO

import yaml
from dagster import execute_pipeline
from dagster.cli.pipeline import execute_list_versions_command
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import ConsolidatedSqliteEventLogStorage
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage
from dagster.utils import file_relative_path

from ...core_tests.execution_tests.memoized_dev_loop_pipeline import asset_pipeline


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout  # pylint: disable=W0201
        self._stringio = BytesIO()  # pylint: disable=W0201
        sys.stdout = self._stringio
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def test_execute_display_command():
    with tempfile.TemporaryDirectory() as temp_dir:
        run_store = SqliteRunStorage.from_local(temp_dir)
        event_store = ConsolidatedSqliteEventLogStorage(temp_dir)
        compute_log_manager = LocalComputeLogManager(temp_dir)
        instance = DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=run_store,
            event_storage=event_store,
            compute_log_manager=compute_log_manager,
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=DefaultRunLauncher(),
        )
        run_config = {
            "solids": {
                "create_string_1_asset": {"config": {"input_str": "apple"}},
                "take_string_1_asset": {"config": {"input_str": "apple"}},
            },
            "resources": {"io_manager": {"config": {"base_dir": temp_dir}}},
        }

        # write run config to temp file
        # file is temp because intermediate storage directory is temporary
        with open(os.path.join(temp_dir, "pipeline_config.yaml"), "w") as f:
            f.write(yaml.dump(run_config))

        kwargs = {
            "config": (os.path.join(temp_dir, "pipeline_config.yaml"),),
            "pipeline": "asset_pipeline",
            "python_file": file_relative_path(
                __file__, "../../core_tests/execution_tests/memoized_dev_loop_pipeline.py"
            ),
            "tags": '{"dagster/is_memoized_run": "true"}',
        }

        with Capturing() as output:
            execute_list_versions_command(kwargs=kwargs, instance=instance)

        assert output

        # execute the pipeline once so that addresses have been populated.

        result = execute_pipeline(
            asset_pipeline,
            run_config=run_config,
            mode="only_mode",
            tags={"dagster/is_memoized_run": "true"},
            instance=instance,
        )
        assert result.success

        with Capturing() as output:
            execute_list_versions_command(kwargs=kwargs, instance=instance)

        assert output
