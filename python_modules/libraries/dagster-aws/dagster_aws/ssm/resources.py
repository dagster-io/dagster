from contextlib import contextmanager

from dagster_aws.utils import BOTO3_SESSION_CONFIG

from dagster import Array, Field, Shape
from dagster import _check as check
from dagster import resource
from dagster._core.test_utils import environ
from dagster._utils.merger import merge_dicts

from .parameters import (
    construct_ssm_client,
    get_parameters_by_name,
    get_parameters_by_paths,
    get_parameters_by_tags,
)


@resource(BOTO3_SESSION_CONFIG)
def ssm_resource(context):
    """Resource that gives access to AWS Systems Manager Parameter Store.

    The underlying Parameter Store session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is a Systems Manager client, an instance of `botocore.client.ssm`.

    Example:

        .. code-block:: python

            from dagster import build_op_context, job, op
            from dagster_aws.ssm import ssm_resource

            @op(required_resource_keys={'ssm'})
            def example_ssm_op(context):
                return context.resources.ssm.get_parameter(
                    Name="a_parameter"
                )

            @job(resource_defs={'ssm': ssm_resource})
            def example_job():
                example_ssm_op()

            example_job.execute_in_process(
                run_config={
                    'resources': {
                        'ssm': {
                            'config': {
                                'region_name': 'us-west-1',
                            }
                        }
                    }
                }
            )

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          parameter_store:
            config:
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the Parameter Store session. Default is chosen
              # through the ordinary boto credential chain.
              profile_name: "dev"
              # Optional[str]: Specifies a custom profile for Parameter Store session. Default is default
              # profile as specified in ~/.aws/credentials file

    """
    return construct_ssm_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        profile_name=context.resource_config.get("profile_name"),
    )


tag_shape = Shape(
    {
        "key": Field(str, is_required=True, description="Tag key to search for."),
        "values": Field(
            [str],
            is_required=False,
            description="List of tag values to match on. If no values are provided, "
            "all parameters with the given tag key will be returned. Note: the "
            "underlying AWS API will throw an exception when more than 10 "
            "parameters match the tag filter query.",
        ),
    }
)


@resource(
    merge_dicts(
        BOTO3_SESSION_CONFIG,
        {
            "parameters": Field(
                Array(str),
                is_required=False,
                default_value=[],
                description="An array of AWS SSM Parameter Store parameter names to fetch.",
            ),
            "parameter_tags": Field(
                Array(tag_shape),
                is_required=False,
                default_value=[],
                description="AWS SSM Parameter store parameters with this tag will be fetched and made available.",
            ),
            "parameter_paths": Field(
                [str],
                is_required=False,
                default_value=[],
                description="List of path prefixes to pull parameters from.",
            ),
            "with_decryption": Field(
                bool,
                is_required=False,
                default_value=False,
                description="Whether to decrypt parameters upon retrieval. Is ignored by AWS if parameter type is String or StringList",
            ),
            "add_to_environment": Field(
                bool,
                is_required=False,
                default_value=False,
                description="Whether to mount the parameters as environment variables.",
            ),
        },
    )
)
@contextmanager
def parameter_store_resource(context):
    """Resource that provides a dict which maps selected SSM Parameter Store parameters to
    their string values. Optionally sets selected parameters as environment variables.

    Example:

        .. code-block:: python

            import os
            from dagster import build_op_context, job, op
            from dagster_aws.ssm import parameter_store_resource

            @op(required_resource_keys={'parameter_store'})
            def example_parameter_store_op(context):
                return context.resources.parameter_store.get("my-parameter-name")

            @op(required_resource_keys={'parameter_store'})
            def example_parameter_store_op_2(context):
                return os.getenv("my-other-parameter-name")

            @job(resource_defs={'parameter_store': parameter_store_resource})
            def example_job():
                example_parameter_store_op()
                example_parameter_store_op_2()

            example_job.execute_in_process(
                run_config={
                    'resources': {
                        'parameter_store': {
                            'config': {
                                'region_name': 'us-west-1',
                                'parameter_tags': 'dagster',
                                'add_to_environment': True,
                                'with_decryption': True,
                            }
                        }
                    }
                }
            )

    Note that your ops must also declare that they require this resource with
    `required_resource_keys`, or it will not be initialized for the execution of their compute
    functions.

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          parameter_store:
            config:
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the Parameter Store session. Default is chosen
              # through the ordinary boto credential chain.
              profile_name: "dev"
              # Optional[str]: Specifies a custom profile for Parameter Store session. Default is default
              # profile as specified in ~/.aws/credentials file
              parameters: ["parameter1", "/path/based/parameter2"]
              # Optional[List[str]]: Specifies a list of parameter names to pull from parameter store.
              parameters_tag: "dagster"
              # Optional[Sequence[Dict[str, Any]]]: Specifies a list of tag specifications, all parameters which have the tag set
              will be pulled  from Parameter Store. Each tag specification is in the format {"tag": "tag name or prefix", "option": "BeginsWith|Equals"};
              when option == "BeginsWith", all parameters with tags that start with the tag value will be pulled.
              add_to_environment: true
              # Optional[bool]: Whether to set the selected parameters as environment variables. Defaults
              # to false.

    """
    add_to_environment = check.bool_param(
        context.resource_config["add_to_environment"], "add_to_environment"
    )
    parameter_tags = check.opt_list_param(
        context.resource_config["parameter_tags"], "parameter_tags", of_type=dict
    )
    parameters = check.list_param(context.resource_config["parameters"], "parameters", of_type=str)
    parameter_paths = check.list_param(
        context.resource_config["parameter_paths"], "parameter_paths", of_type=str
    )
    with_decryption = check.bool_param(
        context.resource_config["with_decryption"], "with_decryption"
    )

    ssm_manager = construct_ssm_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        profile_name=context.resource_config.get("profile_name"),
    )

    results = []
    if parameters:
        results.append(get_parameters_by_name(ssm_manager, parameters, with_decryption))
    if parameter_tags:
        results.append(get_parameters_by_tags(ssm_manager, parameter_tags, with_decryption))
    if parameter_paths:
        results.append(
            get_parameters_by_paths(ssm_manager, parameter_paths, with_decryption, recursive=True)
        )
    if not results:
        parameter_values = {}
    else:
        if len(results) > 1:
            parameter_values = merge_dicts(*results)
        else:
            parameter_values = results[0]

    with environ(parameter_values if add_to_environment else {}):
        yield parameter_values
