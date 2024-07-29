def get_weather_defs():
    # gather_assets_start

    # definitions.py
    from dagster import Definitions, load_assets_from_modules

    from .assets import table_assets
    from .local_filesystem_io_manager import LocalFileSystemIOManager

    defs = Definitions(
        # imports the module called "assets" from the package containing the current module
        # the "assets" module contains the asset definitions
        assets=load_assets_from_modules([table_assets]),
        resources={
            "io_manager": LocalFileSystemIOManager(),
        },
    )
    # gather_assets_end

    return defs


def get_spark_weather_defs():
    # gather_spark_assets_start

    # definitions.py

    from dagster import Definitions, load_assets_from_modules

    from .assets import spark_asset, table_assets
    from .local_spark_filesystem_io_manager import LocalFileSystemIOManager

    defs = Definitions(
        assets=load_assets_from_modules([table_assets, spark_asset]),
        resources={"io_manager": LocalFileSystemIOManager()},
    )
    # gather_spark_assets_end

    return defs


defs = get_spark_weather_defs()
