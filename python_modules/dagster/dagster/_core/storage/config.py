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
