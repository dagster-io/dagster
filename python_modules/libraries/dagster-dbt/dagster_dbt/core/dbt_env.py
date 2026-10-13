import os


def _get_dbt_env_var(key: str, default: str | None = None) -> str | None:
    """Return a dbt global config environment variable with dbt's precedence.

    The helper accepts the legacy `DBT_*` environment variable name and checks the corresponding
    `DBT_ENGINE_*` name first before falling back to `DBT_*`. This mirrors dbt's behavior for global
    config environment variables while preserving the call shape of `os.getenv`.

    `DBT_CLOUD_*` variables are not global config variables, so they are read without applying
    the engine prefix.
    """
    if not key.startswith("DBT_") or key.startswith("DBT_CLOUD_"):
        return os.getenv(key, default)

    engine_value = os.getenv(f"DBT_ENGINE_{key.removeprefix('DBT_')}")
    return engine_value if engine_value is not None else os.getenv(key, default)
