from dagster import AssetKey

from with_openai import defs


def test_defs():
    assert defs.get_job_def("question_job")
    assert defs.get_job_def("search_index_job")
    assert defs.get_sensor_def("question_sensor")
    assert defs.get_asset_graph().has(AssetKey("source_docs"))
    assert defs.get_asset_graph().has(AssetKey("search_index"))
    assert defs.get_asset_graph().has(AssetKey("completion"))
