from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

from dagster import (
    resource,
)
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.test_utils import environ
from dagster._utils.merger import merge_dicts
from pydantic import Field

from dagster_aws.utils import Boto3ResourceBase

from .secrets import construct_secretsmanager_client, get_secrets_from_arns, get_tagged_secrets


class SecretsManagerResource(Boto3ResourceBase[Any]):
    """Resource that gives access to AWS SecretsManager.

    The underlying SecretsManager session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is a SecretsManager client, an instance of `botocore.client.SecretsManager`.

    Example:
        .. code-block:: python

            from dagster import build_op_context, job, op
            from dagster_aws.secretsmanager import SecretsManagerResource

            @op(required_resource_keys={'secretsmanager'})
            def example_secretsmanager_op(context):
                return context.resources.secretsmanager.get_secret_value(
                    SecretId='arn:aws:secretsmanager:region:aws_account_id:secret:appauthexample-AbCdEf'
                )

            @job(resource_defs={
                'secretsmanager': SecretsManagerResource(region_name='us-west-1')
            })
            def example_job():
                example_secretsmanager_op()

            example_job.execute_in_process()
    """

    def create_resource(self, context: InitResourceContext) -> Any:
        return construct_secretsmanager_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )


@resource(SecretsManagerResource.to_config_schema())
def secretsmanager_resource(context) -> Any:
    """Resource that gives access to AWS SecretsManager.

    The underlying SecretsManager session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is a SecretsManager client, an instance of `botocore.client.SecretsManager`.

    Example:
        .. code-block:: python

            from dagster import build_op_context, job, op
            from dagster_aws.secretsmanager import secretsmanager_resource

            @op(required_resource_keys={'secretsmanager'})
            def example_secretsmanager_op(context):
                return context.resources.secretsmanager.get_secret_value(
                    SecretId='arn:aws:secretsmanager:region:aws_account_id:secret:appauthexample-AbCdEf'
                )

            @job(resource_defs={'secretsmanager': secretsmanager_resource})
            def example_job():
                example_secretsmanager_op()

            example_job.execute_in_process(
                run_config={
                    'resources': {
                        'secretsmanager': {
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
          secretsmanager:
            config:
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the SecretsManager session. Default is chosen
              # through the ordinary boto credential chain.
              profile_name: "dev"
              # Optional[str]: Specifies a custom profile for SecretsManager session. Default is default
              # profile as specified in ~/.aws/credentials file

    """
    return SecretsManagerResource.from_resource_context(context)


class SecretsManagerSecretsResource(Boto3ResourceBase[Dict[str, str]]):
    """Resource that provides a dict which maps selected SecretsManager secrets to
    their string values. Also optionally sets chosen secrets as environment variables.

    Example:
        .. code-block:: python

            import os
            from dagster import build_op_context, job, op
            from dagster_aws.secretsmanager import SecretsManagerSecretsResource

            @op(required_resource_keys={'secrets'})
            def example_secretsmanager_secrets_op(context):
                return context.resources.secrets.get("my-secret-name")

            @op(required_resource_keys={'secrets'})
            def example_secretsmanager_secrets_op_2(context):
                return os.getenv("my-other-secret-name")

            @job(resource_defs={
                'secrets': SecretsManagerSecretsResource(
                    region_name='us-west-1',
                    secrets_tag="dagster",
                    add_to_environment=True,
                )}
            )
            def example_job():
                example_secretsmanager_secrets_op()
                example_secretsmanager_secrets_op_2()

            example_job.execute_in_process()

    Note that your ops must also declare that they require this resource with or it will not be initialized
    for the execution of their compute functions.
    """

    secrets: List[str] = Field(
        default=[], description="An array of AWS Secrets Manager secrets arns to fetch."
    )
    secrets_tag: Optional[str] = Field(
        default=None,
        description="AWS Secrets Manager secrets with this tag will be fetched and made available.",
    )
    add_to_environment: bool = Field(
        default=False, description="Whether to mount the secrets as environment variables."
    )

    def create_resource(self, context: InitResourceContext) -> Iterable[Dict[str, str]]:
        secrets_manager = construct_secretsmanager_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )

        secret_arns = merge_dicts(
            (get_tagged_secrets(secrets_manager, [self.secrets_tag]) if self.secrets_tag else {}),
            get_secrets_from_arns(secrets_manager, self.secrets),
        )

        secrets_map = {
            name: secrets_manager.get_secret_value(SecretId=arn).get("SecretString")
            for name, arn in secret_arns.items()
        }
        with environ(secrets_map if self.add_to_environment else {}):
            yield secrets_map


@resource(config_schema=SecretsManagerSecretsResource.to_config_schema())
@contextmanager
def secretsmanager_secrets_resource(context):
    """Resource that provides a dict which maps selected SecretsManager secrets to
    their string values. Also optionally sets chosen secrets as environment variables.

    Example:
        .. code-block:: python

            import os
            from dagster import build_op_context, job, op
            from dagster_aws.secretsmanager import secretsmanager_secrets_resource

            @op(required_resource_keys={'secrets'})
            def example_secretsmanager_secrets_op(context):
                return context.resources.secrets.get("my-secret-name")

            @op(required_resource_keys={'secrets'})
            def example_secretsmanager_secrets_op_2(context):
                return os.getenv("my-other-secret-name")

            @job(resource_defs={'secrets': secretsmanager_secrets_resource})
            def example_job():
                example_secretsmanager_secrets_op()
                example_secretsmanager_secrets_op_2()

            example_job.execute_in_process(
                run_config={
                    'resources': {
                        'secrets': {
                            'config': {
                                'region_name': 'us-west-1',
                                'secrets_tag': 'dagster',
                                'add_to_environment': True,
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
          secretsmanager:
            config:
              region_name: "us-west-1"
              # Optional[str]: Specifies a custom region for the SecretsManager session. Default is chosen
              # through the ordinary boto credential chain.
              profile_name: "dev"
              # Optional[str]: Specifies a custom profile for SecretsManager session. Default is default
              # profile as specified in ~/.aws/credentials file
              secrets: ["arn:aws:secretsmanager:region:aws_account_id:secret:appauthexample-AbCdEf"]
              # Optional[List[str]]: Specifies a list of secret ARNs to pull from SecretsManager.
              secrets_tag: "dagster"
              # Optional[str]: Specifies a tag, all secrets which have the tag set will be pulled
              # from SecretsManager.
              add_to_environment: true
              # Optional[bool]: Whether to set the selected secrets as environment variables. Defaults
              # to false.

    """
    return SecretsManagerSecretsResource.from_resource_context(context)
