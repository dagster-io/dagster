from typing import TYPE_CHECKING, TypedDict, cast

from dagster._core.pipes.utils import PipesSession
from typing_extensions import NotRequired

if TYPE_CHECKING:
    from mypy_boto3_emr.type_defs import ConfigurationUnionTypeDef


def add_emr_configuration(
    configurations: list["ConfigurationUnionTypeDef"],
    configuration: "ConfigurationUnionTypeDef",
):
    """Add a configuration to a list of EMR configurations, merging configurations with the same classification.

    This is necessary because EMR doesn't accept multiple configurations with the same classification.
    """
    for existing_configuration in configurations:
        if existing_configuration.get("Classification") is not None and existing_configuration.get(
            "Classification"
        ) == configuration.get("Classification"):
            properties = {**existing_configuration.get("Properties", {})}
            properties.update(properties)

            inner_configurations = cast(
                list["ConfigurationUnionTypeDef"], existing_configuration.get("Configurations", [])
            )

            for inner_configuration in cast(
                list["ConfigurationUnionTypeDef"], configuration.get("Configurations", [])
            ):
                add_emr_configuration(inner_configurations, inner_configuration)

            existing_configuration["Properties"] = properties
            existing_configuration["Configurations"] = inner_configurations  # type: ignore

            break
    else:
        configurations.append(configuration)


def emr_inject_pipes_env_vars(
    session: PipesSession, configurations: list["ConfigurationUnionTypeDef"]
) -> list["ConfigurationUnionTypeDef"]:
    pipes_env_vars = session.get_bootstrap_env_vars()

    # add all possible env vars to spark-defaults, spark-env, yarn-env, hadoop-env
    # since we can't be sure which one will be used by the job
    add_emr_configuration(
        configurations,
        {
            "Classification": "spark-defaults",
            "Properties": {
                f"spark.yarn.appMasterEnv.{var}": value for var, value in pipes_env_vars.items()
            },
        },
    )

    for classification in ["spark-env", "yarn-env", "hadoop-env"]:
        add_emr_configuration(
            configurations,
            {
                "Classification": classification,
                "Configurations": [
                    {
                        "Classification": "export",
                        "Properties": pipes_env_vars,
                    }
                ],
            },
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
