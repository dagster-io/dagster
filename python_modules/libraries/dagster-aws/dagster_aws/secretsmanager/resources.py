from contextlib import contextmanager

from dagster import Array, Field, Noneable
from dagster import _check as check
from dagster import resource
from dagster._core.test_utils import environ
from dagster._utils.merger import merge_dicts

from .secrets import construct_secretsmanager_client, get_secrets_from_arns, get_tagged_secrets

SECRETSMANAGER_SESSION_CONFIG = {
    "region_name": Field(
        str,
        description="Specifies a custom region for the SecretsManager session",
        is_required=False,
    ),
    "max_attempts": Field(
        int,
        description="This provides Boto3's retry handler with a value of maximum retry attempts, "
        "where the initial call counts toward the max_attempts value that you provide",
        is_required=False,
        default_value=5,
    ),
    "profile_name": Field(
        str,
        description="Specifies a profile to connect that session",
        is_required=False,
    ),
}


@resource(SECRETSMANAGER_SESSION_CONFIG)
def secretsmanager_resource(context):
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

    """
    return construct_secretsmanager_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        profile_name=context.resource_config.get("profile_name"),
    )


@resource(
    merge_dicts(
        SECRETSMANAGER_SESSION_CONFIG,
        {
            "secrets": Field(
                Array(str),
                is_required=False,
                default_value=[],
                description=("An array of AWS Secrets Manager secrets arns to fetch."),
            ),
            "secrets_tag": Field(
                Noneable(str),
                is_required=False,
                default_value=None,
                description=(
                    "AWS Secrets Manager secrets with this tag will be fetched and made available."
                ),
            ),
            "add_to_environment": Field(
                bool,
                is_required=False,
                default_value=False,
                description=("Whether to mount the secrets as environment variables."),
            ),
        },
    )
)
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
    add_to_environment = check.bool_param(
        context.resource_config["add_to_environment"], "add_to_environment"
    )
    secrets_tag = check.opt_str_param(context.resource_config["secrets_tag"], "secrets_tag")
    secrets = check.list_param(context.resource_config["secrets"], "secrets", of_type=str)

    secrets_manager = construct_secretsmanager_client(
        max_attempts=context.resource_config["max_attempts"],
        region_name=context.resource_config.get("region_name"),
        profile_name=context.resource_config.get("profile_name"),
    )

    secret_arns = merge_dicts(
        (get_tagged_secrets(secrets_manager, [secrets_tag]) if secrets_tag else {}),
        get_secrets_from_arns(secrets_manager, secrets),
    )

    secrets_map = {
        name: secrets_manager.get_secret_value(SecretId=arn).get("SecretString")
        for name, arn in secret_arns.items()
    }
    with environ(secrets_map if add_to_environment else {}):
        yield secrets_map
