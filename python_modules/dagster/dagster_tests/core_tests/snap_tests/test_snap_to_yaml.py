import os
import sys

from dagster import Field, job, op
from dagster._config.field import resolve_to_config_type
from dagster._config.snap import snap_from_config_type
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.host_representation import InProcessCodeLocationOrigin
from dagster._core.host_representation.external import ExternalJob
from dagster._core.snap.snap_to_yaml import default_values_yaml_from_type_snap
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin


def test_basic_default():
    snap = snap_from_config_type(resolve_to_config_type({"a": Field(str, "foo")}))
    yaml_str = default_values_yaml_from_type_snap(snap)
    assert yaml_str == "a: foo\n"


def test_with_spaces():
    snap = snap_from_config_type(resolve_to_config_type({"a": Field(str, "with spaces")}))
    yaml_str = default_values_yaml_from_type_snap(snap)
    assert yaml_str == "a: with spaces\n"


def external_repository_for_function(fn):
    return external_repository_for_module(fn.__module__, fn.__name__)


def external_repository_for_module(module_name, attribute=None, repository_name="__repository__"):
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name=module_name,
        working_directory=os.getcwd(),
        attribute=attribute,
    )

    location = InProcessCodeLocationOrigin(
        loadable_target_origin=loadable_target_origin, location_name=module_name
    ).create_location()

    return location.get_repository(repository_name)


def trivial_job_defs():
    @op
    def an_op():
        pass

    @job
    def a_job():
        an_op()

    return Definitions(jobs=[a_job])


def test_print_root() -> None:
    external_repository = external_repository_for_function(trivial_job_defs)
    external_a_job: ExternalJob = external_repository.get_full_external_job("a_job")
    root_config_key = external_a_job.root_config_key
    assert root_config_key
    root_type = external_a_job.config_schema_snapshot.get_config_snap(root_config_key)
    assert (
        default_values_yaml_from_type_snap(root_type)
        == """execution:
  config:
    multiprocess:
      max_concurrent: 0
      retries:
        enabled: {}
loggers: {}
ops:
  an_op: {}
resources:
  io_manager: {}
"""
    )
