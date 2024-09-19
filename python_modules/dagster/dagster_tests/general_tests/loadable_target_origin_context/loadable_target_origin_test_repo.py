from dagster import Definitions
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin

assert LoadableTargetOrigin.get() is not None, "LoadableTargetOrigin is not available from context"
origin = LoadableTargetOrigin.get()

assert (
    origin.python_file == __file__
    or origin.module_name
    == "dagster_tests.general_tests.loadable_target_origin_context.loadable_target_origin_test_repo"
    or origin.package_name
    == "dagster_tests.general_tests.loadable_target_origin_context.loadable_target_origin_test_repo"
)

defs = Definitions()
