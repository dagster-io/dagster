from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, cast

from dagster import (
    Config,
    Field as LegacyDagsterField,
    resource,
)
from dagster._config.field_utils import Shape
from dagster._core.definitions.resource_definition import dagster_maintained_resource
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

if TYPE_CHECKING:
    import botocore


class SSMResource(ResourceWithBoto3Configuration):
    """Resource that gives access to AWS Systems Manager Parameter Store.

    The underlying Parameter Store session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is a Systems Manager client, an instance of `botocore.client.ssm`.

    Example:
        .. code-block:: python

            from typing import Any
            from dagster import build_op_context, job, op
            from dagster_aws.ssm import SSMResource

            @op
            def example_ssm_op(ssm: SSMResource):
                return ssm.get_client().get_parameter(
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

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> "botocore.client.ssm":
        return construct_ssm_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )


@dagster_maintained_resource
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
    return SSMResource.from_resource_context(context).get_client()


class ParameterStoreTag(Config):
    key: str = Field(description="Tag key to search for.")
    values: Optional[List[str]] = Field(default=None, description="List")


class ParameterStoreResource(ResourceWithBoto3Configuration):
    """Resource that provides a dict which maps selected SSM Parameter Store parameters to
    their string values. Optionally sets selected parameters as environment variables.

    Example:
        .. code-block:: python

            import os
            from typing import Dict
            from dagster import build_op_context, job, op
            from dagster_aws.ssm import ParameterStoreResource, ParameterStoreTag

            @op
            def example_parameter_store_op(parameter_store: ParameterStoreResource):
                return parameter_store.fetch_parameters().get("my-parameter-name")

            @op
            def example_parameter_store_op_2(parameter_store: ParameterStoreResource):
                with parameter_store.parameters_in_environment():
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

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @contextmanager
    def parameters_in_environment(
        self,
        parameters: Optional[List[str]] = None,
        parameter_tags: Optional[List[ParameterStoreTag]] = None,
        parameter_paths: Optional[List[str]] = None,
    ) -> Generator[Dict[str, str], None, None]:
        """Yields a dict which maps selected Parameter Store parameters to their string values. Also
        sets chosen parameters as environment variables.

        Args:
            parameters (Optional[List[str]]):   An array of AWS SSM Parameter Store parameter names to fetch.
                Note that this will override the parameters specified in the resource config.
            parameter_tags (Optional[List[ParameterStoreTag]]): AWS SSM Parameter store parameters with this tag
                will be fetched and made available. Note that this will override the parameter_tags specified
                in the resource config.
            parameter_paths (Optional[List[str]]): List of path prefixes to pull parameters from. Note that this
                will override the parameter_paths specified in the resource config.
        """
        ssm_manager = construct_ssm_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )
        parameters_to_fetch = parameters if parameters is not None else self.parameters
        parameter_tags_to_fetch = (
            parameter_tags if parameter_tags is not None else self.parameter_tags
        )
        parameter_paths_to_fetch = (
            parameter_paths if parameter_paths is not None else self.parameter_paths
        )

        results = []
        if parameters_to_fetch:
            results.append(
                get_parameters_by_name(ssm_manager, parameters_to_fetch, self.with_decryption)
            )
        if parameter_tags_to_fetch:
            parameter_tag_inputs = [
                {"key": tag.key, "values": tag.values} for tag in parameter_tags_to_fetch
            ]
            results.append(
                get_parameters_by_tags(ssm_manager, parameter_tag_inputs, self.with_decryption)
            )
        if parameter_paths_to_fetch:
            results.append(
                get_parameters_by_paths(
                    ssm_manager, parameter_paths_to_fetch, self.with_decryption, recursive=True  # type: ignore
                )
            )
        if not results:
            parameter_values = {}
        else:
            if len(results) > 1:
                parameter_values = merge_dicts(*results)
            else:
                parameter_values = results[0]

        with environ(parameter_values):
            yield parameter_values

    def fetch_parameters(
        self,
        parameters: Optional[List[str]] = None,
        parameter_tags: Optional[List[ParameterStoreTag]] = None,
        parameter_paths: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Fetches parameters from SSM Parameter Store and returns them as a dict.

        Args:
            parameters (Optional[List[str]]):   An array of AWS SSM Parameter Store parameter names to fetch.
                Note that this will override the parameters specified in the resource config.
            parameter_tags (Optional[List[ParameterStoreTag]]): AWS SSM Parameter store parameters with this tag
                will be fetched and made available. Note that this will override the parameter_tags specified
                in the resource config.
            parameter_paths (Optional[List[str]]): List of path prefixes to pull parameters from. Note that this
                will override the parameter_paths specified in the resource config.
        """
        with self.parameters_in_environment(
            parameters=parameters, parameter_tags=parameter_tags, parameter_paths=parameter_paths
        ) as parameter_values:
            return parameter_values


LEGACY_PARAMETERSTORE_SCHEMA = {
    **cast(Shape, ParameterStoreResource.to_config_schema().as_field().config_type).fields,
    "add_to_environment": LegacyDagsterField(
        bool,
        default_value=False,
        description="Whether to add the paramters to the environment. Defaults to False.",
    ),
}


@dagster_maintained_resource
@resource(config_schema=LEGACY_PARAMETERSTORE_SCHEMA)
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
    add_to_environment = context.resource_config.get("add_to_environment", False)
    if add_to_environment:
        with ParameterStoreResource.from_resource_context(
            context
        ).parameters_in_environment() as secrets:
            yield secrets
    else:
        yield ParameterStoreResource.from_resource_context(context).fetch_parameters()
