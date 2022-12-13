from assets_pandas_type_metadata import defs


def test_defs_can_load():
    defs.get_repository_def().load_all_definitions()
