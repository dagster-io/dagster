import os
import sys

import pytest

from dagster import custom_reconstructable, pipeline, reconstructable, solid
from dagster.core.errors import DagsterInvariantViolationError


@solid
def top_scope_solid(_context):
    pass


class PipelineFactory(object):
    def __init__(self, prefix=None):
        self.prefix = prefix

    def make_pipeline(self, has_nested_scope_solid, name=None):
        @solid
        def nested_scope_solid(_context):
            pass

        @pipeline(name=self.prefix + name)
        def _pipeline():
            if has_nested_scope_solid:
                nested_scope_solid()
            top_scope_solid()

        return _pipeline


def reconstruct_pipeline(factory_prefix, has_nested_scope_solid, name=None):
    factory = PipelineFactory(factory_prefix)
    return factory.make_pipeline(has_nested_scope_solid, name=name)


def test_custom_reconstructable_roundtrip():
    sys_path = sys.path
    try:
        factory = PipelineFactory("foo_")
        bar_pipeline = factory.make_pipeline(True, name="bar")

        with pytest.raises(
            DagsterInvariantViolationError,
            match=(
                "Use a function or decorated function defined at module scope instead, or use "
                "custom_reconstructable"
            ),
        ):
            reconstructable(bar_pipeline)

        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

        reconstructable_bar_pipeline = custom_reconstructable(
            bar_pipeline,
            "test_custom_reconstructable",
            "reconstruct_pipeline",
            ("foo_",),
            {"has_nested_scope_solid": True, "name": "bar"},
        )

        reconstructed_bar_pipeline_def = reconstructable_bar_pipeline.get_definition()

        assert reconstructed_bar_pipeline_def.name == "foo_bar"
        assert len(reconstructed_bar_pipeline_def.solids) == 2
        assert reconstructed_bar_pipeline_def.solid_named("top_scope_solid")
        assert reconstructed_bar_pipeline_def.solid_named("nested_scope_solid")

    finally:
        sys.path = sys_path
