import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Literal

import pydantic
from cryptography.hazmat.primitives import serialization


class UserFacingDataError(Exception):
    pass


def run_snowflake_query(connect_args: dict, query: str) -> list[dict[str, Any]]:
    import snowflake.connector

    params = dict(connect_args)

    conn = snowflake.connector.connect(
        **params,
    )
    with conn:
        conn.telemetry_enabled = False
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]  # type: ignore


@dataclass
class TableInfo:
    """Information about a database table"""

    name: str
    description: str | None


@dataclass
class SchemaTablesResult:
    """Result of attempting to discover tables in a single schema"""

    schema_name: str
    success: bool
    tables: list[TableInfo]
    error: str | None


@dataclass
class ListTablesResult:
    """Overall result of table discovery across multiple schemas"""

    success: bool
    schema_results: list[SchemaTablesResult]
    error: str | None

    @property
    def all_tables(self) -> list[TableInfo]:
        """Get all successfully discovered tables"""
        tables = []
        for result in self.schema_results:
            if result.success:
                tables.extend(result.tables)
        return tables

    @property
    def failed_schemas(self) -> list[str]:
        """Get list of schemas that failed"""
        return [r.schema_name for r in self.schema_results if not r.success]

    @property
    def has_any_success(self) -> bool:
        """Check if at least one schema succeeded"""
        return any(r.success for r in self.schema_results)


@dataclass
class WarehouseNetworkInfo:
    """Network access information for warehouse connections"""

    connection_method: str
    port: str | None = None
    ip_addresses: list[str] | None = None
    additional_info: str | None = None


@dataclass
class WarehousePermissionInfo:
    """Permission requirements for warehouse operations"""

    header: str
    permissions: list[str]


@dataclass
class WarehouseHelpInfo:
    """Help information for warehouse setup and operations"""

    setup_instructions: list[str] | None = None
    network_info: WarehouseNetworkInfo | None = None
    connection_permissions: WarehousePermissionInfo | None = None
    schema_permissions: WarehousePermissionInfo | None = None


class JsonConfig(pydantic.BaseModel):
    type: str
    config: dict[str, Any]

    @classmethod
    def from_url(cls, url: str) -> "JsonConfig":
        if not url.startswith("jsonconfig:"):
            raise ValueError("Invalid URL")
        json_base64 = url.split(":")[1]
        json_data = json.loads(base64.b64decode(json_base64).decode())
        return cls(type=json_data["type"], config=json_data["config"])

    def to_url(self) -> str:
        json_base64 = base64.b64encode(json.dumps(self.model_dump()).encode()).decode()
        return f"jsonconfig:{json_base64}"


Dialect = Literal[
    "snowflake",
    "bigquery",
    "duckdb",
    "aws_athena_trino_sql",
    "aws_athena_spark_sql",
    "redshift",
    "postgres",
]


class SnowflakePasswordCredential(pydantic.BaseModel):
    type: Literal["password"]
    password: str = pydantic.Field(
        title="Password",
        description="Database password",
        examples=["Your password"],
        json_schema_extra={"widget": "password"},
    )


class SnowflakePrivateKeyCredential(pydantic.BaseModel):
    type: Literal["private_key"]
    private_key_file: str = pydantic.Field(
        title="Private Key",
        description="Paste your private key in PEM format",
        examples=["-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"],
        json_schema_extra={"widget": "textarea"},
    )
    key_password: str | None = pydantic.Field(
        default=None,
        title="Private Key Password",
        description="Password for encrypted private key (leave empty for unencrypted keys)",
        examples=["Your key password"],
        json_schema_extra={"widget": "password"},
    )


class SnowflakeWarehouseConfig(pydantic.BaseModel):
    account_id: str = pydantic.Field(
        title="Account Locator",
        description="Your Snowflake account locator",
        examples=["abc12345"],
    )
    username: str = pydantic.Field(
        title="Username", description="Database username", examples=["admin"]
    )
    credential: SnowflakePasswordCredential | SnowflakePrivateKeyCredential
    warehouse: str = pydantic.Field(
        title="Warehouse",
        description="The compute warehouse to use for queries",
        examples=["COMPUTE_WH"],
    )
    role: str = pydantic.Field(
        title="Role",
        description="A role with access to the tables you want to analyze",
        examples=["ANALYST"],
    )
    region: str | None = pydantic.Field(
        default="",
        title="Region",
        description="AWS region where your Snowflake account is located (optional)",
        examples=["us-east-1"],
    )

    def to_url(self) -> str:
        return JsonConfig(
            type="snowflake",
            config=self.model_dump(mode="json"),
        ).to_url()

    def run_sql_query(self, query: str) -> list[dict[str, Any]]:
        # figure out rbac with datadog
        # try_set_tag("query", query)

        account_locator = self.account_id
        if self.region:
            account_locator += f".{self.region}"

        password = None
        private_key = None
        if self.credential.type == "password":
            password = self.credential.password
        elif self.credential.type == "private_key":
            # Parse the PEM formatted private key to base64 encoded DER format
            try:
                # Prepare password for key loading
                key_password = None
                if self.credential.key_password and self.credential.key_password.strip():
                    key_password = self.credential.key_password.encode("utf-8")

                # Load the private key from PEM format
                private_key_obj = serialization.load_pem_private_key(
                    self.credential.private_key_file.encode("utf-8"),
                    password=key_password,
                )
                # Convert to DER format
                der_private_key = private_key_obj.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
                # Encode as base64 string
                private_key = base64.b64encode(der_private_key).decode("utf-8")
            except Exception as e:
                raise ValueError(f"Failed to parse private key: {e!s}") from e

        connect_args = {
            "account": account_locator,
            "user": self.username,
            "password": password,
            "private_key": private_key,
            "warehouse": self.warehouse,
            "role": self.role,
        }

        return run_snowflake_query(connect_args, query)

    def list_schemas(self) -> list[str]:
        """List all accessible database.schema combinations in Snowflake"""
        try:
            schemas = []
            print("RUNNING")
            all_databases = [row["name"] for row in self.run_sql_query("SHOW DATABASES")]
            print(all_databases)
            return []
            for database in all_databases:
                database_schemas = [
                    row["name"] for row in self.run_sql_query(f"SHOW SCHEMAS IN {database}")
                ]
                for schema in database_schemas:
                    schemas.append(f"{database}.{schema}")
            return schemas
        except Exception as e:
            raise
            raise UserFacingDataError(f"Failed to list schemas in Snowflake: {e!s}")

    def list_tables(self, selected_schemas: list[str] | None) -> ListTablesResult:
        """List all accessible tables in Snowflake warehouse with per-schema error handling"""
        schema_results = []

        try:
            if selected_schemas is not None:
                # Use only selected schemas
                for schema_path in selected_schemas:
                    try:
                        database, schema = schema_path.split(".", 1)
                        rows = self.run_sql_query(f"SHOW TABLES IN {database}.{schema}")
                        print("ROWS:")
                        print(rows)
                        tables = []
                        for row in rows:
                            table_name = row["name"]
                            table_comment = row["comment"]
                            tables.append(
                                TableInfo(
                                    name=f"{database}.{schema}.{table_name}",
                                    description=table_comment,
                                )
                            )
                        schema_results.append(
                            SchemaTablesResult(
                                schema_name=schema_path, success=True, tables=tables, error=None
                            )
                        )
                    except Exception as e:
                        raise
                        # Record failure for this schema
                        schema_results.append(
                            SchemaTablesResult(
                                schema_name=schema_path, success=False, tables=[], error=str(e)
                            )
                        )
            else:
                # Original behavior - get all tables
                all_databases = [row["name"] for row in self.run_sql_query("SHOW DATABASES")]
                for database in all_databases:
                    schemas = [
                        row["name"] for row in self.run_sql_query(f"SHOW SCHEMAS IN {database}")
                    ]
                    for schema in schemas:
                        schema_path = f"{database}.{schema}"
                        try:
                            rows = self.run_sql_query(f"SHOW TABLES IN {database}.{schema}")
                            tables = []
                            for row in rows:
                                table_name = row["name"]
                                table_comment = row["comment"]
                                tables.append(
                                    TableInfo(
                                        name=f"{database}.{schema}.{table_name}",
                                        description=table_comment,
                                    )
                                )
                            schema_results.append(
                                SchemaTablesResult(
                                    schema_name=schema_path, success=True, tables=tables, error=None
                                )
                            )
                        except Exception as e:
                            schema_results.append(
                                SchemaTablesResult(
                                    schema_name=schema_path, success=False, tables=[], error=str(e)
                                )
                            )

        except Exception as e:
            raise
            # If we can't query Snowflake at all, return failure
            return ListTablesResult(
                success=False, schema_results=[], error=f"Failed to list Snowflake tables: {e!s}"
            )

        # Determine overall success
        has_any_success = any(r.success for r in schema_results)
        return ListTablesResult(success=has_any_success, schema_results=schema_results, error=None)

    def get_connection_name(self) -> str:
        """Generate connection name for Snowflake"""
        # Clean username for use in connection name
        clean_username = self.username.replace("@", "_").replace(".", "_")
        return clean_string_for_connection_name(f"snowflake_{clean_username}")

    @classmethod
    def get_help_info(cls) -> WarehouseHelpInfo:
        """Get help information for Snowflake setup"""
        return WarehouseHelpInfo(
            setup_instructions=[
                "Contact your Snowflake administrator to create an account",
                "Get your account locator from the Snowflake console URL",
                "Set up password or private key authentication",
                "Request the required Snowflake Privileges (see below)",
            ],
            network_info=WarehouseNetworkInfo(
                connection_method="HTTPS over port 443",
                ip_addresses=["100.20.92.101", "44.225.181.72", "44.227.217.144"],
                additional_info="Connects to <account>.snowflakecomputing.com - may require firewall allowlisting",
            ),
            connection_permissions=WarehousePermissionInfo(
                header="Required Snowflake Privileges",
                permissions=[
                    "USAGE on warehouse",
                    "USAGE on schema - Access schema objects",
                    "SELECT on tables - Query table data for analysis",
                    "SHOW privilege - View table metadata and structure",
                ],
            ),
            schema_permissions=WarehousePermissionInfo(
                header="Schema Discovery Privileges",
                permissions=[
                    "USAGE on schema - Access schema objects",
                    "SELECT on tables - Query table data for analysis",
                    "SHOW privilege - View table metadata and structure",
                ],
            ),
        )


def clean_string_for_connection_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s)


import os

import dagster as dg
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.remote_representation.external_data import AssetNodeSnap
from dagster._serdes import serialize_value
from dagster.observe_prototype.asset_source import (
    RemoteConnectionAssetNode,
    SnowflakeConnectionAssets,
)

if __name__ == "__main__":
    config = SnowflakeWarehouseConfig(
        account_id="na94824.us-east-1",
        username="slinguser",
        credential=SnowflakePasswordCredential(
            type="password", password=os.environ["SNOWFLAKE_PASSWORD"]
        ),
        warehouse="purina",
        role="sling_writer",
    )

    schemas = ["PURINA.CORE"]

    tables_result = config.list_tables(schemas)
    assert tables_result.success
    specs = []
    for schema_result in tables_result.schema_results:
        for table in schema_result.tables:
            specs.append(
                RemoteConnectionAssetNode(
                    asset_node_snap=AssetNodeSnap(
                        asset_key=dg.AssetKey(table.name),
                        parent_edges=[],
                        child_edges=[],
                        execution_type=AssetExecutionType.UNEXECUTABLE,
                        description=table.description,
                        is_observable=True,
                    ),
                    parent_keys=set(),
                    child_keys=set(),
                    check_keys=set(),
                    execution_set_entity_keys=set(),
                )
            )

    with open("snowflake_connection_assets.json", "w") as f:
        f.write(serialize_value(SnowflakeConnectionAssets(asset_nodes=specs)))
