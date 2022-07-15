from dagster import ModeDefinition, repository
from dagster._legacy import pipeline, solid

from .prod_dev_resources import dev_external_service, prod_external_service


@solid(required_resource_keys={"external_service"})
def do_something():
    ...


# start
@pipeline(
    mode_defs=[
        ModeDefinition("prod", resource_defs={"external_service": prod_external_service}),
        ModeDefinition("dev", resource_defs={"external_service": dev_external_service}),
    ]
)
def do_it_all():
    do_something()


@repository
def repo():
    return [do_it_all]


# end
