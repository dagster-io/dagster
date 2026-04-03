import os
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

import dagster as dg
import pydantic
import pytest
from dagster import DagsterInstance
from dagster._config.field import resolve_to_config_type
from dagster._config.snap import ConfigSchemaSnapshot, snap_from_config_type
from dagster._core.remote_origin import InProcessCodeLocationOrigin
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.snap.snap_to_yaml import default_values_yaml_from_type_snap
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from pydantic import Field as PyField

if TYPE_CHECKING:
    from dagster._core.remote_representation.external import RemoteJob


@pytest.fixture
def instance():
    with dg.instance_for_test() as the_instance:
        yield the_instance


def test_basic_default():
    snap = snap_from_config_type(resolve_to_config_type({"a": dg.Field(str, "foo")}))
    yaml_str = default_values_yaml_from_type_snap(
        ConfigSchemaSnapshot(all_config_snaps_by_key={}), snap
    )
    assert yaml_str == "a: foo\n"


def test_basic_no_nested_fields():
    snap = snap_from_config_type(resolve_to_config_type(str))
    yaml_str = default_values_yaml_from_type_snap(
        ConfigSchemaSnapshot(all_config_snaps_by_key={}), snap
    )
    assert yaml_str == "{}\n"


def test_with_spaces():
    snap = snap_from_config_type(resolve_to_config_type({"a": dg.Field(str, "with spaces")}))
    yaml_str = default_values_yaml_from_type_snap(
        ConfigSchemaSnapshot(all_config_snaps_by_key={}), snap
    )
    assert yaml_str == "a: with spaces\n"


def _remote_repository_for_function(
    instance: DagsterInstance, fn: Callable[..., Any]
) -> RemoteRepository:
    return _remote_repository_for_module(instance, fn.__module__, fn.__name__)


def _remote_repository_for_module(
    instance: DagsterInstance,
    module_name: str,
    attribute: str | None = None,
    repository_name="__repository__",
) -> RemoteRepository:
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name=module_name,
        working_directory=os.getcwd(),
        attribute=attribute,
    )

    location = InProcessCodeLocationOrigin(
        loadable_target_origin=loadable_target_origin, location_name=module_name
    ).create_location(instance)

    return location.get_repository(repository_name)


def trivial_job_defs():
    @dg.op
    def an_op():
        pass

    @dg.job
    def a_job():
        an_op()

    return dg.Definitions(jobs=[a_job])


def test_print_root(
    instance,
) -> None:
    repo = _remote_repository_for_function(instance, trivial_job_defs)
    external_a_job: RemoteJob = repo.get_full_job("a_job")
    root_config_key = external_a_job.root_config_key
    assert root_config_key
    root_type = external_a_job.config_schema_snapshot.get_config_snap(root_config_key)
    assert (
        default_values_yaml_from_type_snap(external_a_job.config_schema_snapshot, root_type)
        == "{}\n"
    )


def job_def_with_config():
    class MyOpConfig(dg.Config):
        a_str_with_default: str = "foo"
        optional_int: int | None = None
        a_str_no_default: str

    @dg.op
    def an_op(config: MyOpConfig):
        pass

    @dg.job
    def a_job():
        an_op()

    return dg.Definitions(jobs=[a_job])


def test_print_root_op_config(
    instance,
) -> None:
    repo = _remote_repository_for_function(instance, job_def_with_config)
    external_a_job: RemoteJob = repo.get_full_job("a_job")
    root_config_key = external_a_job.root_config_key
    assert root_config_key
    root_type = external_a_job.config_schema_snapshot.get_config_snap(root_config_key)
    assert (
        default_values_yaml_from_type_snap(external_a_job.config_schema_snapshot, root_type)
        == """ops:
  an_op:
    config:
      a_str_with_default: foo
"""
    )


def job_def_with_complex_config():
    class MyNestedConfig(dg.Config):
        a_default_int: int = 1

    class MyOpConfig(dg.Config):
        nested: MyNestedConfig
        my_list: list[dict[str, int]] = [{"foo": 1, "bar": 2}]

    @dg.op
    def an_op(config: MyOpConfig):
        pass

    @dg.job
    def a_job():
        an_op()

    return dg.Definitions(jobs=[a_job])


def test_print_root_complex_op_config(instance) -> None:
    repo = _remote_repository_for_function(instance, job_def_with_complex_config)
    a_job = repo.get_full_job("a_job")
    root_config_key = a_job.root_config_key
    assert root_config_key
    root_type = a_job.config_schema_snapshot.get_config_snap(root_config_key)
    assert (
        default_values_yaml_from_type_snap(a_job.config_schema_snapshot, root_type)
        == """ops:
  an_op:
    config:
      my_list:
      - bar: 2
        foo: 1
      nested:
        a_default_int: 1
"""
    )


def job_def_with_secret_config():
    """Test that secret fields are masked in YAML output."""

    class MyOpConfig(dg.Config):
        username: str = PyField(default="admin", description="the username")
        password: str = PyField(
            default="secret123",
            description="the password",
            json_schema_extra={"dagster__is_secret": True},
        )
        api_key: str = PyField(
            default="key_456",
            description="the api key",
            json_schema_extra={"dagster__is_secret": True},
        )

    @dg.op
    def an_op(config: MyOpConfig):
        pass

    @dg.job
    def a_job():
        an_op()

    return dg.Definitions(jobs=[a_job])


def test_print_root_with_secret_fields(instance) -> None:
    """Test that secret fields are masked with ******** in YAML output."""
    repo = _remote_repository_for_function(instance, job_def_with_secret_config)
    a_job = repo.get_full_job("a_job")
    root_config_key = a_job.root_config_key
    assert root_config_key
    root_type = a_job.config_schema_snapshot.get_config_snap(root_config_key)
    yaml_output = default_values_yaml_from_type_snap(a_job.config_schema_snapshot, root_type)

    # Verify that secret fields are masked
    assert "password: '********'" in yaml_output
    assert "api_key: '********'" in yaml_output
    # Verify that non-secret field is not masked
    assert "username: admin" in yaml_output
    # Verify that actual secret values are not in the output
    assert "secret123" not in yaml_output
    assert "key_456" not in yaml_output


class AuthToken(dg.Config):
    auth_type: Literal["token"] = "token"
    token: str


class AuthDefault(dg.Config):
    auth_type: Literal["default"] = "default"
    extra: dict[str, Any] = {}


class MyConnectionResource(dg.ConfigurableResource):
    host: str
    auth: AuthToken | AuthDefault = pydantic.Field(discriminator="auth_type")


def job_def_with_discriminated_union_resource():
    @dg.asset
    def my_asset(conn: MyConnectionResource):
        pass

    return dg.Definitions(
        assets=[my_asset],
        resources={
            "conn": MyConnectionResource(
                host="localhost",
                auth=AuthDefault(extra={}),
            )
        },
    )


def test_discriminated_union_empty_dict_default_preserved(instance) -> None:
    """Empty dict defaults inside discriminated unions must survive the
    empty-dict filtering pass. Without type-aware filtering, _filter_empty_dicts
    would recursively collapse: extra: {} -> removed -> default: {} -> removed
    -> auth: {} -> removed, causing Launchpad to report missing required config.
    """
    repo = _remote_repository_for_function(instance, job_def_with_discriminated_union_resource)
    remote_job = repo.get_full_job("__ASSET_JOB")
    root_config_key = remote_job.root_config_key
    assert root_config_key
    root_type = remote_job.config_schema_snapshot.get_config_snap(root_config_key)
    yaml_output = default_values_yaml_from_type_snap(remote_job.config_schema_snapshot, root_type)

    # Discriminated unions use the discriminator value as a selector key,
    # so it appears as "default:" not "auth_type: ..."
    assert "auth:" in yaml_output
    assert "default:" in yaml_output
    assert "extra: {}" in yaml_output
