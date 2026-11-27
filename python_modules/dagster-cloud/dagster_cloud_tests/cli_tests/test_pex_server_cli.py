from unittest.mock import MagicMock, patch

import pytest
from dagster._core.code_pointer import FileCodePointer
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin
from dagster._core.utils import make_new_run_id
from dagster._grpc.types import ExecuteRunArgs, ResumeRunArgs
from dagster_cloud.pex.grpc.server.cli import RunApiCommand, execute_run
from dagster_cloud.pex.grpc.server.registry import PexExecutable
from dagster_cloud_cli.core.workspace import PexMetadata
from dagster_shared.serdes.serdes import serialize_value

JOB_ORIGIN = JobPythonOrigin(
    job_name="test",
    repository_origin=RepositoryPythonOrigin(
        executable_path="/usr/bin/python",
        code_pointer=FileCodePointer(python_file="foo.py", fn_name="foo"),
    ),
)


@pytest.mark.parametrize(
    "args_cls,expected_api_command",
    [
        (ExecuteRunArgs, RunApiCommand.EXECUTE_RUN),
        (ResumeRunArgs, RunApiCommand.RESUME_RUN),
    ],
)
def test_execute_run_dispatches_on_args_type(args_cls, expected_api_command, tmp_path):
    run_id = make_new_run_id()
    input_json = serialize_value(args_cls(job_origin=JOB_ORIGIN, run_id=run_id, instance_ref=None))
    pex_metadata_json = serialize_value(PexMetadata(pex_tag="deps-abc.pex:source-def.pex"))

    executable = PexExecutable(
        source_path="/tmp/pex-files/source-def.pex",
        all_paths=[],
        environ={},
        working_directory=None,
        venv_dirs=[],
    )

    with (
        patch(
            "dagster_cloud.pex.grpc.server.cli.PexS3Registry.get_pex_executable",
            return_value=executable,
        ),
        patch("dagster_cloud.pex.grpc.server.cli.subprocess.Popen") as mock_popen,
    ):
        mock_popen.return_value = MagicMock(wait=MagicMock(return_value=0))
        execute_run(input_json, pex_metadata_json, local_pex_files_dir=str(tmp_path))

    command = mock_popen.call_args[0][0]
    assert command == [
        executable.source_path,
        "-m",
        "dagster",
        "api",
        expected_api_command.value,
        input_json,
    ]
