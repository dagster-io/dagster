from dagster import Field, resource

from .utils import create_s3_session


@resource(
    {
        'use_unsigned_session': Field(
            bool,
            description='Specifies whether to use an unsigned S3 session',
            is_required=False,
            default_value=False,
        ),
        'region_name': Field(
            str, description='Specifies a custom region for the S3 session', is_required=False
        ),
        'endpoint_url': Field(
            str, description='Specifies a custom endpoint for the S3 session', is_required=False
        ),
    }
)
def s3_resource(context):
    '''Resource that gives solids access to S3.

    The underlying S3 session is created by calling :py:func:`boto3.resource('s3') <boto3:boto3.resource>`.

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition` in order to make it
    available to your solids.

    Example:

        .. code-block:: python

            from dagster import ModeDefinition, execute_solid, solid
            from dagster_aws.s3 import s3_resource

            @solid(required_resource_keys={'s3'})
            def example_s3_solid(context):
                return context.resources.s3.list_objects_v2(
                    Bucket='my-bucket',
                    Prefix='some-key'
                )

            result = execute_solid(
                example_s3_solid,
                environment_dict={
                    'resources': {
                        's3': {
                            'config': {
                                'region_name': 'us-west-1',
                            }
                        }
                    }
                },
                mode_def=ModeDefinition(resource_defs={'s3': s3_resource}),
            )

    Note that your solids must also declare that they require this resource with
    `required_resource_keys`, or it will not be initialized for the execution of their compute
    functions.

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          s3:
            config:
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the S3 session. Default is chosen
              # through the ordinary boto credential chain.
              use_unsigned_session: false
              # Optional[bool]: Specifies whether to use an unsigned S3 session. Default: True
              endpoint_url: "http://localhost"
              # Optional[str]: Specifies a custom endpoint for the S3 session. Default is None.
    '''
    use_unsigned_session = context.resource_config['use_unsigned_session']
    region_name = context.resource_config.get('region_name')
    endpoint_url = context.resource_config.get('endpoint_url')

    return create_s3_session(
        signed=not use_unsigned_session, region_name=region_name, endpoint_url=endpoint_url
    )
