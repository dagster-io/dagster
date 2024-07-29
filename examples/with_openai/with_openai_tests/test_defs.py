from with_openai.definitions import defs


def test_defs():
    assert defs.get_job_def("question_job")
    assert defs.get_job_def("search_index_job")
    assert defs.get_sensor_def("question_sensor")
    assert defs.get_assets_def("source_docs")
    assert defs.get_assets_def("search_index")
    assert defs.get_assets_def("completion")
