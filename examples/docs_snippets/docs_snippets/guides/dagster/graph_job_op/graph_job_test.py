from unittest.mock import MagicMock

from dagster import job, op, resource


@resource
def external_service():
    ...


@op(required_resource_keys={"external_service"})
def do_something():
    ...


@job(resource_defs={"external_service": external_service})
def do_it_all():
    do_something()


def test_do_it_all():
    result = do_it_all.graph.execute_in_process(resources={"external_service": MagicMock()})
    assert result.success
