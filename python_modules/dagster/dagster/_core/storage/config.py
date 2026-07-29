from typing_extensions import TypedDict

from dagster._config import Field, IntSource, Permissive, Selector, Shape, StringSource
from dagster._config.config_schema import UserConfigSchema


class MySqlStorageConfig(TypedDict):
    mysql_url: str
    mysql_db: "MySqlStorageConfigDb"


class MySqlStorageConfigDb(TypedDict):
    username: str
    password: str
    hostname: str
    db_name: str
    port: int


def mysql_config() -> UserConfigSchema:
    return Selector(
        {
            "mysql_url": StringSource,
            "mysql_db": {
                "username": StringSource,
                "password": StringSource,
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=3306),
            },
        }
    )


class MsSqlStorageConfig(TypedDict, total=False):
    mssql_url: str
    mssql_db: "MsSqlStorageConfigDb"


class MsSqlStorageConfigDb(TypedDict, total=False):
    username: str
    password: str
    hostname: str
    db_name: str
    port: int
    driver: str
    params: dict[str, object]
    scheme: str


def mssql_config() -> UserConfigSchema:
    return Selector(
        {
            "mssql_url": StringSource,
            "mssql_db": {
                "username": StringSource,
                "password": StringSource,
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=1433),
                # pyodbc dispatches on a named, locally installed ODBC driver rather than
                # speaking the wire protocol itself, so the driver name is part of the
                # connection identity and varies by host.
                "driver": Field(
                    StringSource,
                    is_required=False,
                    default_value="ODBC Driver 18 for SQL Server",
                ),
                # Passed through as query args, e.g. Encrypt, TrustServerCertificate,
                # Authentication (for Entra ID against Azure SQL), MultiSubnetFailover.
                "params": Field(Permissive(), is_required=False, default_value={}),
                "scheme": Field(StringSource, is_required=False, default_value="mssql+pyodbc"),
            },
        }
    )


class PostgresStorageConfig(TypedDict, total=False):
    postgres_url: str
    postgres_db: "PostgresStorageConfigDb"
    auth_provider: dict[str, object]


class PostgresStorageConfigDb(TypedDict, total=False):
    username: str
    password: str
    hostname: str
    db_name: str
    port: int
    params: dict[str, object]
    scheme: str


def pg_config() -> UserConfigSchema:
    return {
        "postgres_url": Field(StringSource, is_required=False),
        "postgres_db": Field(
            {
                "username": StringSource,
                "password": Field(StringSource, is_required=False, default_value=""),
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=5432),
                "params": Field(Permissive(), is_required=False, default_value={}),
                "scheme": Field(StringSource, is_required=False, default_value="postgresql"),
            },
            is_required=False,
        ),
        "auth_provider": Field(
            Selector(
                {
                    "azure_wif": Shape(
                        {
                            "scope": Field(
                                StringSource,
                                is_required=False,
                                default_value="https://ossrdbms-aad.database.windows.net/.default",
                            ),
                        }
                    ),
                    "gcp_wif": Shape({}),
                    "aws_wif": Shape(
                        {
                            "region": StringSource,
                        }
                    ),
                }
            ),
            is_required=False,
        ),
        "should_autocreate_tables": Field(bool, is_required=False, default_value=True),
    }
