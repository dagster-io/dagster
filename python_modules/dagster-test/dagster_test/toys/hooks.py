from dagster import (
    PipelineDefinition,
    SolidInvocation,
    failure_hook,
    repository,
    solid,
    success_hook,
)

called = {}


@success_hook
def a_success_hook(context):
    context.log.info('im a success hook on solid "{}"'.format(context.solid.name))


@failure_hook
def a_failure_hook(context):
    context.log.info('im a failure hook on solid "{}"'.format(context.solid.name))


@solid
def a_solid(_):
    pass


@solid
def failed_solid(_):
    raise Exception()


a_pipeline = PipelineDefinition(
    solid_defs=[a_solid, failed_solid],
    dependencies={
        SolidInvocation('a_solid', hook_defs={a_success_hook, a_failure_hook}): {},
        SolidInvocation('failed_solid', hook_defs={a_success_hook, a_failure_hook}): {},
    },
)


@repository
def repo():
    return [a_pipeline]
