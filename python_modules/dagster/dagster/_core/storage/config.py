from dagster._config import Field, IntSource, Permissive, Selector, StringSource


def mysql_config():
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


def pg_config():
    return {
        "postgres_url": Field(StringSource, is_required=False),
        "postgres_db": Field(
            {
                "username": StringSource,
                "password": StringSource,
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=5432),
                "params": Field(Permissive(), is_required=False, default_value={}),
                "scheme": Field(StringSource, is_required=False, default_value="postgresql"),
            },
            is_required=False,
        ),
        "should_autocreate_tables": Field(bool, is_required=False, default_value=True),
    }
