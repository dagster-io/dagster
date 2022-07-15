from unittest.mock import MagicMock

from dagster import ModeDefinition, ResourceDefinition, execute_pipeline, resource
from dagster._legacy import pipeline, solid


@resource
def external_service():
    ...


@solid(required_resource_keys={"external_service"})
def do_something():
    ...


@pipeline(
    mode_defs=[
        ModeDefinition(resource_defs={"external_service": external_service}),
        ModeDefinition(
            "test",
            resource_defs={"external_service": ResourceDefinition.hardcoded_resource(MagicMock())},
        ),
    ]
)
def do_it_all():
    do_something()


def test_do_it_all():
    execute_pipeline(do_it_all, mode="test")
