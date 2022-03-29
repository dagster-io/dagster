from dagster import assets_from_package_name, namespaced

core_assets = namespaced("core", assets_from_package_name(__name__))
