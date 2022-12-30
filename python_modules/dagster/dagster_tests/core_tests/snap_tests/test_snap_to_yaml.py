from dagster import Field, op, job, asset
from dagster._config.field import resolve_to_config_type
from dagster._config.snap import snap_from_config_type
from dagster._core.host_representation.represented import RepresentedPipeline
from dagster._core.snap.snap_to_yaml import default_values_yaml_from_type_snap


def test_basic_default():
    snap = snap_from_config_type(resolve_to_config_type({"a": Field(str, "foo")}))
    yaml_str = default_values_yaml_from_type_snap(snap)
    assert yaml_str == "a: foo\n"


# def test_op_job():
#     @op
#     def an_op():
#         pass

#     @job
#     def a_job():
#         an_op()

#     RepresentedPipeline
