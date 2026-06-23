from dagster import Array, Field, Permissive, StringSource

SHARED_DOCKER_CONFIG = {
    "networks": Field(
        Array(StringSource),
        is_required=False,
        description=(
            "Names of the networks to which to connect the launched container at creation time"
        ),
    ),
    "env_vars": Field(
        [str],
        is_required=False,
        description=(
            "The list of environment variables names to include in the docker container. "
            "Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled "
            "from the local environment)"
        ),
    ),
    "container_kwargs": Field(
        Permissive(),
        is_required=False,
        description=(
            "key-value pairs that can be passed into containers.create. See "
            "https://docker-py.readthedocs.io/en/stable/containers.html for the full list "
            "of available options."
        ),
    ),
}
