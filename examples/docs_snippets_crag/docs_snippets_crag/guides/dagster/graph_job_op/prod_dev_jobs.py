from dagster import graph, op, repository

from .prod_dev_resources import dev_external_service, prod_external_service


@op(required_resource_keys={"external_service"})
def do_something():
    ...


# start
@graph
def do_it_all():
    do_something()


@repository
def prod_repo():
    return [do_it_all.to_job(resource_defs={"external_service": prod_external_service})]


@repository
def dev_repo():
    return [do_it_all.to_job(resource_defs={"external_service": dev_external_service})]


# end
