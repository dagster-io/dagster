from unittest.mock import MagicMock

from dagster import graph, op, resource


@resource
def external_service():
    ...


@op(required_resource_keys={"external_service"})
def do_something():
    ...


@graph
def do_it_all():
    do_something()


do_it_all_job = do_it_all.to_job(resource_defs={"external_service": external_service})


def test_do_it_all():
    do_it_all.execute_in_process(resources={"external_service": MagicMock()})
