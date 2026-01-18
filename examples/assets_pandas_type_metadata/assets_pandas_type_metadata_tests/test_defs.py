from dagster._core.definitions.definitions_class import Definitions

from assets_pandas_type_metadata.definitions import defs


def test_defs_can_load() -> None:
    assert isinstance(defs, Definitions)
    assert defs.resolve_all_job_defs()
