import pickle

from dagster_dbt.types import DbtOutput

DBT_RESULT_DICT = {
    "logs": [],
    "results": [
        {
            "unique_id": "model.fake_model",
            "error": None,
            "status": "CREATE VIEW",
            "execution_time": 1.1,
            "thread_id": "Thread-1",
            "timing": [
                {
                    "name": "compile",
                    "started_at": "2020-09-28T17:00:18.426563Z",
                    "completed_at": "2020-09-28T17:00:18.447900Z",
                },
                {
                    "name": "execute",
                    "started_at": "2020-09-28T17:00:18.448162Z",
                    "completed_at": "2020-09-28T17:00:18.521685Z",
                },
            ],
        },
        {
            "unique_id": "model.fake_model_2",
            "error": "This is a test error message on a dbt node.",
            "status": "ERROR",
            "execution_time": 1.1,
            "thread_id": "Thread-2",
            "timing": [],
        },
    ],
    "generated_at": "2020-09-28T17:00:18.746001Z",
    "elapsed_time": 1.1,
}


def test_pickle_roundtrip():
    rr = DbtOutput(result=DBT_RESULT_DICT)
    rr_new = pickle.loads(pickle.dumps(rr))

    assert vars(rr) == vars(rr_new)
