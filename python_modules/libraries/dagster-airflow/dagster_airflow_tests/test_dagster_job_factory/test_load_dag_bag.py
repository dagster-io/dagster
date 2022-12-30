import os
import tempfile

import pytest
from airflow import __version__ as airflow_version
from dagster_airflow import make_dagster_definitions_from_airflow_dags_path

from ..airflow_utils import test_make_from_dagbag_inputs


@pytest.mark.skipif(airflow_version >= "2.0.0", reason="requires airflow 1")
@pytest.mark.parametrize(
    "path_and_content_tuples, fn_arg_path, expected_job_names",
    test_make_from_dagbag_inputs,
)
def test_make_definition(
    path_and_content_tuples,
    fn_arg_path,
    expected_job_names,
):
    with tempfile.TemporaryDirectory() as tmpdir_path:
        for (path, content) in path_and_content_tuples:
            with open(os.path.join(tmpdir_path, path), "wb") as f:
                f.write(bytes(content.encode("utf-8")))

        definition = (
            make_dagster_definitions_from_airflow_dags_path(
                tmpdir_path
            )
            if fn_arg_path is None
            else make_dagster_definitions_from_airflow_dags_path(
                os.path.join(tmpdir_path, fn_arg_path)
            )
        )

        repo = definition.get_repository_def()

        for job_name in expected_job_names:
            assert repo.has_job(job_name)

            job = definition.get_job_def(job_name)
            result = job.execute_in_process()
            assert result.success
            for event in result.all_events:
                assert event.event_type_value != "STEP_FAILURE"

        assert set(repo.job_names) == set(expected_job_names)