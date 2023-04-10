from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

import botocore
from dagster import (
    Config,
    InitResourceContext,
    resource,
)
from dagster._core.test_utils import environ
from dagster._utils.merger import merge_dicts
from pydantic import Field

from dagster_aws.utils import ResourceWithBoto3Configuration

from .parameters import (
    construct_ssm_client,
    get_parameters_by_name,
    get_parameters_by_paths,
    get_parameters_by_tags,
)


class SSMResource(ResourceWithBoto3Configuration["botocore.client.ssm"]):
    """Resource that gives access to AWS Systems Manager Parameter Store.

    The underlying Parameter Store session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is a Systems Manager client, an instance of `botocore.client.ssm`.

    Example:
        .. code-block:: python

            from typing import Any
            from dagster import build_op_context, job, op, Resource
            from dagster_aws.ssm import SSMResource

            @op
            def example_ssm_op(ssm: Resource[Any]):
                return ssm.get_parameter(
                    Name="a_parameter"
                )

            @job
            def example_job():
                example_ssm_op()

            defs = Definitions(
                jobs=[example_job],
                resources={
                    'ssm': SSMResource(
                        region_name='us-west-1'
                    )
                }
            )
    """

    def provide_object_for_execution(self, context: InitResourceContext) -> Any:
        return construct_ssm_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )


@resource(config_schema=SSMResource.to_config_schema())
def ssm_resource(context) -> "botocore.client.ssm":
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
    return SSMResource.from_resource_context(context)


class ParameterStoreTag(Config):
    key: str = Field(description="Tag key to search for.")
    values: Optional[List[str]] = Field(default=None, description="List")


class ParameterStoreResource(ResourceWithBoto3Configuration[Dict[str, str]]):
    """Resource that provides a dict which maps selected SSM Parameter Store parameters to
    their string values. Optionally sets selected parameters as environment variables.

    Example:
        .. code-block:: python

            import os
            from typing import Dict
            from dagster import build_op_context, job, op, Resource
            from dagster_aws.ssm import ParameterStoreResource, ParameterStoreTag

            @op
            def example_parameter_store_op(parameter_store: Resource[Dict[str, str]]):
                return context.resources.parameter_store.get("my-parameter-name")

            @op
            def example_parameter_store_op_2(parameter_store: Resource[Dict[str, str]]):
                return os.getenv("my-other-parameter-name")

            @job
            def example_job():
                example_parameter_store_op()
                example_parameter_store_op_2()

            defs = Definitions(
                jobs=[example_job],
                resource_defs={
                    'parameter_store': ParameterStoreResource(
                        region_name='us-west-1',
                        parameter_tags=[ParameterStoreTag(key='my-tag-key', values=['my-tag-value'])],
                        add_to_environment=True,
                        with_decryption=True,
                    )
                },
            )
    """

    parameters: List[str] = Field(
        default=[], description="An array of AWS SSM Parameter Store parameter names to fetch."
    )
    parameter_tags: List[ParameterStoreTag] = Field(
        default=[],
        description=(
            "AWS SSM Parameter store parameters with this tag will be fetched and made available."
        ),
    )
    parameter_paths: List[str] = Field(
        default=[], description="List of path prefixes to pull parameters from."
    )
    with_decryption: bool = Field(
        default=False,
        description=(
            "Whether to decrypt parameters upon retrieval. Is ignored by AWS if parameter type is"
            " String or StringList"
        ),
    )
    add_to_environment: bool = Field(
        default=False, description="Whether to add the parameters to the environment."
    )

    def provide_object_for_execution(
        self, context: InitResourceContext
    ) -> Generator[Dict[str, str], None, None]:
        ssm_manager = construct_ssm_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )

        results = []
        if self.parameters:
            results.append(
                get_parameters_by_name(ssm_manager, self.parameters, self.with_decryption)
            )
        if self.parameter_tags:
            parameter_tag_inputs = [
                {"key": tag.key, "values": tag.values} for tag in self.parameter_tags
            ]
            results.append(
                get_parameters_by_tags(ssm_manager, parameter_tag_inputs, self.with_decryption)
            )
        if self.parameter_paths:
            results.append(
                get_parameters_by_paths(
                    ssm_manager, self.parameter_paths, self.with_decryption, recursive=True  # type: ignore
                )
            )
        if not results:
            parameter_values = {}
        else:
            if len(results) > 1:
                parameter_values = merge_dicts(*results)
            else:
                parameter_values = results[0]

        with environ(parameter_values if self.add_to_environment else {}):
            yield parameter_values


@resource(config_schema=ParameterStoreResource.to_config_schema())
@contextmanager
def parameter_store_resource(context) -> Any:
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
    return ParameterStoreResource.from_resource_context(context)
