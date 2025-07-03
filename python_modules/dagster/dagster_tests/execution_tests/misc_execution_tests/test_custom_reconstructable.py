import os
import sys

import dagster as dg
import pytest
from dagster._core.definitions import ReconstructableJob


@dg.op
def top_scope_op(_context):
    pass


class JobFactory:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def make_job(self, has_nested_scope_solid: bool, name: str) -> dg.JobDefinition:
        @dg.op
        def nested_scope_op(_context):
            pass

        @dg.job(name=self.prefix + name)
        def _job():
            if has_nested_scope_solid:
                nested_scope_op()
            top_scope_op()

        return _job


def reconstruct_job(factory_prefix: str, has_nested_scope_op: bool, name: str) -> dg.JobDefinition:
    factory = JobFactory(factory_prefix)
    return factory.make_job(has_nested_scope_op, name=name)


def test_build_reconstructable_job():
    sys_path = sys.path
    try:
        factory = JobFactory("foo_")
        bar_job = factory.make_job(True, name="bar")

        with pytest.raises(dg.DagsterInvariantViolationError):
            dg.reconstructable(bar_job)

        reconstructable_bar_job = dg.build_reconstructable_job(
            "test_custom_reconstructable",
            "reconstruct_job",
            ("foo_",),
            {"has_nested_scope_op": True, "name": "bar"},
            reconstructor_working_directory=os.path.dirname(os.path.realpath(__file__)),
        )

        reconstructed_bar_job_def = reconstructable_bar_job.get_definition()

        assert reconstructed_bar_job_def.name == "foo_bar"
        assert len(reconstructed_bar_job_def.nodes) == 2
        assert reconstructed_bar_job_def.get_node_named("top_scope_op")
        assert reconstructed_bar_job_def.get_node_named("nested_scope_op")

    finally:
        sys.path = sys_path


def test_build_reconstructable_job_serdes():
    sys_path = sys.path
    try:
        factory = JobFactory("foo_")
        bar_job = factory.make_job(True, name="bar")

        with pytest.raises(dg.DagsterInvariantViolationError):
            dg.reconstructable(bar_job)

        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

        reconstructable_bar_job = dg.build_reconstructable_job(
            "test_custom_reconstructable",
            "reconstruct_job",
            ("foo_",),
            {"has_nested_scope_op": True, "name": "bar"},
        )

        reconstructable_bar_job_dict = reconstructable_bar_job.to_dict()

        reconstructed_bar_job = ReconstructableJob.from_dict(reconstructable_bar_job_dict)

        reconstructed_bar_job_def = reconstructed_bar_job.get_definition()

        assert reconstructed_bar_job_def.name == "foo_bar"
        assert len(reconstructed_bar_job_def.nodes) == 2
        assert reconstructed_bar_job_def.get_node_named("top_scope_op")
        assert reconstructed_bar_job_def.get_node_named("nested_scope_op")

    finally:
        sys.path = sys_path
