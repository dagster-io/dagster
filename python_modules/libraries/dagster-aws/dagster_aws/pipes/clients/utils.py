from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal, TypedDict, TypeVar, Union, cast, overload

from dagster._core.pipes.utils import PipesSession
from typing_extensions import NotRequired

if TYPE_CHECKING:
    from mypy_boto3_emr.type_defs import ConfigurationTypeDef as EMRConfigurationUnionTypeDef
    from mypy_boto3_emr_containers.type_defs import (
        ConfigurationTypeDef as EMRContainersConfigurationUnionTypeDef,
    )


C = TypeVar(  # TypeVar for EMR/EMR Containers configurations
    # AWS EMR uses uppercase keys (Configurations, Properties, Classification)
    # while EMR Containers uses lowercase keys. This handles both cases.
    "C",
    bound=Union["EMRConfigurationUnionTypeDef", "EMRContainersConfigurationUnionTypeDef"],
)


@overload
def add_emr_configuration(
    configurations: Sequence["EMRConfigurationUnionTypeDef"],
    configuration: "EMRConfigurationUnionTypeDef",
    emr_flavor: Literal["standard"],
): ...


@overload
def add_emr_configuration(
    configurations: Sequence["EMRContainersConfigurationUnionTypeDef"],
    configuration: "EMRContainersConfigurationUnionTypeDef",
    emr_flavor: Literal["containers"],
): ...


def add_emr_configuration(
    configurations: Sequence[C],
    configuration: C,
    emr_flavor: Literal["standard", "containers"],
) -> list[C]:
    """Add a configuration to a list of EMR configurations, merging configurations with the same classification.

    This is necessary because EMR doesn't accept multiple configurations with the same classification.

    EMR uses uppercase keys, while EMR Containers uses lowercase keys. Some typing shenanigans are necessary to make
    this single function compatible with both EMR and EMR Containers.
    """
    configurations = list(configurations)

    if emr_flavor == "standard":
        classification_key = "Classification"
        properties_key = "Properties"
        configurations_key = "Configurations"
    elif emr_flavor == "containers":
        classification_key = "classification"
        properties_key = "properties"
        configurations_key = "configurations"
    else:
        raise ValueError(f"Invalid emr_flavor: {emr_flavor}")

    for existing_configuration in configurations:
        if (
            isinstance(existing_configuration, dict)
            and isinstance(configuration, dict)
            and existing_configuration.get(classification_key) is not None
            and existing_configuration.get(classification_key)
            == configuration.get(classification_key)
        ):
            properties = {**existing_configuration.get(properties_key, {})}
            properties.update(properties)

            inner_configurations = cast(
                "list[C]", existing_configuration.get(classification_key, [])
            )

            for inner_configuration in cast("list[C]", configuration.get(configurations_key, [])):
                add_emr_configuration(  # ty: ignore[no-matching-overload]
                    inner_configurations,
                    inner_configuration,
                    emr_flavor=emr_flavor,
                )

            existing_configuration[properties_key] = properties  # ty: ignore[invalid-assignment]
            existing_configuration[classification_key] = inner_configurations  # ty: ignore[invalid-assignment]

            break
    else:
        configurations.append(configuration)

    return configurations


def emr_inject_pipes_env_vars(
    session: PipesSession,
    configurations: Sequence[C],
    emr_flavor: Literal["standard", "containers"],
) -> list[C]:
    """EMR uses uppercase keys, while EMR Containers uses lowercase keys."""
    if emr_flavor == "standard":
        classification_key = "Classification"
        properties_key = "Properties"
        configurations_key = "Configurations"
        # add  env vars to all posttible configurations: spark-defaults, spark-env, yarn-env, hadoop-env
        # since we can't be sure which one will be used by the job
        classifications = ["spark-defaults", "spark-env", "yarn-env", "hadoop-env"]
    elif emr_flavor == "containers":
        classification_key = "classification"
        properties_key = "properties"
        configurations_key = "configurations"
        # for EMR Containets we only need to add the env vars to spark-env
        classifications = ["spark-env"]
    else:
        raise ValueError(f"Invalid emr_flavor: {emr_flavor}")

    pipes_env_vars = session.get_bootstrap_env_vars()

    configurations = add_emr_configuration(  # ty: ignore[no-matching-overload]
        configurations,
        {
            classification_key: "spark-defaults",
            properties_key: {
                f"spark.yarn.appMasterEnv.{var}": value for var, value in pipes_env_vars.items()
            },
        },
        emr_flavor=emr_flavor,
    )

    for classification in classifications:
        configurations = add_emr_configuration(  # ty: ignore[no-matching-overload]
            configurations,
            {
                classification_key: classification,
                configurations_key: [
                    {
                        classification_key: "export",
                        properties_key: pipes_env_vars,
                    }
                ],
            },
            emr_flavor=emr_flavor,
        )

    return configurations


class WaiterConfig(TypedDict):
    """A WaiterConfig representing the configuration of the waiter.

    Args:
        Delay (NotRequired[int]): The amount of time in seconds to wait between attempts. Defaults to 6.
        MaxAttempts (NotRequired[int]): The maximum number of attempts to be made. Defaults to 1000000
            By default the waiter is configured to wait up to 70 days (waiter_delay*waiter_max_attempts).
            See `Boto3 API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/waiter/TasksStopped.html>`_
    """

    Delay: NotRequired[int]
    MaxAttempts: NotRequired[int]
