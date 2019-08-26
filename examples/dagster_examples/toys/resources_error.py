# pylint: disable=no-value-for-parameter

from dagster import Field, Int, ModeDefinition, execute_pipeline, pipeline, resource, solid


@resource(config_field=Field(Int, is_optional=True))
def a_resource(context):
    raise Exception("Bad Resource")


resources = {'BadResource': a_resource}


@solid(required_resource_keys={'BadResource'})
def one(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(resource_defs=resources)])
def resource_error_pipeline():
    one()


if __name__ == '__main__':
    result = execute_pipeline(
        resource_error_pipeline,
        environment_dict={
            'storage': {'filesystem': {}},
            'execution': {'in_process': {'config': {'raise_on_error': False}}},
        },
    )
