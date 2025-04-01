import json
import os

from dagster._core.execution.context.init import build_init_resource_context
from dagster._core.test_utils import environ

from dagster_aws.secretsmanager import (
    SecretsManagerSecretsResource,
    get_secrets_from_arns,
    secretsmanager_secrets_resource,
)
from dagster_aws.secretsmanager.secrets import get_tagged_secrets


def test_get_secrets_from_arns(mock_secretsmanager_resource):
    foo_secret = mock_secretsmanager_resource.create_secret(
        Name="foo_secret", SecretString="foo_value"
    )
    bar_secret = mock_secretsmanager_resource.create_secret(
        Name="bar_secret", SecretString="bar_value"
    )
    assert get_secrets_from_arns(
        mock_secretsmanager_resource, [foo_secret["ARN"], bar_secret["ARN"]]
    ) == {"foo_secret": foo_secret["ARN"], "bar_secret": bar_secret["ARN"]}

    baz_secret = mock_secretsmanager_resource.create_secret(
        Name="baz_secret", SecretString="baz_value"
    )
    assert get_secrets_from_arns(
        mock_secretsmanager_resource, [foo_secret["ARN"], bar_secret["ARN"], baz_secret["ARN"]]
    ) == {
        "foo_secret": foo_secret["ARN"],
        "bar_secret": bar_secret["ARN"],
        "baz_secret": baz_secret["ARN"],
    }


def test_get_tagged_secrets(mock_secretsmanager_resource):
    assert get_tagged_secrets(mock_secretsmanager_resource, ["dagster"]) == {}

    foo_secret = mock_secretsmanager_resource.create_secret(
        Name="foo_secret", SecretString="foo_value", Tags=[{"Key": "dagster", "Value": "foo"}]
    )
    bar_secret = mock_secretsmanager_resource.create_secret(
        Name="bar_secret", SecretString="bar_value", Tags=[{"Key": "other_tag", "Value": "bar"}]
    )

    assert get_tagged_secrets(mock_secretsmanager_resource, ["dagster"]) == {
        "foo_secret": foo_secret["ARN"]
    }
    assert get_tagged_secrets(mock_secretsmanager_resource, ["other_tag"]) == {
        "bar_secret": bar_secret["ARN"]
    }

    assert get_tagged_secrets(mock_secretsmanager_resource, ["dagster", "other_tag"]) == {
        "foo_secret": foo_secret["ARN"],
        "bar_secret": bar_secret["ARN"],
    }

    baz_secret = mock_secretsmanager_resource.create_secret(
        Name="baz_secret", SecretString="baz_value", Tags=[{"Key": "dagster", "Value": "baz"}]
    )
    assert get_tagged_secrets(mock_secretsmanager_resource, ["dagster"]) == {
        "foo_secret": foo_secret["ARN"],
        "baz_secret": baz_secret["ARN"],
    }


def test_secretmanager_secrets_resource(mock_secretsmanager_resource):
    foo_secret = mock_secretsmanager_resource.create_secret(
        Name="foo_secret", SecretString="foo_value", Tags=[{"Key": "dagster", "Value": "foo"}]
    )
    bar_secret = mock_secretsmanager_resource.create_secret(
        Name="bar_secret", SecretString="bar_value", Tags=[{"Key": "other_tag", "Value": "bar"}]
    )
    _baz_secret = mock_secretsmanager_resource.create_secret(
        Name="baz_secret", SecretString="baz_value", Tags=[{"Key": "dagster", "Value": "baz"}]
    )
    asdf_secret = mock_secretsmanager_resource.create_secret(
        Name="asdf_secret", SecretString="asdf_value"
    )

    # Test various compbinations of secret ARNs and secret tags
    with secretsmanager_secrets_resource(
        build_init_resource_context(config={"secrets": [foo_secret["ARN"]]})
    ) as secret_map:
        assert secret_map == {"foo_secret": "foo_value"}

    with secretsmanager_secrets_resource(
        build_init_resource_context(config={"secrets": [foo_secret["ARN"], bar_secret["ARN"]]})
    ) as secret_map:
        assert secret_map == {"foo_secret": "foo_value", "bar_secret": "bar_value"}

    with secretsmanager_secrets_resource(
        build_init_resource_context(config={"secrets_tag": "dagster"})
    ) as secret_map:
        assert secret_map == {"foo_secret": "foo_value", "baz_secret": "baz_value"}

    with secretsmanager_secrets_resource(
        build_init_resource_context(
            config={"secrets_tag": "dagster", "secrets": [asdf_secret["ARN"]]}
        )
    ) as secret_map:
        assert secret_map == {
            "foo_secret": "foo_value",
            "baz_secret": "baz_value",
            "asdf_secret": "asdf_value",
        }

        assert os.getenv("foo_secret") is None
        assert os.getenv("baz_secret") is None
        assert os.getenv("asdf_secret") is None

    # Test adding secrets to the environment
    # Ensure env vars are overridden
    with environ({"foo_secret": "prior_foo_value"}):
        assert os.getenv("foo_secret") == "prior_foo_value"

        with secretsmanager_secrets_resource(
            build_init_resource_context(
                config={
                    "secrets_tag": "dagster",
                    "secrets": [asdf_secret["ARN"]],
                    "add_to_environment": True,
                }
            )
        ) as secret_map:
            assert secret_map == {
                "foo_secret": "foo_value",
                "baz_secret": "baz_value",
                "asdf_secret": "asdf_value",
            }

            assert os.getenv("foo_secret") == "foo_value"
            assert os.getenv("baz_secret") == "baz_value"
            assert os.getenv("asdf_secret") == "asdf_value"

    # Test JSON secret
    json_secret_obj = {"key1": "value1", "key2": {"nest1": "value2", "nest2": "value3"}}
    json_secret = mock_secretsmanager_resource.create_secret(
        Name="json_secret",
        SecretString=json.dumps(json_secret_obj),
    )
    with secretsmanager_secrets_resource(
        build_init_resource_context(
            config={
                "secrets": [json_secret["ARN"]],
                "add_to_environment": True,
            }
        )
    ) as secret_map:
        assert json.loads(secret_map["json_secret"]) == json_secret_obj

        assert json.loads(os.getenv("json_secret")) == json_secret_obj  # pyright: ignore[reportArgumentType]

    # Binary secrets have a None value
    binary_secret = mock_secretsmanager_resource.create_secret(
        Name="binary_secret", SecretBinary=b"binary_value"
    )
    with secretsmanager_secrets_resource(
        build_init_resource_context(
            config={
                "secrets": [binary_secret["ARN"]],
                "add_to_environment": True,
            }
        )
    ) as secret_map:
        assert secret_map == {
            "binary_secret": None,
        }

        assert os.getenv("binary_secret") is None


def test_secretmanager_secrets_resource_pythonic(mock_secretsmanager_resource) -> None:
    foo_secret = mock_secretsmanager_resource.create_secret(
        Name="foo_secret", SecretString="foo_value", Tags=[{"Key": "dagster", "Value": "foo"}]
    )
    bar_secret = mock_secretsmanager_resource.create_secret(
        Name="bar_secret", SecretString="bar_value", Tags=[{"Key": "other_tag", "Value": "bar"}]
    )
    _baz_secret = mock_secretsmanager_resource.create_secret(
        Name="baz_secret", SecretString="baz_value", Tags=[{"Key": "dagster", "Value": "baz"}]
    )
    asdf_secret = mock_secretsmanager_resource.create_secret(
        Name="asdf_secret", SecretString="asdf_value"
    )

    # Test various compbinations of secret ARNs and secret tags
    assert SecretsManagerSecretsResource(secrets=[foo_secret["ARN"]]).fetch_secrets() == {
        "foo_secret": "foo_value"
    }

    assert SecretsManagerSecretsResource(
        secrets=[foo_secret["ARN"], bar_secret["ARN"]]
    ).fetch_secrets() == {"foo_secret": "foo_value", "bar_secret": "bar_value"}

    assert SecretsManagerSecretsResource(secrets_tag="dagster").fetch_secrets() == {
        "foo_secret": "foo_value",
        "baz_secret": "baz_value",
    }

    assert SecretsManagerSecretsResource(
        secrets_tag="dagster", secrets=[asdf_secret["ARN"]]
    ).fetch_secrets() == {
        "foo_secret": "foo_value",
        "baz_secret": "baz_value",
        "asdf_secret": "asdf_value",
    }

    # Test fetching as params rather than via config
    assert SecretsManagerSecretsResource().fetch_secrets(
        secrets=[foo_secret["ARN"], bar_secret["ARN"]]
    ) == {"foo_secret": "foo_value", "bar_secret": "bar_value"}

    assert SecretsManagerSecretsResource().fetch_secrets(secrets_tag="dagster") == {
        "foo_secret": "foo_value",
        "baz_secret": "baz_value",
    }

    assert SecretsManagerSecretsResource().fetch_secrets(
        secrets_tag="dagster", secrets=[asdf_secret["ARN"]]
    ) == {
        "foo_secret": "foo_value",
        "baz_secret": "baz_value",
        "asdf_secret": "asdf_value",
    }

    # Test fetching as params rather than via config overrides config
    assert SecretsManagerSecretsResource(secrets=[bar_secret["ARN"]]).fetch_secrets(
        secrets=[foo_secret["ARN"]]
    ) == {"foo_secret": "foo_value"}

    # Test adding secrets to the environment
    # Ensure env vars are overridden
    with environ({"foo_secret": "prior_foo_value"}):
        assert os.getenv("foo_secret") == "prior_foo_value"

        with SecretsManagerSecretsResource(
            secrets_tag="dagster",
            secrets=[asdf_secret["ARN"]],
        ).secrets_in_environment() as secret_map:
            assert secret_map == {
                "foo_secret": "foo_value",
                "baz_secret": "baz_value",
                "asdf_secret": "asdf_value",
            }

            assert os.getenv("foo_secret") == "foo_value"
            assert os.getenv("baz_secret") == "baz_value"
            assert os.getenv("asdf_secret") == "asdf_value"

    # Test JSON secret
    json_secret_obj = {"key1": "value1", "key2": {"nest1": "value2", "nest2": "value3"}}
    json_secret = mock_secretsmanager_resource.create_secret(
        Name="json_secret",
        SecretString=json.dumps(json_secret_obj),
    )
    with SecretsManagerSecretsResource(
        secrets=[json_secret["ARN"]],
    ).secrets_in_environment() as secret_map:
        assert json.loads(secret_map["json_secret"]) == json_secret_obj

        assert json.loads(str(os.getenv("json_secret"))) == json_secret_obj

    # Binary secrets have a None value
    binary_secret = mock_secretsmanager_resource.create_secret(
        Name="binary_secret", SecretBinary=b"binary_value"
    )
    with SecretsManagerSecretsResource(
        secrets=[binary_secret["ARN"]]
    ).secrets_in_environment() as secret_map:
        assert secret_map == {
            "binary_secret": None,
        }

        assert os.getenv("binary_secret") is None
