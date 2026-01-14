"""Snowflake resource configuration and helpers."""

import base64
import binascii
import os
import re
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

from dagster_snowflake_ai.defs.constants import DEFAULT_SCHEMA


class SnowflakeConfig(dg.ConfigurableResource):
    """Configuration for Snowflake connection.

    Supports both password and private key authentication.
    If private_key is provided, it will be used instead of password.
    """

    account: str
    user: str
    password: str = dg.EnvVar("SNOWFLAKE_PASSWORD")
    database: str
    warehouse: str
    schema_name: str = "PUBLIC"
    role: str | None = None
    private_key: str | None = None
    private_key_passphrase: str | None = None
    private_key_format: str = "PEM"

    @staticmethod
    def parse_private_key(key_data: str, format: str = "PEM") -> bytes:
        """Parse private key from PEM or DER format (handles base64, with/without headers)."""
        if not isinstance(key_data, str):
            raise TypeError(f"key_data must be a string, got {type(key_data).__name__}")

        if not key_data.strip():
            raise ValueError("key_data cannot be empty")

        if format not in ("PEM", "DER"):
            raise ValueError(f"Unsupported format: {format}. Must be 'PEM' or 'DER'")

        try:
            try:
                decoded = base64.b64decode(key_data, validate=True)
                if format == "DER":
                    return decoded
                key_data = decoded.decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                pass

            if format == "PEM":
                key_data = key_data.strip()

                if not key_data.startswith("-----BEGIN"):
                    key_data = f"-----BEGIN PRIVATE KEY-----\n{key_data}\n-----END PRIVATE KEY-----"

                key_data = key_data.replace("\\n", "\n")

                return key_data.encode("utf-8")

            if format == "DER":
                if isinstance(key_data, str):
                    try:
                        return base64.b64decode(key_data, validate=True)
                    except (binascii.Error, ValueError):
                        return key_data.encode("utf-8")
                return (
                    key_data
                    if isinstance(key_data, bytes)
                    else key_data.encode("utf-8")
                )

            raise ValueError(f"Unsupported format: {format}")

        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Failed to parse private key: {exc}") from exc

    def make_resource(self) -> SnowflakeResource:
        """Create SnowflakeResource. Uses private_key if provided, otherwise password."""
        resource_kwargs = {
            "account": self.account,
            "user": self.user,
            "database": self.database,
            "warehouse": self.warehouse,
            "schema": self.schema_name,
        }

        if self.role:
            resource_kwargs["role"] = self.role

        private_key = self.private_key or os.getenv("SNOWFLAKE_PRIVATE_KEY")
        if private_key:
            try:
                key_bytes = self.parse_private_key(private_key, self.private_key_format)
                passphrase = self.private_key_passphrase or os.getenv(
                    "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
                )
                key_obj = serialization.load_pem_private_key(
                    key_bytes,
                    password=passphrase.encode("utf-8") if passphrase else None,
                )
                pem_key = key_obj.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,
                    encryption_algorithm=NoEncryption(),
                )
                resource_kwargs["private_key"] = pem_key.decode("utf-8")
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Failed to load private key: {exc}") from exc
        else:
            resource_kwargs["password"] = self.password

        return SnowflakeResource(**resource_kwargs)  # type: ignore[call-arg]


def make_snowflake_resource(config: SnowflakeConfig) -> SnowflakeResource:
    """Backward compatibility wrapper for config.make_resource()."""
    return config.make_resource()


class SnowflakeResourceHelper:
    """Helper class for SnowflakeResource operations."""

    @staticmethod
    @contextmanager
    def get_connection_with_schema(
        snowflake: "SnowflakeResource",
    ) -> Generator[tuple[object, str], None, None]:
        """Get Snowflake connection and current schema."""
        with snowflake.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT CURRENT_SCHEMA()")
                schema_result = cursor.fetchone()
                schema = schema_result[0] if schema_result else DEFAULT_SCHEMA
            except (AttributeError, RuntimeError) as exc:
                raise RuntimeError(
                    f"Failed to get schema from Snowflake connection: {exc}"
                ) from exc
            yield connection, schema

    @staticmethod
    def quote_identifier(identifier: str) -> str:
        """Quote Snowflake identifier if needed (reserved words, starts with number, special chars)."""
        if not identifier:
            raise ValueError("Identifier cannot be empty or None")

        if identifier.startswith('"') and identifier.endswith('"'):
            return identifier

        reserved_words = {
            "select",
            "from",
            "where",
            "group",
            "order",
            "by",
            "having",
            "insert",
            "update",
            "delete",
            "create",
            "drop",
            "alter",
            "table",
            "view",
            "database",
            "schema",
            "warehouse",
            "role",
            "user",
            "grant",
            "revoke",
            "use",
            "show",
            "describe",
            "explain",
            "with",
            "as",
        }

        needs_quoting = (
            identifier.lower() in reserved_words
            or (identifier and identifier[0].isdigit())
            or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_$]*$", identifier)
        )

        if needs_quoting:
            escaped = identifier.replace('"', '""')
            return f'"{escaped}"'

        return identifier

    @staticmethod
    def sanitize_column_name(name: str) -> str:
        """Sanitize column name for Snowflake (spaces→underscores, remove special chars, ensure valid start)."""
        if not name:
            return name

        sanitized = re.sub(r"[\s-]+", "_", name)
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", sanitized)

        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized

        if not sanitized:
            sanitized = "_column"

        return sanitized

    @staticmethod
    def validate_column_name(name: str) -> bool:
        """Check if column name needs quoting in Snowflake."""
        if not name:
            return False

        if name.startswith('"') and name.endswith('"'):
            return False

        reserved_words = {
            "select",
            "from",
            "where",
            "group",
            "order",
            "by",
            "having",
            "insert",
            "update",
            "delete",
            "create",
            "drop",
            "alter",
            "table",
        }

        return (
            name.lower() in reserved_words
            or (name and name[0].isdigit())
            or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_$]*$", name)
        )

    @staticmethod
    def build_safe_query(template: str, **kwargs: str) -> str:
        """Build SQL query with quoted identifiers. Does NOT protect against SQL injection for values."""
        quoted_kwargs = {
            k: SnowflakeResourceHelper.quote_identifier(v) for k, v in kwargs.items()
        }
        return template.format(**quoted_kwargs)

    @staticmethod
    def quote_schema_table(schema: str, table: str) -> str:
        """Quote schema.table identifiers."""
        return f"{SnowflakeResourceHelper.quote_identifier(schema)}.{SnowflakeResourceHelper.quote_identifier(table)}"
