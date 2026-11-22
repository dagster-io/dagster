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
    pool: "PostgresStoragePoolConfig"


class PostgresStoragePoolConfig(TypedDict, total=False):
    pool_size: int
    max_overflow: int
    pool_recycle: int


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
        "pool": Field(
            {
                "pool_size": Field(
                    IntSource,
                    is_required=False,
                    default_value=5,
                    description="Maximum number of idle connections each storage keeps open.",
                ),
                "max_overflow": Field(
                    IntSource,
                    is_required=False,
                    default_value=10,
                    description=(
                        "Additional connections each storage may open beyond `pool_size` under"
                        " load. They are closed when returned to the pool."
                    ),
                ),
                "pool_recycle": Field(
                    IntSource,
                    is_required=False,
                    default_value=3600,
                    description=(
                        "Seconds after which a pooled connection is closed and replaced on next"
                        " use. -1 disables recycling."
                    ),
                ),
            },
            is_required=False,
            description=(
                "Reuse database connections instead of opening one per query. Recommended for"
                " the daemon under high load, where connection setup dominates query time."
                " Limits apply per storage (run, event log, schedule) in each process, so a"
                " process may hold up to 3 * (pool_size + max_overflow) connections. Pooled"
                " connections are checked with a ping before use. Without this block no"
                " connections are held open. The setting also applies to run workers and"
                " other processes that load this instance, which then hold idle connections"
                " for their lifetime. Ignored by dagster-webserver, which configures its pool"
                " with the --db-pool-* options."
            ),
        ),
    }
