import os


def get_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise Exception(f"{var_name} is not set")
    return value
