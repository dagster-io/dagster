import os
from unittest.mock import ANY, MagicMock, patch

import pytest
import wandb
from callee import EndsWith
from dagster import (
    DagsterRunMetadataValue,
    IntMetadataValue,
    TextMetadataValue,
    UrlMetadataValue,
    build_init_resource_context,
    build_input_context,
    build_output_context,
)
from dagster_wandb import WandbArtifactsIOManagerError, wandb_artifacts_io_manager, wandb_resource
from wandb.sdk.wandb_artifacts import Artifact

DAGSTER_RUN_ID = "unit-testing"
DAGSTER_RUN_ID_SHORT = DAGSTER_RUN_ID[0:8]
DAGSTER_HOME = "/path/to/dagster_home"
WANDB_PROJECT = "project"
WANDB_ENTITY = "entity"
WANDB_RUN_NAME = "wandb_run_name"
WANDB_RUN_ID = "wandb_run_id"
WANDB_RUN_PATH = f"{WANDB_ENTITY}/{WANDB_PROJECT}/{WANDB_RUN_ID}"
WANDB_RUN_URL = f"https://wandb.ai/{WANDB_RUN_PATH}"
ARTIFACT_ID = "artifact_id"
ARTIFACT_NAME = "artifact_name"
ARTIFACT_TYPE = "dataset"
ARTIFACT_VERSION = "v1"
ARTIFACT_SIZE = 42
ARTIFACT_URL = f"https://wandb.ai/{WANDB_ENTITY}/{WANDB_PROJECT}/artifacts/{ARTIFACT_TYPE}/{ARTIFACT_ID}/{ARTIFACT_VERSION}"
ARTIFACT_DESCRIPTION = "Artifact description"
EXTRA_ALIAS = "extra_alias"
DIRS = [
    {
        "name": "dirname",
        "local_path": "path/to/dir",
    },
    {
        "local_path": "path/to/dir",
    },
]
FILES = [
    {
        "name": "filename",
        "local_path": "path/to/file.py",
    },
    {
        "is_tmp": True,
        "local_path": "path/to/file",
    },
]
REFERENCES = [
    {
        "uri": "https://picsum.photos/200/300",
        "name": "Lorem ipsum photo",
    }
]
ASSET_NAME = "asset_name"
LOCAL_ARTIFACT_PATH = (
    f"/storage/wandb_artifacts_manager/artifacts/{ARTIFACT_NAME}:{ARTIFACT_VERSION}"
)

wandb_resource_configured = wandb_resource.configured(
    {
        "api_key": "WANDB_API_KEY",
    }
)


@pytest.fixture(autouse=True)
def environ_mock():
    with patch.dict(os.environ, {"DAGSTER_HOME": DAGSTER_HOME}) as mock:
        yield mock


@pytest.fixture(autouse=True)
def makedirs_mock():
    with patch("os.makedirs") as mock:
        yield mock


@pytest.fixture(autouse=True)
def walk_mock():
    with patch("os.walk") as mock:
        yield mock


@pytest.fixture(autouse=True)
def lstat_mock():
    with patch("os.lstat") as mock:
        yield mock


@pytest.fixture(autouse=True)
def remove_mock():
    with patch("os.remove") as mock:
        yield mock


@pytest.fixture(autouse=True)
def listdir_mock():
    with patch("os.listdir") as mock:
        yield mock


@pytest.fixture(autouse=True)
def rmtree_mock():
    with patch("shutil.rmtree") as mock:
        yield mock


@pytest.fixture
def pickle_dump_mock():
    with patch("pickle.dump") as mock:
        yield mock


@pytest.fixture
def dill_dump_mock():
    with patch("dill.dump") as mock:
        yield mock


@pytest.fixture
def cloudpickle_dump_mock():
    with patch("cloudpickle.dump") as mock:
        yield mock


@pytest.fixture
def joblib_dump_mock():
    with patch("joblib.dump") as mock:
        yield mock


@pytest.fixture
def log_artifact_mock():
    with patch("wandb.log_artifact") as mock:
        yield mock


@pytest.fixture
def artifact_mock():
    with patch(
        "wandb.Artifact",
        autospec=True,
        return_value=MagicMock(
            id=ARTIFACT_ID,
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            version=ARTIFACT_VERSION,
            size=ARTIFACT_SIZE,
        ),
    ) as mock:
        yield mock


@pytest.fixture
def run_mock():
    with patch(
        "wandb.run",
    ) as mock:
        yield mock


@pytest.fixture
def login_mock():
    with patch(
        "wandb.login",
    ) as mock:
        yield mock


@pytest.fixture
def init_mock():
    with patch(
        "wandb.init",
    ) as mock:
        yield mock


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_serialization_module": "pickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")

        assert pickle_dump_mock.call_count == 1
        pickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output_and_dill_serialization_module(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, dill_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
                "serialization_module": {"name": "dill"},
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_dill_version_used": ANY,
            "source_serialization_module": "dill",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.dill", "wb")

        assert dill_dump_mock.call_count == 1
        dill_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output_and_cloudpickle_serialization_module(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, cloudpickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
                "serialization_module": {"name": "cloudpickle"},
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_cloudpickle_version_used": ANY,
            "source_serialization_module": "cloudpickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.cloudpickle", "wb")

        assert cloudpickle_dump_mock.call_count == 1
        cloudpickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output_and_joblib_serialization_module(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, joblib_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
                "serialization_module": {"name": "joblib"},
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_joblib_version_used": ANY,
            "source_serialization_module": "joblib",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.joblib", "wb")

        assert joblib_dump_mock.call_count == 1
        joblib_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output_and_custom_config(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name="my_custom_run_name",
        id="my_custom_run_id",
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            config={
                "run_name": "my_custom_run_name",
                "run_id": "my_custom_run_id",
                "run_tags": ["my_first_tag", "my_second_tag"],
            },
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id="my_custom_run_id",
            name="my_custom_run_name",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["my_first_tag", "my_second_tag", "dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_serialization_module": "pickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")

        assert pickle_dump_mock.call_count == 1
        pickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text="my_custom_run_id"),
                "wandb_run_name": TextMetadataValue(text="my_custom_run_name"),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output_and_custom_host(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource.configured(
                    {"api_key": "WANDB_API_KEY", "host": "http://wandb.my-custom-host.com/"}
                ),
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="http://wandb.my-custom-host.com/",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_serialization_module": "pickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")

        assert pickle_dump_mock.call_count == 1
        pickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(
                    url=f"http://wandb.my-custom-host.com/{WANDB_ENTITY}/{WANDB_PROJECT}/artifacts/{ARTIFACT_TYPE}/{ARTIFACT_ID}/{ARTIFACT_VERSION}"
                ),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_partitioned_op_with_simple_output(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource.configured({"api_key": "WANDB_API_KEY"}),
            },
        )
    )

    PARTITION_KEY = "partition_key"

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        },
        partition_key=PARTITION_KEY,
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=f"{ARTIFACT_NAME}.{PARTITION_KEY}",
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_serialization_module": "pickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")

        assert pickle_dump_mock.call_count == 1
        pickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_raises_when_no_name_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context()

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        with pytest.raises(WandbArtifactsIOManagerError):
            manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0
        assert artifact_mock.return_value.wait.call_count == 0
        assert log_artifact_mock.call_count == 0
        assert context.add_output_metadata.call_count == 0
        assert add_output_metadata_spy.return_value.call_count == 0


def test_wandb_artifacts_io_manager_handle_output_for_op_raises_when_unsupported_serialization_module_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
                "serialization_module": {"name": "unsupported"},
            }
        },
    )
    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        with pytest.raises(WandbArtifactsIOManagerError):
            manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0
        assert artifact_mock.return_value.wait.call_count == 0
        assert log_artifact_mock.call_count == 0
        assert context.add_output_metadata.call_count == 0
        assert add_output_metadata_spy.return_value.call_count == 0


def test_wandb_artifacts_io_manager_handle_output_for_asset_with_simple_output(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        asset_key=ASSET_NAME,
        metadata={
            "wandb_artifact_configuration": {
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ASSET_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_serialization_module": "pickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")

        assert pickle_dump_mock.call_count == 1
        pickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_asset_raise_when_double_name_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        asset_key=ASSET_NAME,
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        with pytest.raises(WandbArtifactsIOManagerError):
            manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0
        assert artifact_mock.return_value.wait.call_count == 0
        assert log_artifact_mock.call_count == 0
        assert context.add_output_metadata.call_count == 0
        assert add_output_metadata_spy.return_value.call_count == 0


def test_wandb_artifacts_io_manager_handle_output_for_op_with_simple_output_all_parameters(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
                "description": ARTIFACT_DESCRIPTION,
                "aliases": [EXTRA_ALIAS],
                "add_dirs": DIRS,
                "add_files": FILES,
                "add_references": REFERENCES,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = [1, 2, 3]
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=ARTIFACT_DESCRIPTION,
        )
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 2
        assert artifact_mock.return_value.add_dir.call_count == 2
        assert artifact_mock.return_value.add_reference.call_count == 1

        assert artifact_mock.return_value.metadata == {
            "source_pickle_protocol_used": ANY,
            "source_serialization_module": "pickle",
        }
        assert artifact_mock.return_value.new_file.call_count == 1
        artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")

        assert pickle_dump_mock.call_count == 1
        pickle_dump_mock.assert_called_with(
            output_value,
            artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
            protocol=ANY,
        )

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[EXTRA_ALIAS, f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_object_output(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = wandb.Table(columns=["a", "b", "c"], data=[[1, 2, 3]])
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 1
        artifact_mock.return_value.add.assert_called_with(
            output_value, output_value.__class__.__name__
        )

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_object_output_all_parameters(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "type": ARTIFACT_TYPE,
                "aliases": [EXTRA_ALIAS],
                "add_dirs": DIRS,
                "add_files": FILES,
                "add_references": REFERENCES,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        output_value = wandb.Table(columns=["a", "b", "c"], data=[[1, 2, 3]])
        manager.handle_output(context, output_value)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 1
        artifact_mock.assert_called_with(
            metadata={
                "source_created_at": ANY,
                "source_dagster_run_id": DAGSTER_RUN_ID,
                "source_integration": "dagster_wandb",
                "source_integration_version": ANY,
                "source_python_version": ANY,
            },
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            description=None,
        )
        assert artifact_mock.return_value.add.call_count == 1
        artifact_mock.return_value.add.assert_called_with(
            output_value, output_value.__class__.__name__
        )

        assert artifact_mock.return_value.add_file.call_count == 2
        assert artifact_mock.return_value.add_dir.call_count == 2
        assert artifact_mock.return_value.add_reference.call_count == 1

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact_mock.return_value.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact_mock.return_value,
            aliases=[EXTRA_ALIAS, f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_artifact_output(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context()

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        artifact = MagicMock(
            spec=Artifact,
            id=ARTIFACT_ID,
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            version=ARTIFACT_VERSION,
            size=ARTIFACT_SIZE,
        )
        manager.handle_output(context, artifact)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact,
            aliases=[f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_artifact_output_raise_when_name_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        artifact = MagicMock(
            spec=Artifact,
            id=ARTIFACT_ID,
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            version=ARTIFACT_VERSION,
            size=ARTIFACT_SIZE,
        )
        with pytest.raises(WandbArtifactsIOManagerError):
            manager.handle_output(context, artifact)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact.wait.call_count == 0

        assert artifact.wait.call_count == 0

        assert log_artifact_mock.call_count == 0

        assert context.add_output_metadata.call_count == 0
        assert add_output_metadata_spy.return_value.call_count == 0


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_artifact_output_raise_when_type_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "type": ARTIFACT_TYPE,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        artifact = MagicMock(
            spec=Artifact,
            id=ARTIFACT_ID,
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            version=ARTIFACT_VERSION,
            size=ARTIFACT_SIZE,
        )
        with pytest.raises(WandbArtifactsIOManagerError):
            manager.handle_output(context, artifact)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact.wait.call_count == 0

        assert artifact.wait.call_count == 0

        assert log_artifact_mock.call_count == 0

        assert context.add_output_metadata.call_count == 0
        assert add_output_metadata_spy.return_value.call_count == 0


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_artifact_output_raise_when_double_description_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "description": ARTIFACT_DESCRIPTION,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        artifact = MagicMock(
            spec=Artifact,
            id=ARTIFACT_ID,
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            version=ARTIFACT_VERSION,
            size=ARTIFACT_SIZE,
            description=ARTIFACT_DESCRIPTION,
        )
        with pytest.raises(WandbArtifactsIOManagerError):
            manager.handle_output(context, artifact)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.return_value.add_file.call_count == 0
        assert artifact_mock.return_value.add_dir.call_count == 0
        assert artifact_mock.return_value.add_reference.call_count == 0

        assert artifact_mock.return_value.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact.wait.call_count == 0

        assert artifact.wait.call_count == 0

        assert log_artifact_mock.call_count == 0

        assert context.add_output_metadata.call_count == 0
        assert add_output_metadata_spy.return_value.call_count == 0


def test_wandb_artifacts_io_manager_handle_output_for_op_with_wandb_artifact_output_and_all_parameters(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )
    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_output_context(
        metadata={
            "wandb_artifact_configuration": {
                "aliases": [EXTRA_ALIAS],
                "add_dirs": DIRS,
                "add_files": FILES,
                "add_references": REFERENCES,
            }
        },
    )

    with patch.object(context, "add_output_metadata") as add_output_metadata_spy:
        artifact = MagicMock(
            spec=Artifact,
            id=ARTIFACT_ID,
            name=ARTIFACT_NAME,
            type=ARTIFACT_TYPE,
            version=ARTIFACT_VERSION,
            size=ARTIFACT_SIZE,
        )
        manager.handle_output(context, artifact)

        assert init_mock.call_count == 1
        init_mock.assert_called_with(
            anonymous="never",
            dir=EndsWith(f"/storage/wandb_artifacts_manager/runs/{DAGSTER_RUN_ID}"),
            entity=WANDB_ENTITY,
            id=DAGSTER_RUN_ID,
            name=f"dagster-run-{DAGSTER_RUN_ID_SHORT}",
            project=WANDB_PROJECT,
            resume="allow",
            tags=["dagster_wandb"],
        )

        assert login_mock.call_count == 1
        login_mock.assert_called_with(
            anonymous="never",
            host="https://api.wandb.ai",
            key="WANDB_API_KEY",
        )

        assert artifact_mock.call_count == 0
        assert artifact_mock.return_value.add.call_count == 0

        assert artifact_mock.add_file.call_count == 0
        assert artifact_mock.add_dir.call_count == 0
        assert artifact_mock.add_reference.call_count == 0

        assert artifact.add_file.call_count == 2
        assert artifact.add_dir.call_count == 2
        assert artifact.add_reference.call_count == 1

        assert artifact_mock.return_value.new_file.call_count == 0

        assert artifact.new_file.call_count == 0

        assert pickle_dump_mock.call_count == 0

        assert artifact.wait.call_count == 1

        log_artifact_mock.assert_called_with(
            artifact,
            aliases=[EXTRA_ALIAS, f"dagster-run-{DAGSTER_RUN_ID_SHORT}", "latest"],
        )

        assert context.add_output_metadata.call_count == 1
        add_output_metadata_spy.assert_called_with(
            {
                "dagster_run_id": DagsterRunMetadataValue(run_id=DAGSTER_RUN_ID),
                "wandb_artifact_id": TextMetadataValue(text=ARTIFACT_ID),
                "wandb_artifact_size": IntMetadataValue(value=ARTIFACT_SIZE),
                "wandb_artifact_type": TextMetadataValue(text=ARTIFACT_TYPE),
                "wandb_artifact_url": UrlMetadataValue(url=ARTIFACT_URL),
                "wandb_artifact_version": TextMetadataValue(text=ARTIFACT_VERSION),
                "wandb_entity": TextMetadataValue(text=WANDB_ENTITY),
                "wandb_project": TextMetadataValue(text=WANDB_PROJECT),
                "wandb_run_id": TextMetadataValue(text=WANDB_RUN_ID),
                "wandb_run_name": TextMetadataValue(text=WANDB_RUN_NAME),
                "wandb_run_path": TextMetadataValue(text=WANDB_RUN_PATH),
                "wandb_run_url": UrlMetadataValue(url=WANDB_RUN_URL),
            },
        )


def test_wandb_artifacts_io_manager_load_input_raise_when_no_name_is_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_input_context()

    with pytest.raises(WandbArtifactsIOManagerError):
        assert manager.load_input(context) is None


def test_wandb_artifacts_io_manager_load_input(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
        use_artifact=MagicMock(
            return_value=MagicMock(
                spec=Artifact,
                id=ARTIFACT_ID,
                name=ARTIFACT_NAME,
                type=ARTIFACT_TYPE,
                version=ARTIFACT_VERSION,
                size=ARTIFACT_SIZE,
                description=ARTIFACT_DESCRIPTION,
            ),
        ),
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_input_context(
        metadata={"wandb_artifact_configuration": {"name": ARTIFACT_NAME}},
    )

    assert manager.load_input(context) == run_mock.use_artifact.return_value

    run_mock.use_artifact.assert_called_with(
        f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}:latest"
    )

    assert run_mock.use_artifact.return_value.get.call_count == 0
    assert run_mock.use_artifact.return_value.get_path.call_count == 0

    run_mock.use_artifact.return_value.download.assert_called_with(
        recursive=True, root=EndsWith(LOCAL_ARTIFACT_PATH)
    )

    run_mock.use_artifact.return_value.verify.assert_called_with(root=EndsWith(LOCAL_ARTIFACT_PATH))


def test_wandb_artifacts_io_manager_load_input_get(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
        use_artifact=MagicMock(
            return_value=MagicMock(
                spec=Artifact,
                id=ARTIFACT_ID,
                name=ARTIFACT_NAME,
                type=ARTIFACT_TYPE,
                version=ARTIFACT_VERSION,
                size=ARTIFACT_SIZE,
                description=ARTIFACT_DESCRIPTION,
            ),
        ),
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    object_named = "name"
    context = build_input_context(
        metadata={"wandb_artifact_configuration": {"name": ARTIFACT_NAME, "get": object_named}}
    )

    assert manager.load_input(context) == run_mock.use_artifact.return_value.get.return_value

    run_mock.use_artifact.assert_called_with(
        f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}:latest"
    )

    run_mock.use_artifact.return_value.get.assert_called_with(object_named)
    assert run_mock.use_artifact.return_value.get_path.call_count == 0
    assert run_mock.use_artifact.return_value.download.call_count == 0
    assert run_mock.use_artifact.return_value.verify.call_count == 0


def test_wandb_artifacts_io_manager_load_input_get_path(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
        use_artifact=MagicMock(
            return_value=MagicMock(
                spec=Artifact,
                id=ARTIFACT_ID,
                name=ARTIFACT_NAME,
                type=ARTIFACT_TYPE,
                version=ARTIFACT_VERSION,
                size=ARTIFACT_SIZE,
                description=ARTIFACT_DESCRIPTION,
            ),
        ),
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    path = "path/to/files"
    context = build_input_context(
        metadata={"wandb_artifact_configuration": {"name": ARTIFACT_NAME, "get_path": path}}
    )

    assert (
        manager.load_input(context)
        == run_mock.use_artifact.return_value.get_path.return_value.download.return_value
    )

    run_mock.use_artifact.assert_called_with(
        f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}:latest"
    )

    assert run_mock.use_artifact.return_value.get.call_count == 0
    run_mock.use_artifact.return_value.get_path.assert_called_with(path)
    assert run_mock.use_artifact.return_value.download.call_count == 0
    assert run_mock.use_artifact.return_value.verify.call_count == 0


def test_wandb_artifacts_io_manager_load_input_raise_when_version_and_alias_are_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_input_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "version": ARTIFACT_VERSION,
                "alias": "latest",
            }
        }
    )

    with pytest.raises(WandbArtifactsIOManagerError):
        assert manager.load_input(context) is None


def test_wandb_artifacts_io_manager_load_input_raise_when_get_and_get_path_are_provided(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_input_context(
        metadata={
            "wandb_artifact_configuration": {
                "name": ARTIFACT_NAME,
                "get": "file",
                "get_path": "path",
            }
        }
    )

    with pytest.raises(WandbArtifactsIOManagerError):
        assert manager.load_input(context) is None


def test_wandb_artifacts_io_manager_load_input_with_specific_version(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
        use_artifact=MagicMock(
            return_value=MagicMock(
                spec=Artifact,
                id=ARTIFACT_ID,
                name=ARTIFACT_NAME,
                type=ARTIFACT_TYPE,
                version=ARTIFACT_VERSION,
                size=ARTIFACT_SIZE,
                description=ARTIFACT_DESCRIPTION,
            ),
        ),
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_input_context(
        metadata={
            "wandb_artifact_configuration": {"name": ARTIFACT_NAME, "version": ARTIFACT_VERSION}
        }
    )

    assert manager.load_input(context) == run_mock.use_artifact.return_value

    run_mock.use_artifact.assert_called_with(
        f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}:{ARTIFACT_VERSION}"
    )

    assert run_mock.use_artifact.return_value.get.call_count == 0
    assert run_mock.use_artifact.return_value.get_path.call_count == 0

    run_mock.use_artifact.return_value.download.assert_called_with(
        recursive=True, root=EndsWith(LOCAL_ARTIFACT_PATH)
    )

    run_mock.use_artifact.return_value.verify.assert_called_with(root=EndsWith(LOCAL_ARTIFACT_PATH))


def test_wandb_artifacts_io_manager_load_input_with_specific_alias(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
        use_artifact=MagicMock(
            return_value=MagicMock(
                spec=Artifact,
                id=ARTIFACT_ID,
                name=ARTIFACT_NAME,
                type=ARTIFACT_TYPE,
                version=ARTIFACT_VERSION,
                size=ARTIFACT_SIZE,
                description=ARTIFACT_DESCRIPTION,
            ),
        ),
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    context = build_input_context(
        metadata={"wandb_artifact_configuration": {"name": ARTIFACT_NAME, "alias": EXTRA_ALIAS}}
    )

    assert manager.load_input(context) == run_mock.use_artifact.return_value

    run_mock.use_artifact.assert_called_with(
        f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}:{EXTRA_ALIAS}"
    )

    assert run_mock.use_artifact.return_value.get.call_count == 0
    assert run_mock.use_artifact.return_value.get_path.call_count == 0

    run_mock.use_artifact.return_value.download.assert_called_with(
        recursive=True, root=EndsWith(LOCAL_ARTIFACT_PATH)
    )

    run_mock.use_artifact.return_value.verify.assert_called_with(root=EndsWith(LOCAL_ARTIFACT_PATH))


def test_wandb_artifacts_io_manager_load_partitioned_input(
    init_mock, login_mock, run_mock, artifact_mock, log_artifact_mock, pickle_dump_mock
):
    run_mock.configure_mock(
        name=WANDB_RUN_NAME,
        id=WANDB_RUN_ID,
        entity=WANDB_ENTITY,
        project=WANDB_PROJECT,
        path=WANDB_RUN_PATH,
        url=WANDB_RUN_URL,
        use_artifact=MagicMock(
            return_value=MagicMock(
                spec=Artifact,
                id=ARTIFACT_ID,
                name=ARTIFACT_NAME,
                type=ARTIFACT_TYPE,
                version=ARTIFACT_VERSION,
                size=ARTIFACT_SIZE,
                description=ARTIFACT_DESCRIPTION,
            ),
        ),
    )

    manager = wandb_artifacts_io_manager(
        build_init_resource_context(
            resources={
                "wandb_config": {"entity": WANDB_ENTITY, "project": WANDB_PROJECT},
                "wandb_resource": wandb_resource_configured,
            },
        )
    )

    PARTITION_KEY = "partition_key"
    context = build_input_context(
        metadata={"wandb_artifact_configuration": {"name": ARTIFACT_NAME, "alias": EXTRA_ALIAS}},
        partition_key=PARTITION_KEY,
    )

    assert manager.load_input(context) == run_mock.use_artifact.return_value

    run_mock.use_artifact.assert_called_with(
        f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}.{PARTITION_KEY}:{EXTRA_ALIAS}"
    )

    assert run_mock.use_artifact.return_value.get.call_count == 0
    assert run_mock.use_artifact.return_value.get_path.call_count == 0

    LOCAL_PARTITIONED_ARTIFACT_PATH = f"/storage/wandb_artifacts_manager/artifacts/{ARTIFACT_NAME}.{PARTITION_KEY}:{ARTIFACT_VERSION}"
    run_mock.use_artifact.return_value.download.assert_called_with(
        recursive=True,
        root=EndsWith(LOCAL_PARTITIONED_ARTIFACT_PATH),
    )

    run_mock.use_artifact.return_value.verify.assert_called_with(
        root=EndsWith(LOCAL_PARTITIONED_ARTIFACT_PATH)
    )
