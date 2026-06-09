def test_legacy_registry_import_still_works():
    from dagster._core.libraries import DagsterLibraryRegistry  # noqa

def test_dagster_library_registry_import_from_dagster():
    from dagster import DagsterLibraryRegistry # noqa
