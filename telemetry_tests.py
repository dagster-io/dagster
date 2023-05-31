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
            if (
                klass is ResourceDefinition
                or klass is IOManagerDefinition
                or klass is RootInputManagerDefinition
                or klass is ConfigurableResource
                or klass is ConfigurableIOManager
                or klass is ConfigurableLegacyIOManagerAdapter
                or klass is ConfigurableIOManagerFactory
            ):
                # klass is the actual definition object
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
