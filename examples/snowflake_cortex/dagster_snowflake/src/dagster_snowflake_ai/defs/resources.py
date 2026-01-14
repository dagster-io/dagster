"""Dagster resources combining Snowflake, dbt, and ingestion resources."""

import os
import warnings
from collections.abc import Generator
from contextlib import contextmanager

import dagster as dg
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.dbt import get_dbt_resource
from dagster_snowflake_ai.defs.ingestion.resources import WebScraperResource
from dagster_snowflake_ai.defs.snowflake.resources import (
    SnowflakeConfig,
    SnowflakeResourceHelper,
)


@contextmanager
def get_snowflake_connection_with_schema(
    snowflake: "SnowflakeResource",
) -> Generator[tuple[object, str], None, None]:
    """Backward compatibility wrapper for SnowflakeResourceHelper.get_connection_with_schema()."""
    with SnowflakeResourceHelper.get_connection_with_schema(snowflake) as result:
        yield result


if SnowflakeResource is not None:
    snowflake_kwargs = {
        "account": dg.EnvVar("SNOWFLAKE_ACCOUNT"),
        "user": dg.EnvVar("SNOWFLAKE_USER"),
        "database": dg.EnvVar("SNOWFLAKE_DATABASE"),
        "warehouse": dg.EnvVar("SNOWFLAKE_WAREHOUSE"),
        "schema": dg.EnvVar("SNOWFLAKE_SCHEMA"),
    }

    private_key = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    if private_key:
        try:
            key_bytes = SnowflakeConfig.parse_private_key(
                private_key,
                os.getenv("SNOWFLAKE_PRIVATE_KEY_FORMAT", "PEM"),
            )
            passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
            key_obj = serialization.load_pem_private_key(
                key_bytes,
                password=passphrase.encode("utf-8") if passphrase else None,
            )
            pem_key = key_obj.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            )
            snowflake_kwargs["private_key"] = pem_key.decode("utf-8")
        except (ValueError, TypeError) as exc:
            warnings.warn(
                f"Failed to parse private key, falling back to password: {exc}",
                UserWarning,
                stacklevel=2,
            )
            snowflake_kwargs["password"] = dg.EnvVar("SNOWFLAKE_PASSWORD")
    else:
        snowflake_kwargs["password"] = dg.EnvVar("SNOWFLAKE_PASSWORD")

    if os.getenv("SNOWFLAKE_AUTHENTICATOR"):
        snowflake_kwargs["authenticator"] = dg.EnvVar("SNOWFLAKE_AUTHENTICATOR")

    resources = {
        "snowflake": SnowflakeResource(**snowflake_kwargs),  # type: ignore[call-arg]
        "dbt": get_dbt_resource(),
        "web_scraper": WebScraperResource(),
    }
else:
    resources = {
        "dbt": get_dbt_resource(),
        "web_scraper": WebScraperResource(),
    }
