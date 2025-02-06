from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional, cast

from dagster import (
    Field as LegacyDagsterField,
    resource,
)
from dagster._annotations import beta
from dagster._config.field_utils import Shape
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.test_utils import environ
from dagster._utils.merger import merge_dicts
from pydantic import Field

from dagster_aws.secretsmanager.secrets import (
    construct_secretsmanager_client,
    get_secrets_from_arns,
    get_tagged_secrets,
)
from dagster_aws.utils import ResourceWithBoto3Configuration

if TYPE_CHECKING:
    import botocore


@beta
class SecretsManagerResource(ResourceWithBoto3Configuration):
    """Resource that gives access to AWS SecretsManager.

    The underlying SecretsManager session is created by calling
    :py:func:`boto3.session.Session(profile_name) <boto3:boto3.session>`.
    The returned resource object is a SecretsManager client, an instance of `botocore.client.SecretsManager`.

    Example:
        .. code-block:: python

            from dagster import build_op_context, job, op
            from dagster_aws.secretsmanager import SecretsManagerResource

            @op
            def example_secretsmanager_op(secretsmanager: SecretsManagerResource):
                return secretsmanager.get_client().get_secret_value(
                    SecretId='arn:aws:secretsmanager:region:aws_account_id:secret:appauthexample-AbCdEf'
                )

            @job
            def example_job():
                example_secretsmanager_op()

            defs = Definitions(
                jobs=[example_job],
                resources={
                    'secretsmanager': SecretsManagerResource(
                        region_name='us-west-1'
                    )
                }
            )
    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> "botocore.client.SecretsManager":  # pyright: ignore (reportAttributeAccessIssue)
        return construct_secretsmanager_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
            endpoint_url=self.endpoint_url,
            use_ssl=self.use_ssl,
            verify=self.verify,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
        )


@beta
@dagster_maintained_resource
@resource(SecretsManagerResource.to_config_schema())
def secretsmanager_resource(context) -> "botocore.client.SecretsManager":  # pyright: ignore (reportAttributeAccessIssue)
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
    return SecretsManagerResource.from_resource_context(context).get_client()


@beta
class SecretsManagerSecretsResource(ResourceWithBoto3Configuration):
    """Resource that provides a dict which maps selected SecretsManager secrets to
    their string values. Also optionally sets chosen secrets as environment variables.

    Example:
        .. code-block:: python

            import os
            from dagster import build_op_context, job, op, ResourceParam
            from dagster_aws.secretsmanager import SecretsManagerSecretsResource

            @op
            def example_secretsmanager_secrets_op(secrets: SecretsManagerSecretsResource):
                return secrets.fetch_secrets().get("my-secret-name")

            @op
            def example_secretsmanager_secrets_op_2(secrets: SecretsManagerSecretsResource):
                with secrets.secrets_in_environment():
                    return os.getenv("my-other-secret-name")

            @job
            def example_job():
                example_secretsmanager_secrets_op()
                example_secretsmanager_secrets_op_2()

            defs = Definitions(
                jobs=[example_job],
                resources={
                    'secrets': SecretsManagerSecretsResource(
                        region_name='us-west-1',
                        secrets_tag="dagster",
                        add_to_environment=True,
                    )
                }
            )

    Note that your ops must also declare that they require this resource with or it will not be initialized
    for the execution of their compute functions.
    """

    secrets: list[str] = Field(
        default=[], description="An array of AWS Secrets Manager secrets arns to fetch."
    )
    secrets_tag: Optional[str] = Field(
        default=None,
        description="AWS Secrets Manager secrets with this tag will be fetched and made available.",
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @contextmanager
    def secrets_in_environment(
        self,
        secrets: Optional[list[str]] = None,
        secrets_tag: Optional[str] = None,
    ) -> Generator[dict[str, str], None, None]:
        """Yields a dict which maps selected SecretsManager secrets to their string values. Also
        sets chosen secrets as environment variables.

        Args:
            secrets (Optional[List[str]]): An array of AWS Secrets Manager secrets arns to fetch.
                Note that this will override the secrets specified in the resource config.
            secrets_tag (Optional[str]): AWS Secrets Manager secrets with this tag will be fetched
                and made available. Note that this will override the secrets_tag specified in the
                resource config.
        """
        secrets_manager = construct_secretsmanager_client(
            max_attempts=self.max_attempts,
            region_name=self.region_name,
            profile_name=self.profile_name,
        )

        secrets_tag_to_fetch = secrets_tag if secrets_tag is not None else self.secrets_tag
        secrets_to_fetch = secrets if secrets is not None else self.secrets

        secret_arns = merge_dicts(
            (
                get_tagged_secrets(secrets_manager, [secrets_tag_to_fetch])
                if secrets_tag_to_fetch
                else {}
            ),
            get_secrets_from_arns(secrets_manager, secrets_to_fetch),
        )

        secrets_map = {
            name: secrets_manager.get_secret_value(SecretId=arn).get("SecretString")
            for name, arn in secret_arns.items()
        }
        with environ(secrets_map):
            yield secrets_map

    def fetch_secrets(
        self,
        secrets: Optional[list[str]] = None,
        secrets_tag: Optional[str] = None,
    ) -> dict[str, str]:
        """Fetches secrets from AWS Secrets Manager and returns them as a dict.

        Args:
            secrets (Optional[List[str]]): An array of AWS Secrets Manager secrets arns to fetch.
                Note that this will override the secrets specified in the resource config.
            secrets_tag (Optional[str]): AWS Secrets Manager secrets with this tag will be fetched
                and made available. Note that this will override the secrets_tag specified in the
                resource config.
        """
        with self.secrets_in_environment(secrets=secrets, secrets_tag=secrets_tag) as secret_values:
            return secret_values


LEGACY_SECRETSMANAGER_SECRETS_SCHEMA = {
    **cast(Shape, SecretsManagerSecretsResource.to_config_schema().as_field().config_type).fields,
    "add_to_environment": LegacyDagsterField(
        bool,
        default_value=False,
        description="Whether to add the secrets to the environment. Defaults to False.",
    ),
}


@beta
@dagster_maintained_resource
@resource(config_schema=LEGACY_SECRETSMANAGER_SECRETS_SCHEMA)
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
    add_to_environment = context.resource_config.get("add_to_environment", False)
    if add_to_environment:
        with SecretsManagerSecretsResource.from_resource_context(
            context
        ).secrets_in_environment() as secrets:
            yield secrets
    else:
        yield SecretsManagerSecretsResource.from_resource_context(context).fetch_secrets()
