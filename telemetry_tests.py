import os

import dagster._check as check
from dagster import (
    ConfigurableResource,
    IOManagerDefinition,
    ResourceDefinition,
    file_relative_path,
)
from dagster._config.pythonic_config import (
    ConfigurableIOManager,
    ConfigurableIOManagerFactory,
    ConfigurableLegacyIOManagerAdapter,
    ConfigurableResourceFactory,
)
from dagster._core.storage.root_input_manager import RootInputManagerDefinition
from dagster_duckdb import DuckDBIOManager
from dagster_gcp import BigQueryIOManager
from dagster_snowflake.snowflake_io_manager import SnowflakeIOManager


def test_telemetry():
    libraries_dir = file_relative_path(__file__, "python_modules/libraries")

    libraries = [library.name.replace("-", "_") for library in os.scandir(libraries_dir)]
    libraries.append("dagster")

    # TODO - might need to add dagster-census to the dev install script - figure out why it's not there already

    # TODO - add back in one airflow dependency gets figured out
    libraries.remove("dagster_airflow")
    # dagster-ge is out of date and is not installed in the dev environment
    libraries.remove("dagster_ge")

    resources_without_telemetry = []

    exceptions = [
        # the actual class definitions are set to False
        ResourceDefinition,
        IOManagerDefinition,
        RootInputManagerDefinition,
        ConfigurableResource,
        ConfigurableIOManager,
        ConfigurableLegacyIOManagerAdapter,
        ConfigurableIOManagerFactory,
        # the base DB IO managers are set to False since users can instantiate their own versions
        SnowflakeIOManager,
        DuckDBIOManager,
        BigQueryIOManager,
    ]

    for library in libraries:
        print(f"Analyzing {library}")
        package = __import__(library)

        resources = dict(
            [
                (name, cls)
                for name, cls in package.__dict__.items()
                if isinstance(
                    cls,
                    (
                        ResourceDefinition,
                        ConfigurableResource,
                        IOManagerDefinition,
                        ConfigurableResourceFactory,
                    ),
                )
                or (
                    isinstance(cls, type)
                    and issubclass(
                        cls,
                        (
                            ResourceDefinition,
                            ConfigurableResource,
                            IOManagerDefinition,
                            ConfigurableResourceFactory,
                        ),
                    )
                )
            ]
        )
        for _, klass in resources.items():
            if klass in exceptions:
                # the klass is purposely set to dagster_maintained=False
                continue
            try:
                if not klass._dagster_maintained:
                    resources_without_telemetry.append(klass)
            except Exception:
                resources_without_telemetry.append(klass)

    error_message = (
        "The following resources and/or I/O managers are missing telemetry:"
        f" {resources_without_telemetry}"
    )

    check.invariant(len(resources_without_telemetry) == 0, error_message)
