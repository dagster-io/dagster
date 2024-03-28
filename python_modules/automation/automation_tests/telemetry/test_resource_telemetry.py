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
from dagster._core.storage.input_manager import InputManagerDefinition
from dagster_duckdb import DuckDBIOManager
from dagster_gcp import BigQueryIOManager
from dagster_snowflake.snowflake_io_manager import SnowflakeIOManager


def test_resource_telemetry():
    # assert that all Resources and I/O Managers have dagster_maintained=True (or are known exceptions)

    libraries_dir = file_relative_path(__file__, "../../../libraries")

    libraries = [
        library.name.replace("-", "_")
        for library in os.scandir(libraries_dir)
        if not (library.name.startswith(".") or library.name.endswith("CONTRIBUTING.md"))
    ]
    libraries.append("dagster")

    # dagster-ge is out of date and is not installed in the dev environment
    libraries.remove("dagster_ge")
    # airflow isn't correctly installed in the BuildKite environment
    libraries.remove("dagster_airflow")
    # new library, not added yet
    libraries.remove("dagster_embedded_elt")

    resources_without_telemetry = []

    exceptions = [
        # the actual class definitions are set to False
        ResourceDefinition,
        IOManagerDefinition,
        InputManagerDefinition,
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
        for klass in resources.values():
            if klass in exceptions:
                # the klass is purposely set to dagster_maintained=False
                continue
            try:
                if not klass._is_dagster_maintained:  # noqa: SLF001
                    resources_without_telemetry.append(klass)
            except Exception:
                resources_without_telemetry.append(klass)

    error_message = (
        "The following resources and/or I/O managers are missing telemetry:"
        f" {resources_without_telemetry}"
    )

    check.invariant(len(resources_without_telemetry) == 0, error_message)
